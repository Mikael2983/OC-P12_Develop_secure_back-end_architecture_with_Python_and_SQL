import pytest
from datetime import date
from models import Client

def test_validate_all_success(db_session, seed_data_client):
    client = seed_data_client
    client.validate_all(db_session)


def test_validate_all_full_name_empty_raises(db_session, seed_data_client):
    client = seed_data_client
    client.full_name = "  "
    with pytest.raises(ValueError, match="Full name must not be empty."):
        client.validate_all(db_session)
    db_session.refresh(client)


def test_validate_all_email_invalid_raises(db_session, seed_data_client):
    client = seed_data_client
    client.email = "notanemail"
    with pytest.raises(
            ValueError,
            match=f"Format d'email invalide: {client.email}"
    ):
        client.validate_all(db_session)
    db_session.refresh(client)


def test_validate_all_phone_invalid_raises(db_session, seed_data_client):
    client = seed_data_client
    client.phone = "invalidphone"
    with pytest.raises(ValueError, match="Numéro de téléphone invalide"):
        client.validate_all(db_session)
    db_session.refresh(client)


def test_validate_all_company_name_empty_raises(db_session, seed_data_client):
    client = seed_data_client
    client.company_name = "   "
    with pytest.raises(ValueError, match="nom de l'entreprise.*vide"):
        client.validate_all(db_session)
    db_session.refresh(client)


def test_validate_all_last_contact_date_bad_format_raises(db_session, seed_data_client):
    client = seed_data_client
    with db_session.no_autoflush:
        client.last_contact_date = "12/07/2024"  # mauvais format
        with pytest.raises(ValueError, match="Date invalide ou au mauvais format"):
            client.validate_all(db_session)
    db_session.refresh(client)


def test_client_save_success(db_session, seed_data_collaborator):
    commercial = seed_data_collaborator["commercial"]
    new_client = Client(
        full_name="Sophie Lemaire",
        email="sophie@example.com",
        phone="0123456789",
        company_name="Innova",
        created_date=date.today(),
        last_contact_date=date.today(),
        id_commercial=commercial.id
    )
    new_client.validate_all(db_session)
    db_session.add(new_client)
    db_session.commit()

    saved = db_session.query(Client).filter_by(email="sophie@example.com").first()
    assert saved is not None
    assert saved.full_name == "Sophie Lemaire"

    db_session.delete(new_client)
    db_session.commit()
