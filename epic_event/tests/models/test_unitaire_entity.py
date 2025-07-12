import pytest
from epic_event.models import Client



def test_resolve_direct_field(seed_data_client):
    client = seed_data_client
    assert Client._resolve(client, "email") == "client@test.com"


def test_resolve_missing_field(seed_data_client):
    client = seed_data_client
    assert Client._resolve(client, "nonexistent_field") == ""


def test_resolve_nested_existing_object(seed_data_client):
    """
    Vérifie que la résolution de client.commercial.full_name fonctionne.
    """
    client = seed_data_client
    assert Client._resolve(client, "commercial.full_name") == "Dup"


def test_resolve_nested_none():
    """
    Simule client.commercial = None → devrait retourner ""
    """
    client = Client(commercial=None)
    assert Client._resolve(client, "commercial.full_name") == ""


def test_is_valid_path_valid():
    """
    Teste un chemin relationnel valide : Client.contracts.event.id
    """
    assert Client._is_valid_path("contracts__event__id") is True


def test_is_valid_path_invalid():
    """
    Teste un chemin invalide : Client n'a pas directement 'invalid'.
    """
    assert Client._is_valid_path("contracts__invalid__id") is False
