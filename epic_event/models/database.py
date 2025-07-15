import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from epic_event.models.base import Base

SESSION_CONTEXT = {}
logger = logging.getLogger(__name__)


class Database:

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
        """Create tables for all models declared with Base."""
        try:
            self.Base.metadata.create_all(self.engine)
        except Exception as e:
            logger.exception("Failed to initialize the database")
            raise RuntimeError("Database initialization failed") from e
