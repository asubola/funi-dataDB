"""Factory de SQLAlchemy Engine a partir de una Connection + credenciales.

Esto vive separado de `client.py` para que el patron sea facil de extender:
- Anadir un motor = anadir entrada a `connectors.DRIVERS` y CONNECT_ARGS.
- No es necesario tocar este modulo salvo para casos especiales.
"""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import URL

from .connections import Connection, get_connection
from .connectors import CONNECT_ARGS, DRIVERS
from .credentials import ensure_credentials


def make_engine(name_or_conn: str | Connection, *, interactive: bool = True) -> Engine:
    """Construye un Engine de SQLAlchemy listo para conectar.

    - `name_or_conn`: nombre logico (string) o instancia ya cargada de Connection.
    - `interactive`: si True (default) y faltan credenciales, lanza el wizard.
                     Si False, lanza LookupError sin pedir nada (util en CI/scripts no tty).

    El Engine se crea con `pool_pre_ping=True` para detectar conexiones obsoletas
    tras reinicios de servidor o pausas largas.
    """
    conn = get_connection(name_or_conn) if isinstance(name_or_conn, str) else name_or_conn

    if conn.type not in DRIVERS:
        supported = ", ".join(sorted(DRIVERS)) or "(ninguno)"
        raise NotImplementedError(
            f"Motor '{conn.type}' no soportado todavia. Soportados: {supported}. "
            f"Anade entrada a funi_data/connectors/__init__.py."
        )

    user, password = ensure_credentials(conn.name, interactive=interactive)

    url = URL.create(
        drivername=DRIVERS[conn.type],
        username=user,
        password=password,
        host=conn.host,
        port=conn.port,
        database=conn.database,
    )

    return create_engine(
        url,
        connect_args=CONNECT_ARGS.get(conn.type, {}),
        pool_pre_ping=True,
        future=True,
    )
