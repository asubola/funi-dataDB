"""funi-dataDB — capa de datos transversal para los proyectos de eanzuola.

API publica principal:

    from funi_data import connect

    with connect("PS-slave") as db:
        df = db.query("SELECT * FROM ps_product LIMIT 10")
"""
from __future__ import annotations

__version__ = "0.2.0"

from .client import Database, connect
from .connections import (
    CONFIG_PATH,
    Connection,
    ConnectionsConfig,
    get_connection,
    load_connections,
)
from .credentials import (
    SERVICE_NAMESPACE,
    delete_credentials,
    ensure_credentials,
    get_credentials,
    prompt_and_store,
    set_credentials,
)
from .engine import make_engine

__all__ = [
    "__version__",
    # client (API principal)
    "connect",
    "Database",
    # engine (avanzado)
    "make_engine",
    # connections
    "Connection",
    "ConnectionsConfig",
    "CONFIG_PATH",
    "load_connections",
    "get_connection",
    # credentials
    "SERVICE_NAMESPACE",
    "ensure_credentials",
    "get_credentials",
    "set_credentials",
    "delete_credentials",
    "prompt_and_store",
]
