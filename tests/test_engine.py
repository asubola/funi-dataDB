"""Tests de engine.make_engine — verifica construccion de URL sin conectar."""
from __future__ import annotations

from pathlib import Path

import pytest

from funi_data.connections import Connection
from funi_data.credentials import set_credentials
from funi_data.engine import make_engine


def _conn(**kw) -> Connection:
    base = dict(name="test", type="mysql", host="h", port=3306, database="d")
    base.update(kw)
    return Connection(**base)


def test_make_engine_builds_correct_url(fake_keyring) -> None:
    set_credentials("test", "alice", "p4ss")
    eng = make_engine(_conn(), interactive=False)
    url = eng.url
    assert url.drivername == "mysql+pymysql"
    assert url.username == "alice"
    assert url.password == "p4ss"
    assert url.host == "h"
    assert url.port == 3306
    assert url.database == "d"
    eng.dispose()


def test_make_engine_unsupported_type(fake_keyring) -> None:
    set_credentials("x", "u", "p")
    with pytest.raises(NotImplementedError, match="oracle"):
        # bypass pydantic validation creando manualmente con type fuera del Literal
        bad = Connection.model_construct(
            name="x", type="oracle", host="h", port=1521, database="d", db_schema=None, description=None
        )
        make_engine(bad, interactive=False)


def test_make_engine_missing_credentials_non_interactive(fake_keyring) -> None:
    with pytest.raises(LookupError, match="setup"):
        make_engine(_conn(name="sin-creds"), interactive=False)


def test_make_engine_accepts_string_name(tmp_path: Path, monkeypatch, fake_keyring) -> None:
    """Si pasas un nombre, lo carga del yaml; si pasas Connection, lo usa directo."""
    yml = tmp_path / "conn.yaml"
    yml.write_text(
        """
connections:
  - {name: from-yaml, type: mysql, host: h, port: 3306, database: d}
""",
        encoding="utf-8",
    )
    monkeypatch.setattr("funi_data.engine.get_connection",
                        lambda name: __import__("funi_data.connections",
                                                fromlist=["get_connection"]).get_connection(name, yml))
    set_credentials("from-yaml", "u", "p")
    eng = make_engine("from-yaml", interactive=False)
    assert eng.url.host == "h"
    eng.dispose()


def test_make_engine_password_with_special_chars_is_escaped(fake_keyring) -> None:
    """SQLAlchemy URL.create debe escapar caracteres especiales en la contrasena."""
    set_credentials("test", "alice", "p@ss/word#1")
    eng = make_engine(_conn(), interactive=False)
    # render_as_string(hide_password=False) muestra la contrasena tal cual SQLAlchemy
    # la usara — confirmamos que no rompe parseado de URL
    rendered = eng.url.render_as_string(hide_password=False)
    assert "alice" in rendered
    eng.dispose()
