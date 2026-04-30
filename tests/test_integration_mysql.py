"""Tests de integracion contra una BD MySQL real.

Solo se ejecutan con:  pytest -m integration

Requieren:
- ~/.funidelia/connections.yaml con una conexion llamada 'PS-slave'
- Credenciales guardadas (ejecutar `python -m funi_data setup PS-slave` antes)
- Acceso de red al host de la conexion
"""
from __future__ import annotations

import pandas as pd
import pytest

from funi_data import connect
from funi_data.connections import get_connection
from funi_data.credentials import get_credentials

CONNECTION_NAME = "PS-slave"


def _skip_if_unavailable() -> None:
    try:
        get_connection(CONNECTION_NAME)
    except (FileNotFoundError, KeyError):
        pytest.skip(f"Conexion '{CONNECTION_NAME}' no definida en connections.yaml")
    if get_credentials(CONNECTION_NAME) is None:
        pytest.skip(f"Credenciales de '{CONNECTION_NAME}' no configuradas")


@pytest.mark.integration
def test_select_one() -> None:
    _skip_if_unavailable()
    with connect(CONNECTION_NAME, interactive=False) as db:
        df = db.query("SELECT 1 AS ok")
        assert isinstance(df, pd.DataFrame)
        assert df.iloc[0]["ok"] == 1


@pytest.mark.integration
def test_select_with_param() -> None:
    _skip_if_unavailable()
    with connect(CONNECTION_NAME, interactive=False) as db:
        df = db.query("SELECT :n AS n", {"n": 42})
        assert df.iloc[0]["n"] == 42


@pytest.mark.integration
def test_tables_listing_returns_something() -> None:
    """Sanity check: la BD prestashop debe tener al menos una tabla."""
    _skip_if_unavailable()
    with connect(CONNECTION_NAME, interactive=False) as db:
        tables = db.tables()
        assert isinstance(tables, list)
        assert len(tables) > 0, "BD prestashop sin tablas? algo raro"
