import re
from datetime import date, timedelta, datetime

import pytest

from epic_event.models import Event


def test_formatted_start_date_property(seed_data_event):
    event = seed_data_event
    assert event.formatted_start_date == "08/06/2025 09:00"


def test_formatted_end_date_property(seed_data_event):
    event = seed_data_event

    assert event.formatted_end_date == "10/06/2025 18:00"


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


def test_full_data_provided():
    data = {"start_date": "2025-08-01", "start_time": "09:30"}
    result = Event.combine_datetime(data, "start")
    assert result == datetime(2025, 8, 1, 9, 30)


def test_missing_time_uses_fallback():
    fallback = datetime(2025, 8, 1, 14, 45)
    data = {"start_date": "2025-08-01"}
    result = Event.combine_datetime(data, "start", fallback=fallback)
    assert result == datetime(2025, 8, 1, 14, 45)


def test_missing_date_uses_fallback():
    fallback = datetime(2025, 8, 1, 14, 45)
    data = {"start_time": "10:00"}
    result = Event.combine_datetime(data, "start", fallback=fallback)
    assert result == datetime(2025, 8, 1, 10, 0)


def test_missing_both_raises():
    with pytest.raises(ValueError) as exc_info:
        Event.combine_datetime({}, "start")
    assert "Missing required date field" in str(exc_info.value)


def test_valid_string_dates():
    event = Event(
        title="My Event",
        start_date="01-08-2025 09:00",
        end_date="01-08-2025 11:00",
        contract_id=1
    )
    event._validate_dates()
    assert isinstance(event.start_date, datetime)
    assert isinstance(event.end_date, datetime)


def test_valid_datetime_objects():
    event = Event(
        title="My Event",
        start_date=datetime(2025, 8, 1, 9, 0),
        end_date=datetime(2025, 8, 1, 11, 0),
        contract_id=1
    )
    event._validate_dates()
    assert isinstance(event.start_date, datetime)


def test_start_after_end_raises():
    event = Event(
        title="Wrong Dates",
        start_date="03-08-2025 10:00",
        end_date="01-08-2025 09:00",
        contract_id=1
    )
    with pytest.raises(ValueError) as exc_info:
        event._validate_dates()
    assert "La date de début ne peut pas être postérieure" in str(
        exc_info.value)


def test_invalid_date_format_raises():
    event = Event(
        title="Invalid Format",
        start_date="2025/08/01 10:00",
        end_date="01-08-2025 11:00",
        contract_id=1
    )
    with pytest.raises(ValueError) as exc_info:
        event._validate_dates()
    assert "Date invalide ou au mauvais format" in str(exc_info.value)


def test_invalid_type_raises():
    event = Event(
        title="Wrong Type",
        start_date=123456,
        end_date="01-08-2025 11:00",
        contract_id=1
    )
    with pytest.raises(ValueError) as exc_info:
        event._validate_dates()
    assert "La date doit être une instance de `datetime`" in str(
        exc_info.value)


def test_validate_participants_negative_raises(db_session, seed_data_event):
    event = seed_data_event

    try:
        db_session.begin_nested()
        event.participants = -10
        with db_session.no_autoflush:
            with pytest.raises(ValueError,
                               match="Participants must be a positive integer."):
                event.validate_all(db_session)
    finally:
        db_session.refresh(event)


def test_validate_contract_id_missing_raises(db_session, seed_data_event):
    event = seed_data_event

    try:
        db_session.begin_nested()
        event.contract_id = 9999  # ID inexistant
        with db_session.no_autoflush:
            with pytest.raises(ValueError,
                               match=f"Contract ID {event.contract_id} not found."):
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
            with pytest.raises(ValueError,
                               match="The contract must be signed before "
                                     "assigning to an event."
                               ):
                event.validate_all(db_session)
    finally:
        db_session.refresh(event)


def test_validate_support_id_not_found_raises(db_session, seed_data_event):
    event = seed_data_event

    try:
        db_session.begin_nested()
        event.support_id = 9999  # ID inexistant
        with db_session.no_autoflush:
            with pytest.raises(ValueError,
                               match=f"Collaborator ID {event.support_id} not "
                                     f"found."
                               ):
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
            with pytest.raises(ValueError,
                               match="The selected collaborator is not in the "
                                     "'support' role."
                               ):
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
