"""Collaborator ORM model with validation, error handling, and relationships."""
import logging
import re

import bcrypt
from sqlalchemy import Boolean, Column, Integer, LargeBinary, String
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, relationship

from epic_event.models.base import Base
from epic_event.models.entity import Entity

SERVICES = ["gestion", "commercial", "support"]
logger = logging.getLogger(__name__)


class Collaborator(Base, Entity):
    """
    ORM model representing a Collaborator with validation, error handling,
    and secure password handling.

    Attributes:
        id (int): Primary key identifier.
        password (bytes): Bcrypt-hashed password.
        full_name (str): Unique full name of the collaborator.
        email (str): Unique email address.
        role (str): Role of the collaborator (e.g., support, commercial).
        archived (bool): Archive status.
    """

    __tablename__ = 'collaborators'

    id = Column(Integer, primary_key=True)
    password = Column(LargeBinary(60), nullable=False)
    full_name = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    role = Column(String, nullable=False)
    archived = Column(Boolean, default=False)

    events = relationship(
        "Event",
        back_populates="support",
        foreign_keys="Event.support_id"
    )

    clients = relationship("Client", back_populates="commercial")

    def __str__(self):
        return f"le collaborateur {self.full_name} du service {self.role}"

    def _validate_full_name(self, db: Session) -> None:
        """
        Validates that the full name is not empty, is alphabetical and unique.
        Args:
            db (Session): SQLAlchemy session instance.

        Raises:
            ValueError: If the fullname is neither unique nor a valid string
                        format.
        """
        if not self.full_name or not self.full_name.strip():
            raise ValueError("Full name must not be empty.")

        # Autorise les lettres, accents, tirets, apostrophes et espaces
        pattern = r"[A-Za-zÀ-ÖØ-öø-ÿ' \-]+"
        if not re.fullmatch(pattern, self.full_name):
            error = ("Full name must contain only letters, spaces, hyphens or "
                     "apostrophes.")
            logger.exception(error)
            raise ValueError(error)

        try:
            with db.no_autoflush:
                existing = db.query(Collaborator).filter(
                    Collaborator.full_name == self.full_name,
                    Collaborator.id != getattr(self, "id", None)
                ).first()

                if existing:
                    error = "This full name is already in use."
                    logger.exception(error)
                    raise ValueError(error)
        except SQLAlchemyError as e:
            error = f"Database error during full name validation: {e}."
            logger.exception(error)
            raise

    def _validate_email(self, db: Session, email: Column[str]) -> None:
        """
        Validate the type and the format of an email.

        Args:
            db (Session): SQLAlchemy session instance.
            email (str): The email address to validate.

        Raises:
            ValueError: If the email is not a string or its format is invalid
                or already in use.
            SQLAlchemyError : If a database error occurs during the query.
        """

        pattern = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
        if not re.match(pattern, email or ""):
            error = "Invalid email address format."
            logger.exception(error)
            raise ValueError(error)

        try:
            with db.no_autoflush:
                existing_email = db.query(Collaborator).filter(
                    Collaborator.email == self.email,
                    Collaborator.id != getattr(self, "id", None)
                ).first()
            if existing_email:
                error = "This email address is already in use."
                logger.exception(error)
                raise ValueError(error)

        except SQLAlchemyError as e:
            logger.exception(
                "Database error during email validation: %s.", e)
            raise

    @staticmethod
    def _validate_role(role) -> None:
        """
        Validates that the assigned role is among the allowed services.
        args:
            role: the collaborator's role

        raises: ValueError: if the role is not in the list of possible roles
        """

        if role not in SERVICES and role != "admin":
            error = f"Invalid role '{role}'. Must be one of: {SERVICES}."
            logger.exception(error)
            raise ValueError(error)

    def validate_all(self, db: Session) -> None:
        """
        Runs all available validators on the instance.
        """
        self._validate_full_name(db)
        self._validate_email(db, self.email)
        self._validate_role(self.role)

    def set_password(self, raw_password: str) -> None:
        """
        Hashes and stores the given password.

        Args:
            raw_password (str): The plain-text password.

        Raises:
            TypeError: If the password is not a string.
            ValueError: If the password is too long for bcrypt.
        """

        salt = bcrypt.gensalt()
        if not isinstance(raw_password, str):
            error = "Password must be a string."
            logger.exception(error)
            raise TypeError(error)
        if len(raw_password) > 72:
            error = "Password exceeds bcrypt maximum length of 72 characters."
            logger.exception(error)
            raise ValueError(error)

        self.password = bcrypt.hashpw(raw_password.encode("utf-8"), salt)

    def check_password(self, raw_password: str) -> bool:
        """
        Verifies the given raw password against the stored hash.

        Args:
            raw_password (str): The plain-text password to verify.

        Returns:
            bool: True if the password matches, False otherwise.

        Raises:
            TypeError: If the password is not a string.
            ValueError: If  not a valid bcrypt hash
        """

        if not isinstance(raw_password, str):
            raise TypeError("Password must be a string.")

        try:
            return bcrypt.checkpw(raw_password.encode("utf-8"),
                                  self.password)

        except (ValueError, TypeError) as e:
            logger.exception("Password verification failed: %s", e)
            return False
