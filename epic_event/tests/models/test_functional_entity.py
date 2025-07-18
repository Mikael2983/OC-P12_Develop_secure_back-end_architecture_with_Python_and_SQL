import pytest

from epic_event.models import Client, Collaborator


def test_order_by_fields_functional(seed_data_collaborator, db_session):
    sorted_collabs = Collaborator.order_by_fields(db_session, "full_name")
    names = [c.full_name for c in sorted_collabs]

    assert names == ["Admin", "Alice", "Bob", "Dup"]


def test_filter_by_fields_functional(db_session, seed_data_collaborator):
    result = Collaborator.filter_by_fields(db_session, full_name="Alice")
    assert len(result) == 1
    assert result[0].email == "alice@example.com"


def test_soft_delete_functional(db_session, seed_data_collaborator):
    active_collaborators = db_session.query(Collaborator).filter_by(archived=False).all()
    names = [c.full_name for c in active_collaborators]

    assert names == ['Alice', 'Dup', 'Bob', 'Admin']
