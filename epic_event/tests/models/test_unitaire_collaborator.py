import pytest
from unittest.mock import patch

from epic_event.models import Collaborator


def test_validate_full_name_ok(db_session):

    collab = Collaborator(full_name="John Doe",
                          email="john@example.com",
                          role="support")
    collab._validate_full_name(db_session)


def test_validate_full_name_empty_raises(db_session):

    collab = Collaborator(full_name="   ",
                          email="john@example.com",
                          role="support")

    with pytest.raises(ValueError, match="Full name must not be empty"):
        collab._validate_full_name(db_session)


def test_validate_full_name_duplicate_raises(db_session):

    collab = Collaborator(full_name="Bob",
                          email="bob2@example.com",
                          role="support")

    with db_session.no_autoflush:
        with pytest.raises(ValueError, match="already in use"):
            collab._validate_full_name(db_session)


def test_validate_email_valid(db_session):
    collab = Collaborator(full_name="Test",
                          email="valid@example.com",
                          role="support")

    collab._validate_email(db_session, collab.email)


def test_validate_email_invalid_format(db_session):
    collab = Collaborator(full_name="Test",
                          email="invalid-email",
                          role="support")

    with pytest.raises(ValueError, match="Invalid email"):
        collab._validate_email(db_session, collab.email)


def test_validate_email_duplicate(db_session):
    # Email "bob@example.com" est déjà utilisé
    collab = Collaborator(full_name="Another",
                          email="bob@example.com",
                          role="support")

    with pytest.raises(ValueError, match="already in use"):
        collab._validate_email(db_session, collab.email)


@pytest.mark.parametrize("role", ["support", "gestion", "commercial", "admin"])
def test_validate_role_ok(role):
    collab = Collaborator(full_name="Test",
                          email="role@example.com",
                          role=role)
    collab._validate_role(collab.role)


def test_validate_role_invalid():
    collab = Collaborator(full_name="Test",
                          email="r@t.com",
                          role="invalid")

    with pytest.raises(ValueError, match="Invalid role"):
        collab._validate_role(collab.role)


def test_save_success(db_session):
    collab = Collaborator(full_name="Joe",
                          email="joe@example.com",
                          role="support")
    collab.set_password("securepass")

    collab.save(db_session)

    found = db_session.query(Collaborator).filter_by(
        email="joe@example.com"
    ).first()

    assert found is not None

    db_session.delete(found)
    db_session.commit()


def test_set_password_and_check():
    collab = Collaborator(full_name="X", email="x@example.com", role="support")
    collab.set_password("mypassword")
    assert collab.check_password("mypassword") is True
    assert collab.check_password("wrongpass") is False

