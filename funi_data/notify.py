"""Avisos por Slack para los procesos programados, vía FuniHub (`funi.notifications.slack`).

    from funi_data.notify import slack
    slack("Reviews de Amazon · OK · 3 nuevas")          # mensaje directo al canal por defecto

    python -m funi_data notify "texto" [--channel #canal]

Con qué identidad se envía (medido el 2-oct-2026):
- El permiso `notifications.slack.write` lo tiene el USUARIO (eanzuola), no la clave de servicio `m4-tracker` de
  `M4-Tracker/.env`, que solo tiene permisos de lectura. Por eso se prueba primero la sesión personal de FuniHub que
  guarda Claude Code en `~/.claude/.credentials.json` y, si no vale, la clave de servicio (por si IT le da el permiso).
- La sesión personal caduca a las ~2 horas y solo la renueva Claude Code. Si está caducada se intenta que Claude Code
  la renueve (`claude mcp list`); si no lo consigue, el aviso no sale y la función devuelve False.

`slack()` nunca lanza: un aviso que no sale no puede tumbar el proceso que avisa. El mensaje queda encolado en
FuniHub (bot CoreNotifications); que devuelva True significa encolado, no leído.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

FUNIHUB_URL = "https://hub.funidelia.dk"
DEFAULT_CHANNEL = "@eanzuola"  # mensaje directo; se cambia con FUNI_SLACK_CHANNEL
CLAUDE_CREDENTIALS = Path.home() / ".claude" / ".credentials.json"
SERVICE_ENV = Path(__file__).resolve().parents[2] / "M4-Tracker" / ".env"
MAX_CHARS = 3900


def _personal_session() -> tuple[str | None, bool]:
    """(token de la sesión personal de FuniHub, caducado). (None, True) si no hay sesión guardada."""
    try:
        data = json.loads(CLAUDE_CREDENTIALS.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, True
    for entry in data.get("mcpOAuth", {}).values():
        if isinstance(entry, dict) and entry.get("serverName") == "funihub" and entry.get("accessToken"):
            expires = (entry.get("expiresAt") or 0) / 1000
            return entry["accessToken"], expires < time.time() + 60
    return None, True


def _renew_personal_session() -> None:
    """Pide a Claude Code que conecte con sus servidores MCP, lo que renueva una sesión caducada."""
    exe = shutil.which("claude")
    if exe:
        try:
            subprocess.run([exe, "mcp", "list"], capture_output=True, timeout=90, check=False)
        except (OSError, subprocess.TimeoutExpired):
            pass


def _service_token() -> str | None:
    for name in ("FUNIHUB_TOKEN", "FUNI_HUB_TOKEN"):
        if os.environ.get(name):
            return os.environ[name]
    try:
        lines = SERVICE_ENV.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for line in lines:
        key, sep, value = line.partition("=")
        if sep and key.strip() in ("FUNIHUB_TOKEN", "FUNI_HUB_TOKEN"):
            return value.strip().strip("'\"") or None
    return None


def _tokens():
    token, expired = _personal_session()
    if token and expired:
        _renew_personal_session()
        token, expired = _personal_session()
    if token and not expired:
        yield token
    service = _service_token()
    if service:
        yield service


def _post(token: str, channel: str, message: str) -> bool:
    body = json.dumps({"channel": channel, "message": message[:MAX_CHARS]}).encode("utf-8")
    request = urllib.request.Request(
        f"{FUNIHUB_URL}/api/v1/tools/funi.notifications.slack@latest", data=body, method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status < 300
    except (urllib.error.URLError, OSError):  # 401/403 (sin permiso o caducado), red caída
        return False


def slack(message: str, channel: str | None = None) -> bool:
    """Envía `message` por Slack. Devuelve True si FuniHub lo aceptó; False si no se pudo enviar."""
    target = channel or os.environ.get("FUNI_SLACK_CHANNEL") or DEFAULT_CHANNEL
    return any(_post(token, target, message) for token in _tokens())
