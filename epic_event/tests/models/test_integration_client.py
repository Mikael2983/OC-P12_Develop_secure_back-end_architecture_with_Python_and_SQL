import pytest

from epic_event.models import Client


def test_client_has_commercial(seed_data_client, db_session):
    client = seed_data_client
    assert client.commercial is not None
    assert client.commercial.full_name == "Dup"  # défini dans seed_data_collaborator


def test_client_has_contracts(seed_data_contract, seed_data_client):
    signed_contract = seed_data_contract[0]
    client = seed_data_client

    assert len(client.contracts) >= 1
    assert signed_contract in client.contracts
    assert signed_contract.signed is True


def test_commercial_has_clients(seed_data_collaborator, seed_data_client):
    commercial = seed_data_collaborator["commercial"]

    assert len(commercial.clients) >= 1
    assert seed_data_client in commercial.clients
    assert commercial.clients[0].email == "client@test.com"


def test_archived_client_excluded(db_session, seed_data_client):
    seed_data_client.archived = True
    db_session.commit()

    active_clients = db_session.query(Client).filter_by(archived=False).all()
    assert seed_data_client not in active_clients
    seed_data_client.archived = False
    db_session.commit()



def test_client_persists_if_collaborator_soft_deleted(
        seed_data_collaborator,
        seed_data_client, db_session
):
    commercial = seed_data_collaborator["commercial"]
    client_id = seed_data_client.id

    commercial.archived = True
    db_session.commit()

    remaining_client = db_session.query(Client).filter_by(id=client_id).first()
    assert remaining_client is not None
    assert remaining_client.archived is False
    commercial.archived = False
    db_session.commit()
