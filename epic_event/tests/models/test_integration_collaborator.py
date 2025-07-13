import pytest
from models import Collaborator, Event


def test_collaborator_password_and_role(seed_data_collaborator):
    commercial = seed_data_collaborator["commercial"]
    assert commercial.check_password("mypassword") is True
    assert commercial.role == "commercial"


def test_collaborator_has_clients(seed_data_collaborator, seed_data_client ):
    commercial = seed_data_collaborator["commercial"]
    assert len(commercial.clients) >= 1
    assert commercial.clients[0].full_name == "Client Test"


def test_collaborator_support_has_events(db_session, seed_data_collaborator):
    support = seed_data_collaborator["support"]
    events = db_session.query(Event).filter_by(support_id=support.id).all()

    assert len(events) >= 1
    assert events[0].title == "Annual Gala"


def test_archived_collaborator_excluded(db_session, seed_data_collaborator):
    support = seed_data_collaborator["support"]
    support.archived = True
    db_session.commit()

    active = db_session.query(Collaborator).filter_by(archived=False).all()
    assert support not in active
    support.archived = False
    db_session.commit()


def test_client_can_access_commercial(seed_data_client):
    client = seed_data_client
    assert client.commercial is not None
    assert client.commercial.full_name == "Dup"


def test_event_can_access_support(db_session, seed_data_event):
    event = db_session.query(Event).filter_by(title="Annual Gala").first()
    assert event.support is not None
    assert event.support.email == "bob@example.com"
