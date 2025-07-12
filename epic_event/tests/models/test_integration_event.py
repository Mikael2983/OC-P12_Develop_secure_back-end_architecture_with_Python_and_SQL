import pytest
from epic_event.models import Event, Contract


def test_event_contract_relationship(seed_data_event, db_session):
    event = db_session.query(Event).first()
    assert event.contract is not None
    assert event.contract.total_amount == "300"


def test_event_support_relationship(seed_data_event, db_session):
    event = db_session.query(Event).first()
    assert event.support is not None
    assert event.support.role == "support"


def test_contract_event_backref(seed_data_event, db_session):
    contract = db_session.query(Contract).filter(
        Contract.signed == True, Contract.event != None
    ).first()
    assert contract.event is not None
    assert contract.event.title == "Annual Gala"


def test_update_event_location(seed_data_event, db_session):
    event = db_session.query(Event).first()
    event.location = "Marseille"
    db_session.commit()

    updated = db_session.query(Event).filter_by(id=event.id).first()
    assert updated.location == "Marseille"
    event.location = "Paris"
    db_session.commit()


def test_soft_delete_event_archives_it(seed_data_event, db_session):
    event = db_session.query(Event).first()
    event.archived = True
    db_session.commit()

    active_events = db_session.query(Event).filter_by(archived=False).all()
    assert event not in active_events
    event.archived = False
    db_session.commit()


def test_support_has_events(db_session, seed_data_collaborator):
    support = seed_data_collaborator["support"]
    assert len(support.events) == 1
    assert support.events[0].title == "Annual Gala"


def test_client_event_via_contract(db_session, seed_data_client):
    client = seed_data_client

    signed_contracts = [contract for contract in client.contracts if
                        contract.signed and contract.event]
    assert signed_contracts
    assert signed_contracts[0].event.title == "Annual Gala"
