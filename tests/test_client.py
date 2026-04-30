"""Tests de Database + connect() usando SQLite en memoria como BD ficticia."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
from sqlalchemy import create_engine, text

from funi_data.client import Database, connect
from funi_data.connections import Connection


def _meta() -> Connection:
    return Connection(name="test", type="mysql", host="h", port=3306, database="d")


@pytest.fixture
def sqlite_engine():
    """Engine SQLite en memoria con datos de prueba — sustituto del MySQL real."""
    eng = create_engine("sqlite:///:memory:", future=True)
    with eng.begin() as c:
        c.execute(text("CREATE TABLE products (id INTEGER, name TEXT)"))
        c.execute(text("INSERT INTO products VALUES (1, 'foo'), (2, 'bar')"))
    yield eng
    eng.dispose()


def test_database_query_returns_dataframe(sqlite_engine) -> None:
    with sqlite_engine.connect() as conn:
        db = Database(conn, _meta(), sqlite_engine)
        df = db.query("SELECT * FROM products ORDER BY id")
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["id", "name"]
        assert df.iloc[0].to_dict() == {"id": 1, "name": "foo"}


def test_database_query_with_params(sqlite_engine) -> None:
    with sqlite_engine.connect() as conn:
        db = Database(conn, _meta(), sqlite_engine)
        df = db.query("SELECT name FROM products WHERE id = :pid", {"pid": 2})
        assert df.iloc[0]["name"] == "bar"


def test_database_tables(sqlite_engine) -> None:
    with sqlite_engine.connect() as conn:
        db = Database(conn, _meta(), sqlite_engine)
        assert "products" in db.tables()


def test_database_columns(sqlite_engine) -> None:
    with sqlite_engine.connect() as conn:
        db = Database(conn, _meta(), sqlite_engine)
        cols = db.columns("products")
        names = [c["name"] for c in cols]
        assert "id" in names and "name" in names


def test_database_properties(sqlite_engine) -> None:
    with sqlite_engine.connect() as conn:
        db = Database(conn, _meta(), sqlite_engine)
        assert db.name == "test"
        assert db.type == "mysql"
        assert db.database == "d"
        assert "test" in repr(db)


def test_database_raw_returns_sa_connection(sqlite_engine) -> None:
    with sqlite_engine.connect() as conn:
        db = Database(conn, _meta(), sqlite_engine)
        result = db.raw().execute(text("SELECT 1 AS x")).scalar()
        assert result == 1


def test_connect_context_manager_closes_resources(tmp_path, monkeypatch, fake_keyring) -> None:
    """connect() debe cerrar conexion y dispose el engine al salir del with."""
    yml = tmp_path / "conn.yaml"
    yml.write_text(
        """
connections:
  - {name: ctx-test, type: mysql, host: h, port: 3306, database: d}
""",
        encoding="utf-8",
    )
    monkeypatch.setattr("funi_data.client.get_connection",
                        lambda name: __import__("funi_data.connections",
                                                fromlist=["get_connection"]).get_connection(name, yml))

    fake_engine = create_engine("sqlite:///:memory:", future=True)
    disposed = {"flag": False}
    original_dispose = fake_engine.dispose

    def tracking_dispose(*a, **k):
        disposed["flag"] = True
        original_dispose(*a, **k)

    fake_engine.dispose = tracking_dispose
    monkeypatch.setattr("funi_data.client.make_engine", lambda meta, interactive: fake_engine)

    with connect("ctx-test") as db:
        df = db.query("SELECT 1 AS x")
        assert df.iloc[0]["x"] == 1

    assert disposed["flag"], "engine.dispose() no se llamo al salir del with"
