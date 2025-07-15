import pytest

from epic_event.models import Collaborator, Client


def test_create_collaborator_and_set_password():
    collab = Collaborator(full_name="Alice", email="alice@example.com",
                          role="admin")
    collab.set_password("secret123")
    assert collab.check_password("secret123") is True
    assert collab.full_name == "Alice"


def test_check_password_returns_true(db_session, seed_data_collaborator):
    collab = seed_data_collaborator["gestion"]
    collab.set_password("mypassword")
    assert collab.check_password("mypassword") is True


def test_check_password_returns_false(db_session, seed_data_collaborator):
    collab = seed_data_collaborator["gestion"]
    collab.set_password("mypassword")
    assert collab.check_password("wrongpass") is False
    db_session.refresh(collab)


def test_validate_all_raises_if_duplicate_full_name(db_session,
                                                    seed_data_collaborator):
    collab = Collaborator(full_name="Dup", email="other@example.com",
                          role="commercial")
    collab.set_password("pass2")

    with pytest.raises(ValueError, match="already in use"):
        collab.validate_all(db_session)


def test_validate_all_does_not_raise(db_session, seed_data_collaborator):
    collab = seed_data_collaborator["commercial"]

    collab.validate_all(db_session)


def test_save_persists_in_database(db_session):
    collab = Collaborator(full_name="Diane", email="diane@example.com",
                          role="gestion")
    collab.set_password("123456")
    collab.save(db_session)

    found = db_session.query(Collaborator).filter_by(
        email="diane@example.com").first()
    assert found is not None
    assert found.full_name == "Diane"
    db_session.delete(found)
    db_session.commit()


def test_filter_by_fields_returns_correct_result(db_session,
                                                 seed_data_collaborator):
    result = Collaborator.filter_by_fields(db_session, full_name="Alice")
    assert len(result) == 1
    assert result[0].email == "alice@example.com"
