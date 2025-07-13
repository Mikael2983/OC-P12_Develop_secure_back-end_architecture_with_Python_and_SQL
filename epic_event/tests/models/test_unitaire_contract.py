from datetime import date
import pytest

from models import Contract


def test_contract_save_and_validation(db_session, seed_data_client):
    client = seed_data_client

    contract = Contract(
        total_amount="1000",
        amount_due="500",
        created_date=date.today(),
        signed=True,
        client_id=client.id,
        archived=False
    )

    db_session.add(contract)
    db_session.commit()

    saved = db_session.query(Contract).filter_by(id=contract.id).first()
    assert saved is not None
    assert saved.total_amount == "1000"
    assert saved.amount_due == "500"
    assert saved.signed is True
    assert saved.client_id == client.id

    db_session.delete(saved)
    db_session.commit()


def test_contract_validation_amounts_fail(db_session, seed_data_contract):
    contract = seed_data_contract[1]

    try:
        db_session.begin_nested()
        contract.total_amount = "-100"
        with db_session.no_autoflush:
            with pytest.raises(ValueError, match="Amounts must be positive."):
                contract.validate_all(db_session)
    finally:
        db_session.rollback()


def test_contract_validation_client_existence_fail(db_session,
                                                   seed_data_contract):
    contract = seed_data_contract[0]
    try:
        db_session.begin_nested()
        contract.client_id = 9999
        with db_session.no_autoflush:
            with pytest.raises(ValueError,
                               match="No client found with id=9999."):
                contract.validate_all(db_session)
    finally:
        db_session.rollback()


def test_contract_save_invalid_signed(db_session, seed_data_contract):
    contract = seed_data_contract[1]
    try:
        db_session.begin_nested()
        contract.signed = "notabool"
        with db_session.no_autoflush:
            contract.validate_all(db_session)
            assert contract.signed == False
    finally:
        db_session.rollback()
