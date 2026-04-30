"""Tests de carga y validación de connections.yaml."""
from __future__ import annotations

from pathlib import Path

import pytest

from funi_data.connections import (
    Connection,
    get_connection,
    load_connections,
)


def _write_yaml(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "connections.yaml"
    p.write_text(content, encoding="utf-8")
    return p


def test_load_minimal(tmp_path: Path) -> None:
    p = _write_yaml(
        tmp_path,
        """
connections:
  - name: test-mysql
    type: mysql
    host: 10.0.0.1
    port: 3306
    database: testdb
""",
    )
    conns = load_connections(p)
    assert set(conns) == {"test-mysql"}
    c = conns["test-mysql"]
    assert isinstance(c, Connection)
    assert c.type == "mysql"
    assert c.port == 3306
    assert c.db_schema is None
    assert c.description is None


def test_load_with_schema_alias(tmp_path: Path) -> None:
    p = _write_yaml(
        tmp_path,
        """
connections:
  - name: pg
    type: postgresql
    host: db.local
    port: 5432
    database: app
    schema: public
    description: "Postgres dev"
""",
    )
    c = load_connections(p)["pg"]
    assert c.db_schema == "public"
    assert c.description == "Postgres dev"


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_connections(tmp_path / "nope.yaml")


def test_duplicate_name_raises(tmp_path: Path) -> None:
    p = _write_yaml(
        tmp_path,
        """
connections:
  - {name: dup, type: mysql, host: h, port: 3306, database: d}
  - {name: dup, type: mysql, host: h2, port: 3306, database: d2}
""",
    )
    with pytest.raises(ValueError, match="duplicada"):
        load_connections(p)


def test_invalid_type_raises(tmp_path: Path) -> None:
    p = _write_yaml(
        tmp_path,
        """
connections:
  - {name: x, type: oracle, host: h, port: 1521, database: d}
""",
    )
    with pytest.raises(Exception):  # pydantic ValidationError
        load_connections(p)


def test_invalid_port_raises(tmp_path: Path) -> None:
    p = _write_yaml(
        tmp_path,
        """
connections:
  - {name: x, type: mysql, host: h, port: 99999, database: d}
""",
    )
    with pytest.raises(Exception):
        load_connections(p)


def test_get_connection_found(tmp_path: Path) -> None:
    p = _write_yaml(
        tmp_path,
        """
connections:
  - {name: a, type: mysql, host: h, port: 3306, database: d}
""",
    )
    c = get_connection("a", p)
    assert c.name == "a"


def test_get_connection_not_found(tmp_path: Path) -> None:
    p = _write_yaml(
        tmp_path,
        """
connections:
  - {name: a, type: mysql, host: h, port: 3306, database: d}
""",
    )
    with pytest.raises(KeyError, match="no encontrada"):
        get_connection("missing", p)


def test_extra_fields_rejected(tmp_path: Path) -> None:
    p = _write_yaml(
        tmp_path,
        """
connections:
  - {name: a, type: mysql, host: h, port: 3306, database: d, extra_field: foo}
""",
    )
    with pytest.raises(Exception):
        load_connections(p)
