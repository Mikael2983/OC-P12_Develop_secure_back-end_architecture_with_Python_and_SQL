from datetime import date, timedelta
import pytest

from epic_event.models import Event


def test_validate_all_success(seed_data_event, db_session):
    event = seed_data_event

    event.validate_all(db_session)


def test_validate_title_empty_raises(seed_data_event, db_session):
    event = seed_data_event

    event.title = "  "

    with db_session.no_autoflush:
        with pytest.raises(ValueError, match="Title is required"):
            event.validate_all(db_session)

    db_session.refresh(event)


def test_validate_dates_invalid_type_raises(seed_data_event, db_session):
    event = seed_data_event

    event.start_date = "2024-01-01",
    event.end_date = "2024-01-02",
    with db_session.no_autoflush:
        with pytest.raises(ValueError, match="must be valid date instances"):
            event.validate_all(db_session)
    db_session.refresh(event)


def test_validate_dates_start_after_end_raises(seed_data_event, seed_data_collaborator, db_session):
    event = seed_data_event
    event.start_date = date.today() + timedelta(days=1)
    event.end_date = date.today()
    with db_session.no_autoflush:
        with pytest.raises(ValueError, match="Start date cannot be after end date"):
            event.validate_all(db_session)

    db_session.refresh(event)


def test_validate_participants_negative_raises(seed_data_event, seed_data_collaborator, db_session):
    event = seed_data_event
    event.participants = -10
    with db_session.no_autoflush:
        with pytest.raises(ValueError, match="Participants must be a positive integer."):
            event.validate_all(db_session)

    db_session.refresh(event)


def test_validate_contract_id_not_found_raises(seed_data_collaborator, seed_data_event, db_session):

    event = seed_data_event
    event.contract_id = 9999
    with db_session.no_autoflush:
        with pytest.raises(ValueError, match="Contract ID 9999 not found"):
            event.validate_all(db_session)

    db_session.refresh(event)


def test_validate_contract_not_signed_raises(seed_data_contract, seed_data_event, seed_data_client, seed_data_collaborator, db_session):

    not_signed_contract = seed_data_contract[1]
    event = seed_data_event
    event.contract_id = not_signed_contract.id
    with db_session.no_autoflush:
        with pytest.raises(ValueError, match="must be signed before assigning"):
            event.validate_all(db_session)

    db_session.refresh(event)


def test_validate_support_id_not_found_raises(
        seed_data_contract,
        seed_data_event,
        db_session
):
    event = seed_data_event
    event.support_id = 9999
    with db_session.no_autoflush:
        with pytest.raises(ValueError, match="Collaborator ID 9999 not found"):
            event.validate_all(db_session)

    db_session.refresh(event)


def test_validate_support_wrong_role_raises(seed_data_contract, seed_data_event, seed_data_collaborator, db_session):

    commercial = seed_data_collaborator["commercial"]
    event = seed_data_event
    event.support_id = commercial.id

    with db_session.no_autoflush:
        with pytest.raises(ValueError, match="not in the 'support' role"):
            event.validate_all(db_session)

    db_session.refresh(event)


def test_event_save_success(seed_data_contract, seed_data_collaborator, db_session):
    signed_contract = seed_data_contract[0]
    support = seed_data_collaborator["support"]

    event = Event(
        title="Forum Devs",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=1),
        participants=50,
        location="Lyon",
        notes="Tech forum",
        contract_id=signed_contract.id,
        support_id=support.id
    )

    event.save(db_session)

    found = db_session.query(Event).filter_by(title="Forum Devs").first()

    assert found is not None
    assert found.contract_id == signed_contract.id
    db_session.delete(found)
    db_session.commit()
