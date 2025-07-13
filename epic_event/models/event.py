"""Event ORM model with validation, error handling, and relationships."""
from datetime import date

import logging
from sqlalchemy import Date, Column, Integer, String, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship, Session

from models.base import Base
from models import Contract
from models import Collaborator
from models import Entity

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

    @staticmethod
    def _validate_title(title: Column[str]) -> None:
        """
        Validate that the event has a non-empty title.
        Args:
           title (Column[str]): title of the event.

        Raises:
            ValueError: If title is missing or only whitespace.
        """
        try:
            if not title or not title.strip():
                logger.exception("Title is required.")
                raise ValueError("Title is required.")
        except Exception as e:
            logger.exception(e)
            raise

    def _validate_dates(self) -> None:
        """
        Validate the start and end dates of the event.

        Raises:
            ValueError: If dates are missing, not of type `date`, or start > end.
        """
        try:
            if not isinstance(self.start_date, date) or not isinstance(self.end_date, date):
                logger.exception("Start and end dates must be valid date instances.")
                raise ValueError("Start and end dates must be valid date instances.")
            if self.start_date > self.end_date:
                logger.exception("Start date cannot be after end date.")
                raise ValueError("Start date cannot be after end date.")
        except Exception as e:
            logger.exception(e)
            raise

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
            if number < 0:
                logger.exception("Participants must be a positive integer.")
                raise ValueError("Participants must be a positive integer.")
        except Exception as e:
            logger.exception(e)
            raise

    @staticmethod
    def _validate_contract_id(db: Session, contract_id: Column[int]) -> None:
        """
        Check that the contract exists and is signed.

        Args:
            db (Session): SQLAlchemy session.
            contract_id (int): contract id related to the event.
        Raises:
            ValueError: If contract is not found or not signed.
        """
        try:
            contracts = Contract.filter_by_fields(db, id=contract_id)

            if not contracts:
                logger.exception(f"Contract ID {contract_id} not found.")
                raise ValueError(f"Contract ID {contract_id} not found.")

            contract = contracts[0]

            if not contract.signed:
                logger.exception("The contract must be signed before assigning to an event.")
                raise ValueError("The contract must be signed before assigning to an event.")
        except Exception as e:
            logger.exception(e)
            raise

    @staticmethod
    def _validate_support_id(db: Session, support_id: Column[int]) -> None:
        """
        Validate that the support collaborator exists and has the correct role.

        Args:
            db (Session): SQLAlchemy session.
            support_id: id of the collaborator from the support service

        Raises:
            ValueError: If the collaborator is not valid or not in the support role.

        """
        try:
            if support_id is not None:
                with db.no_autoflush:
                    collaborator = db.query(Collaborator).filter_by(id=support_id).first()
                if not collaborator:
                    logger.exception(f"Collaborator ID {support_id} not found.")
                    raise ValueError(f"Collaborator ID {support_id} not found.")
                if collaborator.role != "support":
                    logger.exception("The selected collaborator is not in the 'support' role.")
                    raise ValueError("The selected collaborator is not in the 'support' role.")
        except Exception as e:
            logger.exception(e)
            raise

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
