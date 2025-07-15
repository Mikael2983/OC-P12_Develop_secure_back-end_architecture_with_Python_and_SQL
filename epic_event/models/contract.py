"""Contract ORM model with validation, error handling, and relationships."""
from sqlalchemy import Date, Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship, Session
import logging

from epic_event.models.base import Base
from epic_event.models import Client, Entity

logger = logging.getLogger(__name__)


class Contract(Base, Entity):
    """
    ORM model representing a service contract tied to a client and optionally an event.

    Attributes:
        id (int): Primary key.
        total_amount (str): Total contract amount (stored as string but validated as float).
        amount_due (str): Amount due (stored as string but validated as float).
        created_date (date): Date the contract was created.
        signed (bool): Whether the contract has been signed.
        archived (bool): Whether the contract is archived.
        client_id (int): Foreign key to the Client.
    """

    __tablename__ = 'contracts'

    id = Column(Integer, primary_key=True)
    total_amount = Column(String, nullable=False)
    amount_due = Column(String, nullable=False)
    created_date = Column(Date)
    signed = Column(Boolean, nullable=False, default=False)
    archived = Column(Boolean, default=False)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)

    client = relationship("Client", back_populates="contracts")
    event = relationship("Event", back_populates="contract", uselist=False)

    @staticmethod
    def normalize_signed(raw_value: Column[bool]) -> bool:
        """
        Convert string representation of a boolean to a Python boolean.

        Args:
            raw_value (str): A string like 'True' or 'False'.

        Returns:
            bool: The corresponding boolean value.
        """
        if not isinstance(raw_value, bool):
            return raw_value == 'True'
        return raw_value

    def validate_amounts(self) -> None:
        """
        Validate total and due amounts.

        Args:
            total_amount: Total amount, expected to be convertible to float.
            amount_due: Amount due, expected to be convertible to float.

        Raises:
            ValueError: If inputs are not valid numbers or business constraints fail.
        """
        try:
            total = float(self.total_amount)
            due = float(self.amount_due)
        except (TypeError, ValueError):
            logger.exception("Amounts must be valid numeric values.")
            raise ValueError("Amounts must be valid numeric values.")

        if total < 0 or due < 0:
            logger.exception("Amounts must be positive.")
            raise ValueError("Amounts must be positive.")
        if due > total:
            logger.exception("Amount due cannot exceed total amount.")
            raise ValueError("Amount due cannot exceed total amount.")

    @staticmethod
    def validate_client_existence(db: Session, client_id: Column[int]) -> None:
        """
        Validate that the client ID exists in the database.

        Args:
            db (Session): SQLAlchemy session.
            client_id: id of the client
        Raises:
            ValueError: If client_id is not set or client does not exist.
        """
        try:
            if not client_id:
                logger.exception("Missing client_id.")
                raise ValueError("Missing client_id.")
            with db.no_autoflush:
                client = db.query(Client).filter_by(id=client_id).first()
            if not client:
                logger.exception(f"No client found with id={client_id}.")
                raise ValueError(f"No client found with id={client_id}.")
        except Exception as e:
            logger.exception(e)
            raise

    def validate_all(self, db: Session) -> None:
        """
        Run all validations.

        Args:
            db (Session): SQLAlchemy session.

        Raises:
            ValueError: If any validation fails.
        """
        self.validate_amounts()
        self.validate_client_existence(db, self.client_id)
        self.signed = self.normalize_signed(self.signed)
