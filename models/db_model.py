from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


DB_PATH = "sqlite:///epic_events.db"

engine = create_engine(DB_PATH)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()


def initialize_database():
    Base.metadata.create_all(engine)



