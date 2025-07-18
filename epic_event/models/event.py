"""Event ORM model with validation, error handling, and relationships."""
import logging
from datetime import date, datetime

from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, String, Text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, relationship

from epic_event.models import Collaborator, Contract, Entity
from epic_event.models.base import Base

logger = logging.getLogger(__name__)


class Event(Base, Entity):
    """
    ORM model for managing scheduled events, linked to contracts and support collaborators.

    Attributes:
        id (int): Primary key.
        title (str): Title of the event.
        start_date (date): Start date of the event.
        end_date (date): End date of the event.
        location (str): Location string.
        participants (int): Number of participants.
        notes (str): Optional notes.
        archived (bool): Soft delete flag.
        contract_id (int): Foreign key to the contract.
        support_id (int): Foreign key to the support collaborator.
    """

    __tablename__ = 'events'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    location = Column(String)
    participants = Column(Integer, default=0)
    notes = Column(Text)
    archived = Column(Boolean, default=False)

    contract_id = Column(Integer, ForeignKey('contracts.id'), nullable=False)
    support_id = Column(Integer, ForeignKey('collaborators.id'))

    contract = relationship("Contract", back_populates="event")
    support = relationship("Collaborator", back_populates="events")

    @property
    def formatted_start_date(self):
        return self.start_date.strftime("%d/%m/%Y")

    @property
    def formatted_end_date(self):
        return self.end_date.strftime("%d/%m/%Y")

    @staticmethod
    def _validate_title(title: Column[str]) -> None:
        """
        Validate that the event has a non-empty title.
        Args:
           title (Column[str]): title of the event.

        Raises:
            ValueError: If title is missing or only whitespace.
        """
        if not title or not title.strip():
            error = "Title is required."
            logger.exception(error)
            raise ValueError(error)

    def _validate_dates(self) -> None:
        """
        Validate the start and end dates of the event.

        Raises:
            ValueError: If dates are missing, not of type `date`, or start > end.
        """
        for value in (self.start_date, self.end_date):
            if isinstance(value, date):
                continue
            elif isinstance(value, str):
                try:
                    value = datetime.strptime(value.strip(), "%d-%m-%Y").date()
                except ValueError:
                    error = f"Date invalide ou au mauvais format (attendu : JJ-MM-AAAA) : {value}"
                    logger.exception(error)
                    raise ValueError(error)
            else:
                error = "La date doit être une instance de `date` ou une chaîne."
                logger.exception(error)
                raise ValueError(error)

        if self.start_date > self.end_date:
            error = "Start date cannot be after end date."
            logger.exception(error)
            raise ValueError(error)


    @staticmethod
    def _validate_participants(number: Column[int]) -> None:
        """
        Ensure that the number of participants is a non-negative integer.

        Args:
            number (Column[int]): number of participants.
        Raises:
            ValueError: If participants is not a positive integer.
        """
        try:
            number = int(number)
        except (ValueError, TypeError) as e:
            logger.exception(e)
            raise

        if number < 0:
            logger.exception("Participants must be a positive integer.")
            raise ValueError("Participants must be a positive integer.")


    @staticmethod
    def _validate_contract_id(db: Session, contract_id: Column[int]) -> None:
        """
        Check that the contract exists and is signed.

        Args:
            db (Session): SQLAlchemy session.
            contract_id (int): contract id related to the event.

        Raises:
            ValueError: If contract is not found or not signed.
            SQLAlchemyError : If a database error occurs during the query.
        """
        try:
            contracts = Contract.filter_by_fields(db, id=contract_id)
        except SQLAlchemyError as e:
            raise

        if not contracts:
            error = f"Contract ID {contract_id} not found."
            logger.exception(error)
            raise ValueError(error)

        contract = contracts[0]

        if not contract.signed:
            error = "The contract must be signed before assigning to an event."
            logger.exception(error)
            raise ValueError(error)


    @staticmethod
    def _validate_support_id(db: Session, support_id: Column[int]) -> None:
        """
        Validate that the support collaborator exists and has the correct role.

        Args:
            db (Session): SQLAlchemy session.
            support_id: id of the collaborator from the support service

        Raises:
            ValueError: If the collaborator is not valid or not in the support role.
            SQLAlchemyError : If a database error occurs during the query.
        """
        if support_id is not None:
            try:
                with db.no_autoflush:
                    collaborator = db.query(Collaborator).filter_by(id=support_id).first()
            except SQLAlchemyError as e:
                logger.exception(e)
                raise
            if not collaborator:
                error = f"Collaborator ID {support_id} not found."
                logger.exception(error)
                raise ValueError(error)
            if collaborator.role != "support":
                error = "The selected collaborator is not in the 'support' role."
                logger.exception(error)
                raise ValueError(error)

    def validate_all(self, db: Session) -> None:
        """
        Run all field validations before saving the event.

        Args:
            db (Session): SQLAlchemy session.
        """
        self._validate_title(self.title)
        self._validate_dates()
        self._validate_participants(self.participants)
        self._validate_contract_id(db, self.contract_id)
        self._validate_support_id(db, self.support_id)
