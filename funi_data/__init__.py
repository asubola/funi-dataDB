"""funi-dataDB — capa de datos transversal para los proyectos de eanzuola.

Fase 1: gestión de credenciales y metadatos de conexión.
Fase 2: SQLAlchemy + connect() context manager.
Fase 3: conectores PostgreSQL y Vertica.
"""
from __future__ import annotations

__version__ = "0.1.0"

from .connections import (
    Connection,
    ConnectionsConfig,
    CONFIG_PATH,
    load_connections,
    get_connection,
)
from .credentials import (
    SERVICE_NAMESPACE,
    ensure_credentials,
    get_credentials,
    set_credentials,
    delete_credentials,
    prompt_and_store,
)

__all__ = [
    "__version__",
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
