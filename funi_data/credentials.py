"""Gestión de credenciales contra Windows Credential Manager vía `keyring`.

Diseño:
- Cada conexión almacena dos entradas en el vault, bajo el mismo "service":
    service = f"funi-dataDB/{connection_name}"
    keyring.set_password(service, "_user",     <usuario>)
    keyring.set_password(service, "_password", <contraseña>)
- Esto permite recuperar usuario y contraseña de forma independiente y borrar
  ambos atómicamente.
- En Windows, `keyring` resuelve a `WinVaultKeyring` (DPAPI). Las credenciales
  quedan cifradas con la clave del usuario+máquina y NO son portables.
"""
from __future__ import annotations

import getpass
import sys

import keyring
import keyring.errors

SERVICE_NAMESPACE = "funi-dataDB"

_USER_KEY = "_user"
_PASS_KEY = "_password"


def _service(connection_name: str) -> str:
    if not connection_name:
        raise ValueError("connection_name no puede estar vacío")
    return f"{SERVICE_NAMESPACE}/{connection_name}"


def get_credentials(connection_name: str) -> tuple[str, str] | None:
    """Devuelve (usuario, contraseña) o None si no están guardadas."""
    service = _service(connection_name)
    user = keyring.get_password(service, _USER_KEY)
    password = keyring.get_password(service, _PASS_KEY)
    if user and password:
        return user, password
    return None


def set_credentials(connection_name: str, user: str, password: str) -> None:
    """Guarda usuario y contraseña en el vault. Sobrescribe si ya existían."""
    if not user:
        raise ValueError("usuario no puede estar vacío")
    if not password:
        raise ValueError("contraseña no puede estar vacía")
    service = _service(connection_name)
    keyring.set_password(service, _USER_KEY, user)
    keyring.set_password(service, _PASS_KEY, password)


def delete_credentials(connection_name: str) -> None:
    """Borra usuario y contraseña del vault. No falla si no existían."""
    service = _service(connection_name)
    for key in (_USER_KEY, _PASS_KEY):
        try:
            keyring.delete_password(service, key)
        except keyring.errors.PasswordDeleteError:
            pass


def ensure_credentials(connection_name: str, *, interactive: bool = True) -> tuple[str, str]:
    """Devuelve (usuario, contraseña). Si no existen, lanza el wizard si `interactive=True`.

    En código de aplicación, llamar al inicio para garantizar que la conexión
    podrá hacerse sin pedir input en mitad del proceso.
    """
    creds = get_credentials(connection_name)
    if creds is not None:
        return creds
    if not interactive:
        raise LookupError(
            f"No hay credenciales para '{connection_name}' y interactive=False. "
            f"Ejecuta: python -m funi_data setup {connection_name}"
        )
    return prompt_and_store(connection_name)


def prompt_and_store(connection_name: str) -> tuple[str, str]:
    """Lanza el wizard CLI: prompt de usuario + contraseña y guarda en vault."""
    print(f"\n[funi-dataDB] Configurar credenciales para '{connection_name}'", file=sys.stderr)
    print(f"             (se guardarán en Windows Credential Manager)", file=sys.stderr)
    user = input("  Usuario: ").strip()
    if not user:
        raise ValueError("Usuario vacío, abortando.")
    password = getpass.getpass("  Contraseña: ")
    if not password:
        raise ValueError("Contraseña vacía, abortando.")
    set_credentials(connection_name, user, password)
    print(
        f"[funi-dataDB] OK. Guardadas en namespace '{_service(connection_name)}'.",
        file=sys.stderr,
    )
    return user, password
