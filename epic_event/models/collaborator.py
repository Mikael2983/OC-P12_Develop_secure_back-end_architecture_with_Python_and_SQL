"""Collaborator ORM model with validation, error handling, and relationships."""
import re
import bcrypt

from sqlalchemy import Column, Integer, String, Boolean, LargeBinary
from sqlalchemy.orm import relationship, Session
import logging

from epic_event.models.base import Base
from epic_event.models import Entity

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

    def _validate_full_name(self, db: Session) -> None:
        """
        Validates that the full name is not empty and is unique.
        """
        try:
            if not self.full_name or not self.full_name.strip():
                logger.exception("Full name must not be empty.")
                raise ValueError("Full name must not be empty.")

            if not re.fullmatch(
                    r"[A-Za-zÀ-ÖØ-öø-ÿ\- ]+",
                    self.full_name):
                logger.exception("Full name must be alphabetical.")
                raise ValueError("Full name must be alphabetical.")
            with db.no_autoflush:
                existing = db.query(Collaborator).filter(
                    Collaborator.full_name == self.full_name,
                    Collaborator.id != getattr(self, "id", None)
                ).first()

                if existing:
                    logger.exception("This full name is already in use.")
                    raise ValueError("This full name is already in use.")
        except Exception as e:
            logger.exception(e)
            raise

    def _validate_email(self, db: Session, email) -> None:
        """
        Validates the format and uniqueness of the email address.
        args:
            email: mail adress
        """
        try:
            pattern = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
            if not re.match(pattern, email or ""):
                logger.exception("Invalid email address format.")
                raise ValueError("Invalid email address format.")

            with db.no_autoflush:
                existing_email = db.query(Collaborator).filter(
                    Collaborator.email == self.email,
                    Collaborator.id != getattr(self, "id", None)
                ).first()
            if existing_email:
                logger.exception("This email address is already in use.")
                raise ValueError("This email address is already in use.")

        except Exception as e:
            logger.exception(e)
            raise

    @staticmethod
    def _validate_role(role) -> None:
        """
        Validates that the assigned role is among the allowed services.
        args:
            role: the collaborator's role
        """
        try:
            if role not in SERVICES and role != "admin":
                logger.exception(f"Invalid role '{role}'. Must be one of: {SERVICES}.")
                raise ValueError(f"Invalid role '{role}'. Must be one of: {SERVICES}.")
        except Exception as e:
            logger.exception(e)
            raise

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
        """
        try:
            salt = bcrypt.gensalt()
            self.password = bcrypt.hashpw(raw_password.encode("utf-8"), salt)
        except Exception as e:
            logger.exception(e)
            raise

    def check_password(self, raw_password: str) -> bool:
        """
        Verifies the given raw password against the stored hash.

        Returns:
            bool: True if match, False otherwise.
        """
        try:
            return bcrypt.checkpw(raw_password.encode("utf-8"), self.password)
        except Exception as e:
            logger.exception(e)
            return False