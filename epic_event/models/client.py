"""Client ORM model with validation, error handling, and relationships."""
import logging
import re
from datetime import date, datetime
from typing import Optional, Union

from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, String
from sqlalchemy.orm import Session, relationship

from epic_event.models.base import Base
from epic_event.models.entity import Entity

logger = logging.getLogger(__name__)


class Client(Base, Entity):
    """
    ORM model representing a client with validation, error handling,
    and relationships to contracts and collaborators.

    Attributes:
        id (int): Primary key identifier.
        full_name (str): Full name of the client.
        email (str): Email address of the client.
        phone (Optional[str]): Optional phone number.
        company_name (Optional[str]): Optional name of the client company.
        created_date (Optional[date]): Date when the client was created.
        last_contact_date (Optional[date]): Date of the last contact with the client.
        id_commercial (Optional[int]): Foreign key to the commercial collaborator.
        archived (bool): Indicates if the client is archived.
    """

    __tablename__ = 'clients'

    id: int = Column(Integer, primary_key=True)
    full_name: str = Column(String, nullable=False)
    email: str = Column(String, nullable=False, unique=True)
    phone: Optional[str] = Column(String)
    company_name: Optional[str] = Column(String)
    created_date: Optional[date] = Column(Date)
    last_contact_date: Optional[date] = Column(Date)
    id_commercial: Optional[int] = Column(Integer,
                                          ForeignKey('collaborators.id'))
    archived: bool = Column(Boolean, default=False)

    contracts = relationship("Contract", back_populates="client")
    commercial = relationship("Collaborator", back_populates="clients")

    def __str__(self):
        return f"le client {self.company_name} répresenté par {self.full_name}"

    @property
    def formatted_created_date(self):
        """ Formatted date into european format"""
        return self.created_date.strftime("%d/%m/%Y")

    @property
    def formatted_last_contact_date(self):
        """ Formatted date into european format"""
        return self.last_contact_date.strftime("%d/%m/%Y")

    # session is used by the validate_all method of other models.
    # as the application calls it by entity.validate_all(session),
    # it is mandatory here too, even if it is not used
    def validate_all(self, session: Session) -> None:
        """
        Validates all the client's fields and sanitizes them where necessary.

        """
        self._validate_full_name(self.full_name)
        self._validate_email(self.email)
        self._validate_phone(self.phone)
        self._validate_company_name(self.company_name)
        self.last_contact_date = self._validate_date(self.last_contact_date)

    @staticmethod
    def _validate_full_name(name: str):
        """
        Validates that the full name is not empty, is alphabetical and unique.
        Args:
            name: the name to check.

        Raises:
            ValueError: If the name is not a valid string format.
        """
        if not name or not name.strip():
            logger.exception("Full name must not be empty.")
            raise ValueError("Full name must not be empty.")

        if not re.fullmatch(
                r"[A-Za-zÀ-ÖØ-öø-ÿ\- ]+", name):
            logger.exception("Full name must be alphabetical.")
            raise ValueError("Full name must be alphabetical.")


    @staticmethod
    def _validate_email(email: str):
        """
        Validate the type and the format of an email.

        Args:
            email (str): The email address to validate.

        Raises:
            ValueError: If the email is not a string or its format is invalid.

        """
        if not isinstance(email, str):
            error = "L'email doit être une chaîne de caractères."
            logger.exception(error)
            raise ValueError(error)

        if not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email):
            error = f"Format d'email invalide: {email}"
            logger.exception(error)
            raise ValueError(error)


    @staticmethod
    def _validate_phone(phone: str):
        """
        Validates a French phone number in national or international format.

        Args:
            phone (str): The phone number to validate.

        Raises:
            ValueError: If the phone number is not a string or if it does not
                        match the expected French phone number formats.
        """

        if not isinstance(phone, str):
            error = "Le numéro de téléphone doit être une chaîne de caractères."
            logger.exception(error)
            raise ValueError(error)

        phone = phone.replace(" ", "")
        national = r"^0[1-9](?:[ .-]?\d{2}){4}$"
        international = r"^\+33[1-9](?:[ .-]?\d{2}){4}$"

        if not (re.fullmatch(national, phone) or re.fullmatch(international, phone)):
            error = f"Numéro de téléphone invalide : {phone}"
            logger.exception(error)
            raise ValueError(error)

    @staticmethod
    def _validate_company_name(company: str) -> str:
        """Validates the company name string.
        Args:
            company (str): The company name to validate.

        Raises:
            ValueError: If the company name is not a string or if it's empty'.
        """
        if not isinstance(company, str) or not company.strip():
            error = "Le nom de l'entreprise est invalide ou vide."
            logger.exception(error)
            raise ValueError(error)

    @staticmethod
    def _validate_date(value: Union[date, str]) -> date:
        """
        Validates and converts a value into a `date` object.

        Args:
            value (Union[date, str]): The date to validate, either as a `date`
                            object or as a string in the format "DD-MM-YYYY".

        Returns:
            date: The validated `date` object.

        Raises:
            ValueError: If the input is neither a `date` nor a valid string in
                        the "DD-MM-YYYY" format.
        """

        if isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                return datetime.strptime(value.strip(), "%d-%m-%Y").date()
            except ValueError:
                error = f"Date invalide ou au mauvais format (attendu : JJ-MM-AAAA) : {value}"
                logger.exception(error)
                raise ValueError(error)
        error = "La date doit être une instance de `date` ou une chaîne."
        logger.exception(error)
        raise ValueError(error)
