"""Registro de motores de BD soportados.

Para anadir un motor nuevo:
1. Anadir entrada a DRIVERS con el dialecto+driver de SQLAlchemy.
2. Anadir entrada a CONNECT_ARGS si necesita argumentos especificos.
3. Anadir el driver Python como extra opcional en pyproject.toml.
4. Probar con un test de integracion en tests/test_integration_<motor>.py.
"""
from __future__ import annotations

from typing import Any, Final

# Mapping Connection.type -> SQLAlchemy dialect+driver string.
# Solo los motores listados aqui son ejecutables; el resto lanza NotImplementedError.
DRIVERS: Final[dict[str, str]] = {
    "mysql": "mysql+pymysql",
    "postgresql": "postgresql+psycopg",
    "vertica": "vertica+vertica_python",
}

# Argumentos pasados a sqlalchemy.create_engine(connect_args=...)
CONNECT_ARGS: Final[dict[str, dict[str, Any]]] = {
    "mysql": {"charset": "utf8mb4"},
}


def is_supported(db_type: str) -> bool:
    return db_type in DRIVERS
