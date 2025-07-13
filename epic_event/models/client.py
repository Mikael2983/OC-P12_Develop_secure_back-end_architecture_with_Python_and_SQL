"""Client ORM model with validation, error handling, and relationships."""
import logging
import re
from datetime import date, datetime
from typing import Optional, Union

from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, Session

from models.base import Base
from models import Entity

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

    def validate_all(self, session: Session) -> None:
        """
        Validates all the client's fields and sanitizes them where necessary.

        Raises:
            ValueError: If any validation fails.
        """
        self._validate_full_name(self.full_name)
        self._validate_email(self.email)
        self._validate_phone(self.phone)
        self._validate_company_name(self.company_name)
        self.last_contact_date = self._validate_date(self.last_contact_date)

    @staticmethod
    def _validate_full_name(name: str):
        """Strips and validates the client's full name."""
        try:
            if not name or not name.strip():
                logger.exception("Full name must not be empty.")
                raise ValueError("Full name must not be empty.")

            if not re.fullmatch(
                    r"[A-Za-zÀ-ÖØ-öø-ÿ\- ]+", name):
                logger.exception("Full name must be alphabetical.")
                raise ValueError("Full name must be alphabetical.")

        except Exception as e:
            logger.exception(e)
            raise


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
            logger.exception("L'email doit être une chaîne de caractères.")
            raise ValueError("L'email doit être une chaîne de caractères.")

        if not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email):
            logger.exception(f"Format d'email invalide: {email}")
            raise ValueError(f"Format d'email invalide: {email}")


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
            logger.exception("Le numéro de téléphone doit être une chaîne de caractères.")
            raise ValueError(
                "Le numéro de téléphone doit être une chaîne de caractères.")
        phone = phone.replace(" ", "")
        national = r"^0[1-9](?:[ .-]?\d{2}){4}$"
        international = r"^\+33[1-9](?:[ .-]?\d{2}){4}$"
        if not (re.fullmatch(national, phone) or re.fullmatch(international, phone)):
            logger.exception(f"Numéro de téléphone invalide : {phone}")
            raise ValueError(f"Numéro de téléphone invalide : {phone}")

    @staticmethod
    def _validate_company_name(company: str) -> str:
        """Validates the company name string.
        Args:
            company (str): The company name to validate.

        Raises:
            ValueError: If the company name is not a string or if it's empty'.
        """
        if not isinstance(company, str) or not company.strip():
            logger.exception("Le nom de l'entreprise est invalide ou vide.")
            raise ValueError("Le nom de l'entreprise est invalide ou vide.")

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
                logger.exception(
                    f"Date invalide ou au mauvais format (attendu : JJ-MM-AAAA) : {value}")
                raise ValueError(
                    f"Date invalide ou au mauvais format (attendu : JJ-MM-AAAA) : {value}")

        logger.exception(
            "La date doit être une instance de `date` ou une chaîne.")
        raise ValueError(
            "La date doit être une instance de `date` ou une chaîne.")
