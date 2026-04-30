"""API de alto nivel: connect() context manager + clase Database.

Uso tipico:

    from funi_data import connect

    with connect("PS-slave") as db:
        df = db.query("SELECT id_product, name FROM ps_product LIMIT 10")
        print(df)
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import pandas as pd
from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection as _SAConnection
from sqlalchemy.engine import Engine

from .connections import Connection, get_connection
from .engine import make_engine


class Database:
    """Wrapper sobre una conexion SQLAlchemy activa.

    No instanciar directamente — usar `connect()` como context manager.
    """

    def __init__(self, sa_connection: _SAConnection, meta: Connection, engine: Engine) -> None:
        self._sa_conn = sa_connection
        self._meta = meta
        self._engine = engine

    @property
    def name(self) -> str:
        return self._meta.name

    @property
    def type(self) -> str:
        return self._meta.type

    @property
    def database(self) -> str:
        return self._meta.database

    def query(self, sql: str, params: dict[str, Any] | None = None) -> pd.DataFrame:
        """Ejecuta una SELECT y devuelve un DataFrame.

        Usa parametros con sintaxis `:nombre` (estandar SQLAlchemy):

            df = db.query("SELECT * FROM ps_product WHERE id = :pid", {"pid": 42})
        """
        return pd.read_sql(text(sql), self._sa_conn, params=params)

    def tables(self) -> list[str]:
        """Lista las tablas del schema configurado (o el default si no hay)."""
        return inspect(self._engine).get_table_names(schema=self._meta.db_schema)

    def columns(self, table: str) -> list[dict[str, Any]]:
        """Metadatos de columnas de una tabla: nombre, tipo, nullable, default, etc."""
        return inspect(self._engine).get_columns(table, schema=self._meta.db_schema)

    def raw(self) -> _SAConnection:
        """Acceso a la conexion SQLAlchemy subyacente para casos avanzados."""
        return self._sa_conn

    def __repr__(self) -> str:
        return f"<Database name={self.name!r} type={self.type!r} db={self.database!r}>"


@contextmanager
def connect(name: str, *, interactive: bool = True) -> Iterator[Database]:
    """Abre una conexion a la BD logica `name` y la cierra al salir del with.

    El Engine se crea y se desecha por bloque — pensado para scripts y notebooks.
    Para apps de larga vida (FastAPI etc.) que reutilizan conexiones, usar
    `make_engine()` directamente y gestionar el ciclo de vida manualmente.
    """
    meta = get_connection(name)
    engine = make_engine(meta, interactive=interactive)
    sa_conn = engine.connect()
    try:
        yield Database(sa_conn, meta, engine)
    finally:
        sa_conn.close()
        engine.dispose()
