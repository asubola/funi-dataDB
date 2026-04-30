"""Fixtures compartidas. Usamos un keyring en memoria para no tocar el vault real del usuario."""
from __future__ import annotations

import keyring
import keyring.backend
import pytest


class InMemoryKeyring(keyring.backend.KeyringBackend):
    """Backend trivial para tests — vive en RAM, sin tocar Credential Manager."""

    priority = 1  # cualquier valor; no compite con backends reales

    def __init__(self) -> None:
        self._store: dict[tuple[str, str], str] = {}

    def set_password(self, service: str, username: str, password: str) -> None:
        self._store[(service, username)] = password

    def get_password(self, service: str, username: str) -> str | None:
        return self._store.get((service, username))

    def delete_password(self, service: str, username: str) -> None:
        try:
            del self._store[(service, username)]
        except KeyError as e:
            raise keyring.errors.PasswordDeleteError(str(e)) from e


@pytest.fixture
def fake_keyring(monkeypatch: pytest.MonkeyPatch) -> InMemoryKeyring:
    backend = InMemoryKeyring()
    monkeypatch.setattr(keyring, "get_keyring", lambda: backend)
    monkeypatch.setattr(keyring, "set_password", backend.set_password)
    monkeypatch.setattr(keyring, "get_password", backend.get_password)
    monkeypatch.setattr(keyring, "delete_password", backend.delete_password)
    return backend
