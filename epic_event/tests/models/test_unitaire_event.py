from datetime import date, timedelta
import pytest

from epic_event.models import Event


def test_validate_title_empty_raises(db_session, seed_data_event):
    event = seed_data_event
    try:
        db_session.begin_nested()
        event.title = ""
        with db_session.no_autoflush:
            with pytest.raises(ValueError, match="Title is required."):
                event.validate_all(db_session)
    finally:
        db_session.refresh(event)


def test_validate_dates_invalid_type_raises(db_session, seed_data_event):
    event = seed_data_event

    try:
        db_session.begin_nested()
        event.start_date = "2023-01-01"
        event.end_date = "2023-01-02"
        with db_session.no_autoflush:
            with pytest.raises(ValueError, match="Start and end dates must be valid date instances."):
                event.validate_all(db_session)
    finally:
        db_session.refresh(event)


def test_validate_dates_start_after_end_raises(db_session, seed_data_event):
    event = seed_data_event

    try:
        db_session.begin_nested()
        event.start_date = date.today() + timedelta(days=5)
        event.end_date = date.today()
        with db_session.no_autoflush:
            with pytest.raises(ValueError, match="Start date cannot be after end date."):
                event.validate_all(db_session)
    finally:
        db_session.refresh(event)


def test_validate_participants_negative_raises(db_session, seed_data_event):
    event = seed_data_event

    try:
        db_session.begin_nested()
        event.participants = -10
        with db_session.no_autoflush:
            with pytest.raises(ValueError, match="Participants must be a positive integer."):
                event.validate_all(db_session)
    finally:
        db_session.refresh(event)


def test_validate_contract_id_missing_raises(db_session, seed_data_event):
    event = seed_data_event

    try:
        db_session.begin_nested()
        event.contract_id = 9999  # ID inexistant
        with db_session.no_autoflush:
            with pytest.raises(ValueError, match=f"Contract ID {event.contract_id} not found."):
                event.validate_all(db_session)
    finally:
        db_session.refresh(event)


def test_validate_contract_not_signed_raises(db_session, seed_data_event,
                                             seed_data_contract):
    not_signed_contract = seed_data_contract[1]
    event = seed_data_event

    try:
        db_session.begin_nested()
        event.contract_id = not_signed_contract.id
        with db_session.no_autoflush:
            with pytest.raises(ValueError, match="The contract must be signed before assigning to an event."):
                event.validate_all(db_session)
    finally:
        db_session.refresh(event)


def test_validate_support_id_not_found_raises(db_session, seed_data_event):
    event = seed_data_event

    try:
        db_session.begin_nested()
        event.support_id = 9999  # ID inexistant
        with db_session.no_autoflush:
            with pytest.raises(ValueError, match=f"Collaborator ID {event.support_id} not found."):
                event.validate_all(db_session)
    finally:
        db_session.refresh(event)


def test_validate_support_id_invalid_role_raises(db_session, seed_data_event,
                                                 seed_data_collaborator):
    collab = seed_data_collaborator["commercial"]  # mauvais rôle
    event = seed_data_event

    try:
        db_session.begin_nested()
        event.support_id = collab.id
        with db_session.no_autoflush:
            with pytest.raises(ValueError, match="The selected collaborator is not in the 'support' role."):
                event.validate_all(db_session)
    finally:
        db_session.refresh(event)


def test_save_success(db_session, seed_data_contract):
    signed_contract = seed_data_contract[0]

    event = Event(
        title="Test Event",
        start_date=date.today(),
        end_date=date.today(),
        participants=100,
        contract_id=signed_contract.id,
    )

    event.save(db_session)
    found = db_session.query(Event).filter_by(title="Test Event").first()
    assert found is not None
    db_session.delete(found)
    db_session.commit()


def test_save_validation_error_triggers_rollback(db_session, seed_data_event):
    event = seed_data_event
    event.title = ""
    with db_session.no_autoflush:
        with pytest.raises(ValueError):
            event.save(db_session)

        events = db_session.query(Event).all()
        assert all(e.title != "" for e in events)
    db_session.refresh(event)
