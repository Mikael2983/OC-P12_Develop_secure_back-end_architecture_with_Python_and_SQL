"""
Database Connection Module for Epic Event.

This module provides a centralized `Database` class to manage the database
connection, session lifecycle, and schema creation using SQLAlchemy ORM.

Features:
    - Connects to a local SQLite database by default.
    - Lazily initializes a session when needed.
    - Handles the creation of all ORM model tables via declarative `Base`.
    - Logs errors using the standard Python `logging` module.

Globals:
    SESSION_CONTEXT (dict): In-memory session cache for authenticated users or views.

Classes:
    Database: Encapsulates SQLAlchemy engine, session factory, and schema creation logic.

Usage Example:
    db = Database()
    session = db.get_session()
    db.initialize_database()

Notes:
    - Default database file is `epic_event.db` in the working directory.
    - Errors during schema creation are logged and re-raised.
    - Intended for use in both development and production environments.
"""
import logging

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from epic_event.models.base import Base

SESSION_CONTEXT = {}
logger = logging.getLogger(__name__)


class Database:
    """
    Database handler using SQLAlchemy ORM for Epic Event.

    Manages the database connection, session creation, and schema initialization.

    Attributes:
        db_url (str): The database URL used by SQLAlchemy.
        engine (Engine): The SQLAlchemy engine instance.
        Base (DeclarativeMeta): The declarative base for ORM models.
        SessionLocal (sessionmaker): Factory for creating new Session objects.
        session (Session | None): The current active session, lazily initialized.

    Methods:
        get_session() -> Session:
            Lazily initializes and returns a SQLAlchemy session.

        initialize_database() -> None:
            Creates database tables for all declared ORM models.
            Raises SQLAlchemyError if table creation fails.
    """

    def __init__(self, db_name: str = "epic_event.db"):
        """Database handler using SQLAlchemy ORM.

            Args:
                db_name (str): SQLAlchemy-compatible database name.
            """
        self.db_url = f"sqlite:///{db_name}"
        self.engine = create_engine(self.db_url, echo=False)
        self.Base = Base
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.session = None

    def get_session(self) -> Session:
        """Lazily initialize and return a SQLAlchemy session."""
        if self.session is None:
            self.session = self.SessionLocal()
        return self.session

    def initialize_database(self) -> None:
        """Create tables for all models declared with Base.

            Raises :
                SQLAlchemyError : If a database error occurs during commit.
        """
        try:
            self.Base.metadata.create_all(self.engine)
        except SQLAlchemyError as e:
            logger.exception("Failed to initialize the database: %s", e)
            raise
