"""Tests de credenciales — usan el fake_keyring de conftest, NO tocan Credential Manager."""
from __future__ import annotations

import pytest

from funi_data.credentials import (
    SERVICE_NAMESPACE,
    delete_credentials,
    ensure_credentials,
    get_credentials,
    set_credentials,
)


def test_get_returns_none_when_missing(fake_keyring) -> None:
    assert get_credentials("noexiste") is None


def test_set_and_get_roundtrip(fake_keyring) -> None:
    set_credentials("mysql-test", "alice", "s3cret")
    assert get_credentials("mysql-test") == ("alice", "s3cret")


def test_set_overwrites(fake_keyring) -> None:
    set_credentials("mysql-test", "alice", "old")
    set_credentials("mysql-test", "alice", "new")
    assert get_credentials("mysql-test") == ("alice", "new")


def test_delete_removes_both_keys(fake_keyring) -> None:
    set_credentials("mysql-test", "alice", "s3cret")
    delete_credentials("mysql-test")
    assert get_credentials("mysql-test") is None


def test_delete_idempotent(fake_keyring) -> None:
    delete_credentials("nada")  # no debe lanzar


def test_set_rejects_empty_user(fake_keyring) -> None:
    with pytest.raises(ValueError):
        set_credentials("c", "", "pwd")


def test_set_rejects_empty_password(fake_keyring) -> None:
    with pytest.raises(ValueError):
        set_credentials("c", "user", "")


def test_namespace_isolated_per_connection(fake_keyring) -> None:
    set_credentials("conn-a", "user_a", "pwd_a")
    set_credentials("conn-b", "user_b", "pwd_b")
    assert get_credentials("conn-a") == ("user_a", "pwd_a")
    assert get_credentials("conn-b") == ("user_b", "pwd_b")
    delete_credentials("conn-a")
    assert get_credentials("conn-a") is None
    assert get_credentials("conn-b") == ("user_b", "pwd_b")


def test_service_namespace_format(fake_keyring) -> None:
    """Sanity check: el namespace en el vault es predecible."""
    set_credentials("conn-x", "u", "p")
    # accedemos al store interno para verificar el formato del service
    store = fake_keyring._store
    assert (f"{SERVICE_NAMESPACE}/conn-x", "_user") in store
    assert (f"{SERVICE_NAMESPACE}/conn-x", "_password") in store


def test_ensure_returns_existing(fake_keyring) -> None:
    set_credentials("c", "u", "p")
    assert ensure_credentials("c") == ("u", "p")


def test_ensure_non_interactive_raises_when_missing(fake_keyring) -> None:
    with pytest.raises(LookupError, match="setup"):
        ensure_credentials("missing", interactive=False)


def test_ensure_interactive_calls_prompt(fake_keyring, monkeypatch) -> None:
    """Cuando faltan credenciales en modo interactivo, se debe llamar al wizard."""
    monkeypatch.setattr("builtins.input", lambda _prompt="": "wizard_user")
    monkeypatch.setattr("getpass.getpass", lambda _prompt="": "wizard_pwd")
    user, pwd = ensure_credentials("nueva")
    assert (user, pwd) == ("wizard_user", "wizard_pwd")
    # y deben quedar persistidas
    assert get_credentials("nueva") == ("wizard_user", "wizard_pwd")
