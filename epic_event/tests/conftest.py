from http.server import HTTPServer
import os
from pathlib import Path
import pytest
import threading
import time

from selenium import webdriver
from sqlalchemy.exc import SQLAlchemyError

from epic_event.models import Database, Client, Collaborator, Contract, Event
from epic_event.models.base import Base
from epic_event.models.utils import load_test_data_in_database
from epic_event.router import MyHandler

DB_FILENAME = "test_database.db"


@pytest.fixture(scope="session")
def driver():
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()


@pytest.fixture(scope="session")
def db_path() -> str:
    path = Path(DB_FILENAME)

    if path.exists():
        try:
            os.remove(path)
        except (PermissionError, OSError) :
            raise RuntimeError(
                "Impossible de supprimer test_database.db : fichier verrouillé.")

    yield str(path)

    if path.exists():
        try:
            os.remove(path)
        except (PermissionError, OSError):
            raise RuntimeError(
                "Impossible de supprimer test_database.db : fichier verrouillé.")


@pytest.fixture(scope="session")
def db_session(db_path: str):
    """Database session using a shared SQLite file."""
    db = Database(db_path)
    db.initialize_database()
    session = db.get_session()
    load_test_data_in_database(session)
    MyHandler.session = session

    yield session

    try:
        session.rollback()
        session.close()
    except SQLAlchemyError:
        pass

    try:
        Base.metadata.drop_all(bind=db.engine)
        db.engine.dispose()
    except SQLAlchemyError:
        pass


@pytest.fixture(scope="session", autouse=True)
def start_test_server(db_session):
    server_address = ('localhost', 5000)
    httpd = HTTPServer(server_address, MyHandler)

    thread = threading.Thread(target=httpd.serve_forever)
    thread.Daemon = True
    thread.start()

    time.sleep(1)

    yield

    httpd.shutdown()
    thread.join()


@pytest.fixture(scope="session")
def seed_data_collaborator(db_session):
    gestion = db_session.query(Collaborator).filter_by(role="gestion").first()

    commercial = db_session.query(Collaborator).filter_by(
        role="commercial").first()

    support = db_session.query(Collaborator).filter_by(role="support").first()

    return {"gestion": gestion, "commercial": commercial, "support": support}


@pytest.fixture(scope="session")
def seed_data_client(db_session):
    """return client from the database."""

    client = db_session.query(Client).first()
    return client


@pytest.fixture(scope="session")
def seed_data_contract(db_session):
    signed_contract = db_session.query(Contract).filter(
        Contract.signed.is_(True),
        Contract.event == None
    ).first()

    not_signed_contract = db_session.query(Contract).filter(
        Contract.signed.is_(False),
        Contract.event == None
    ).first()

    contract_with_event = db_session.query(Contract).filter(
        Contract.signed.is_(True),
        Contract.event != None
    ).first()

    return [signed_contract, not_signed_contract, contract_with_event]


@pytest.fixture(scope="session")
def seed_data_event(db_session, seed_data_collaborator, seed_data_contract):
    event = db_session.query(Event).first()

    return event
