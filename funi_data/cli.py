"""CLI de funi-dataDB.

Uso:
    python -m funi_data <comando> [args]

Comandos:
    list                       Listar conexiones definidas y estado de credenciales.
    setup    <connection>      Configurar credenciales (wizard interactivo).
    check    <connection>      Verificar que hay credenciales guardadas.
    delete   <connection>      Borrar credenciales del vault.
    help                       Mostrar esta ayuda.
"""
from __future__ import annotations

import sys

from .connections import CONFIG_PATH, get_connection, load_connections
from .credentials import (
    delete_credentials,
    get_credentials,
    prompt_and_store,
)


def cmd_list(_: list[str]) -> int:
    try:
        conns = load_connections()
    except FileNotFoundError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1
    if not conns:
        print(f"(no hay conexiones definidas en {CONFIG_PATH})")
        return 0
    print(f"Conexiones definidas en {CONFIG_PATH}:")
    name_w = max(len(c) for c in conns)
    for c in conns.values():
        flag = "[OK]" if get_credentials(c.name) else "[--]"
        print(f"  {flag}  {c.name:<{name_w}}  {c.type}://{c.host}:{c.port}/{c.database}")
    print("\nLeyenda: [OK] credenciales guardadas | [--] faltan (ejecuta `setup <nombre>`).")
    return 0


def cmd_setup(args: list[str]) -> int:
    if not args:
        print("Uso: python -m funi_data setup <connection>", file=sys.stderr)
        return 2
    name = args[0]
    try:
        conn = get_connection(name)
    except (FileNotFoundError, KeyError) as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1
    print(f"Configurando credenciales para:")
    print(f"  {conn.name}  ({conn.type}://{conn.host}:{conn.port}/{conn.database})")
    if conn.description:
        print(f"  {conn.description}")
    prompt_and_store(name)
    return 0


def cmd_check(args: list[str]) -> int:
    if not args:
        print("Uso: python -m funi_data check <connection>", file=sys.stderr)
        return 2
    name = args[0]
    try:
        get_connection(name)
    except (FileNotFoundError, KeyError) as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1
    creds = get_credentials(name)
    if creds:
        user, _ = creds
        print(f"[OK] Credenciales presentes para '{name}' (usuario: {user})")
        return 0
    print(
        f"[FALTA] No hay credenciales para '{name}'. "
        f"Ejecuta: python -m funi_data setup {name}",
        file=sys.stderr,
    )
    return 1


def cmd_delete(args: list[str]) -> int:
    if not args:
        print("Uso: python -m funi_data delete <connection>", file=sys.stderr)
        return 2
    name = args[0]
    delete_credentials(name)
    print(f"Credenciales de '{name}' eliminadas (si existían).")
    return 0


def cmd_help(_: list[str]) -> int:
    print(__doc__)
    return 0


COMMANDS = {
    "list": cmd_list,
    "setup": cmd_setup,
    "check": cmd_check,
    "delete": cmd_delete,
    "help": cmd_help,
    "-h": cmd_help,
    "--help": cmd_help,
}


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        return cmd_help([])
    cmd, *rest = argv
    handler = COMMANDS.get(cmd)
    if handler is None:
        print(f"[ERROR] Comando desconocido: {cmd}\n", file=sys.stderr)
        cmd_help([])
        return 2
    return handler(rest)


if __name__ == "__main__":
    sys.exit(main())
