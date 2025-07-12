import pytest
from datetime import date, timedelta
from epic_event.models import Contract, Client


def test_validate_all_success(
        db_session,
        seed_data_contract
):
    signed_contract = seed_data_contract[0]

    signed_contract.validate_all(db_session)


def test_validate_all_amounts_invalid_total_raises(
        db_session,
        seed_data_client,
        seed_data_contract
):

    contract = seed_data_contract[0]
    contract.total_amount = "notanumber"

    with pytest.raises(ValueError, match="valid numeric values"):
        contract.validate_all(db_session)
    db_session.refresh(contract)


def test_validate_all_amount_due_greater_than_total_raises(
        db_session,
        seed_data_client,
        seed_data_contract
):
    contract = seed_data_contract[0]
    contract.total_amount = "500"
    contract.amount_due = "600"

    with pytest.raises(ValueError, match="cannot exceed total"):
        contract.validate_all(db_session)
    db_session.refresh(contract)


def test_validate_all_client_id_not_found_raises(
        db_session,
        seed_data_contract
):

    contract = seed_data_contract[0]
    contract.client_id = 9999  # Inexistant

    with pytest.raises(ValueError, match="No client found with id"):
        contract.validate_all(db_session)

    db_session.refresh(contract)
