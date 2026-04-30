"""Carga y validación de metadatos de conexión desde ~/.funidelia/connections.yaml.

Este módulo NO toca credenciales — solo metadatos no sensibles (host, port, db, etc.).
Ver `credentials.py` para el almacén de usuario/contraseña.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

CONFIG_PATH: Path = Path.home() / ".funidelia" / "connections.yaml"

DBType = Literal["mysql", "postgresql", "vertica"]


class Connection(BaseModel):
    """Metadatos de una conexión a base de datos.

    El campo `schema` es opcional — algunos motores (PostgreSQL, Vertica)
    distinguen schema de database; MySQL no.
    """

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    name: str = Field(min_length=1, description="Identificador lógico (e.g. 'mysql-funidelia')")
    type: DBType
    host: str = Field(min_length=1)
    port: int = Field(gt=0, lt=65536)
    database: str = Field(min_length=1)
    db_schema: str | None = Field(default=None, alias="schema")
    description: str | None = None


class ConnectionsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    connections: list[Connection]


def load_connections(path: Path | None = None) -> dict[str, Connection]:
    """Devuelve dict {name: Connection}. Lanza FileNotFoundError si no existe el yaml."""
    target = path or CONFIG_PATH
    if not target.exists():
        raise FileNotFoundError(
            f"No existe {target}. Copia 'connections.yaml.example' del repo a esa "
            "ruta y edítalo con tus conexiones."
        )
    with target.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    cfg = ConnectionsConfig.model_validate(raw)
    by_name: dict[str, Connection] = {}
    for c in cfg.connections:
        if c.name in by_name:
            raise ValueError(f"Conexión duplicada en {target}: '{c.name}'")
        by_name[c.name] = c
    return by_name


def get_connection(name: str, path: Path | None = None) -> Connection:
    conns = load_connections(path)
    if name not in conns:
        available = ", ".join(sorted(conns.keys())) or "(ninguna)"
        raise KeyError(
            f"Conexión '{name}' no encontrada en {path or CONFIG_PATH}. "
            f"Disponibles: {available}"
        )
    return conns[name]
