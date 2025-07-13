import pytest
from models import Client


def test_entity_resolve_simple_field(seed_data_client):
    client = seed_data_client
    value = Client._resolve(client, "email")
    assert value == "client@test.com"


def test_entity_resolve_nested_field(seed_data_client):
    client = seed_data_client
    value = Client._resolve(client, "commercial.full_name")
    assert value == "Dup"  # nom commercial dans seed_data_collaborator


def test_entity_is_valid_path_true():
    assert Client._is_valid_path("commercial__full_name") is True


def test_entity_is_valid_path_false():
    assert Client._is_valid_path("commercial__nonexistent") is False


def test_entity_filter_by_direct_field(db_session, seed_data_client):
    results = Client.filter_by_fields(db_session, full_name="Client Test")

    assert len(results) == 1
    assert results[0].email == "client@test.com"


def test_entity_filter_by_nested_field(db_session, seed_data_collaborator,
                                       seed_data_client):
    commercial = seed_data_collaborator["commercial"]
    results = Client.filter_by_fields(db_session,
                                      commercial__email=commercial.email)
    assert len(results) >= 1
    assert results[0].commercial.email == commercial.email


def test_entity_order_by_field_ascending(db_session, seed_data_client):
    # Ajout d'un client supplémentaire pour tester le tri
    client2 = Client(
        full_name="Aardvark Z",
        email="aa@corp.com",
        phone="0123456789",
        company_name="AZ Corp",
        created_date=None,
        last_contact_date=None,
        id_commercial=seed_data_client.id_commercial
    )
    db_session.add(client2)
    db_session.commit()

    sorted_clients = Client.order_by_fields(db_session, "full_name")
    names = [c.full_name for c in sorted_clients]
    assert "Aardvark Z" in names
    assert "Client Test" in names

    assert names == sorted(names)


def test_entity_update_persists_changes(db_session, seed_data_client):
    client = seed_data_client

    client.update(db_session, full_name="Updated Client")

    updated = db_session.query(Client).filter_by(full_name="Updated Client").first()
    assert updated.full_name == "Updated Client"

    updated.update(db_session, full_name="Client Test")


def test_entity_soft_delete_sets_archived(db_session, seed_data_client):
    client_id = seed_data_client.id

    Client.soft_delete(db_session, client_id)

    refreshed = db_session.query(Client).filter_by(id=client_id).first()
    assert refreshed.archived is True

    refreshed.archived = False
    db_session.commit()
