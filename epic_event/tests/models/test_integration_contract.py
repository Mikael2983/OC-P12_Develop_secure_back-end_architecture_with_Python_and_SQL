import pytest
from models import Contract


def test_contract_client_relationship(seed_data_contract, seed_data_client):
    signed_contract = seed_data_contract[0]
    client = seed_data_client

    assert signed_contract.client is not None
    assert signed_contract.client.id == client.id
    assert signed_contract.client.full_name == client.full_name


def test_client_contracts_relationship(seed_data_client, seed_data_contract):
    client = seed_data_client
    signed_contract = seed_data_contract[0]

    assert len(client.contracts) >= 1
    assert signed_contract in client.contracts


def test_contract_event_relationship(seed_data_contract, seed_data_event):
    contract_with_event = seed_data_contract[2]
    event = seed_data_event

    assert contract_with_event.event is not None
    assert contract_with_event.event.id == event.id
    assert event.title == "Annual Gala"


def test_add_additional_contract_to_client(db_session, seed_data_client, seed_data_contract):
    client = seed_data_client

    new_contract = Contract(
        total_amount="2000",
        amount_due="800",
        created_date=None,
        signed=True,
        client_id=client.id
    )

    db_session.add(new_contract)
    db_session.commit()

    assert db_session.query(Contract).count() >= 4
    assert len(client.contracts) >= 2
    db_session.delete(new_contract)
    db_session.commit()


def test_contract_persists_if_client_soft_deleted(db_session, seed_data_client, seed_data_contract):
    client = seed_data_client
    signed_contract = seed_data_contract[0]

    contract_id = signed_contract.id

    client.archived = True
    db_session.commit()

    remaining_contract = db_session.query(Contract).filter_by(id=contract_id).first()
    assert remaining_contract is not None
    client.archived = False
    db_session.commit()


def test_archived_contract_excluded_from_active_query(db_session, seed_data_contract):
    signed_contract = seed_data_contract[0]

    signed_contract.archived = True
    db_session.commit()

    active_contracts = db_session.query(Contract).filter_by(archived=False).all()
    assert signed_contract not in active_contracts

    signed_contract.archived = False
    db_session.commit()
