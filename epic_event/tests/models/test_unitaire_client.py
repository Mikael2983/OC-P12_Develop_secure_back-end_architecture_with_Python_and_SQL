from datetime import date, datetime

import pytest

from epic_event.models import Client


def test_validate_all_success(seed_data_collaborator, db_session):
    client = Client(
        full_name="Marc Petit",
        email="marc@alphacorp.com",
        phone="0758493021",
        company_name="AlphaCorp",
        created_date=date.today(),
        last_contact_date=date.today(),
        id_commercial=seed_data_collaborator["commercial"].id)

    with db_session.no_autoflush:
        client.validate_all(db_session)


def test_invalid_full_name_raises(seed_data_client, db_session):
    client = seed_data_client
    try:
        db_session.begin_nested()
        client.full_name = "   "
        with db_session.no_autoflush:
            with pytest.raises(ValueError, match="Full name must not be empty."):
                client.validate_all(db_session)
    finally:
        db_session.rollback()


def test_invalid_email_format_raises(db_session, seed_data_client):
    client = seed_data_client
    try:
        db_session.begin_nested()
        client.email = "bademail"
        with db_session.no_autoflush:
            with pytest.raises(ValueError, match="Format d'email invalide"):
                client.validate_all(db_session)
    finally:
        db_session.rollback()


def test_invalid_phone_format_raises(db_session, seed_data_client):
    client = seed_data_client
    try:
        db_session.begin_nested()
        client.phone = "999999999"
        with db_session.no_autoflush:
            with pytest.raises(ValueError, match="Numéro de téléphone invalide"):
                client.validate_all(db_session)
    finally:
        db_session.rollback()


def test_invalid_company_name_raises(db_session, seed_data_client):
    client = seed_data_client
    try:
        db_session.begin_nested()
        client.company_name = "   "
        with db_session.no_autoflush:
            with pytest.raises(ValueError, match="nom de l'entreprise.*vide"):
                client.validate_all(db_session)
    finally:
        db_session.rollback()


def test_invalid_date_format_raises(db_session, seed_data_client):
    client = seed_data_client
    try:
        db_session.begin_nested()
        client.last_contact_date = "12/01/2023"
        with db_session.no_autoflush:
            with pytest.raises(ValueError, match="Date invalide.*format"):
                client.validate_all(db_session)
    finally:
        db_session.rollback()


def test_invalid_date_type_raises(db_session, seed_data_client):
    client = seed_data_client
    try:
        db_session.begin_nested()
        client.last_contact_date = 12345
        with db_session.no_autoflush:
            with pytest.raises(ValueError, match="La date doit être une instance"):
                client.validate_all(db_session)
    finally:
        db_session.rollback()


@pytest.mark.parametrize("phone", [
    "01 23 45 67 89",
    "01-23-45-67-89",
    "0123456789",
    "+33123456789",
    "+33 1 23 45 67 89",
])
def test_valid_phone_formats(phone, seed_data_client, db_session):
    client = seed_data_client
    try:
        db_session.begin_nested()
        client.phone = phone
        with db_session.no_autoflush:
            client.validate_all(db_session)
    finally:
        db_session.rollback()


def test_valid_dates(db_session, seed_data_client):
    client = seed_data_client
    try:
        db_session.begin_nested()
        client.created_date = date.today(),
        client.last_contact_date = datetime.strptime(
            "07-08-2025",
            "%d-%m-%Y"
        )
        with db_session.no_autoflush:
            client.validate_all(db_session)
    finally:
        db_session.rollback()
