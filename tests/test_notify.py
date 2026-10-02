"""`notify.slack`: orden de identidades y que nunca lanza. Sin red: `_post` y las fuentes de token se sustituyen."""
from __future__ import annotations

import json
import time

from funi_data import notify


def _credentials(tmp_path, monkeypatch, expires_in: float):
    path = tmp_path / "credentials.json"
    path.write_text(json.dumps({"mcpOAuth": {"funihub|x": {
        "serverName": "funihub", "accessToken": "personal", "expiresAt": (time.time() + expires_in) * 1000}}}))
    monkeypatch.setattr(notify, "CLAUDE_CREDENTIALS", path)


def test_usa_la_sesion_personal_si_esta_vigente(tmp_path, monkeypatch):
    _credentials(tmp_path, monkeypatch, 3600)
    monkeypatch.setattr(notify, "_service_token", lambda: "servicio")
    calls = []
    monkeypatch.setattr(notify, "_post", lambda token, channel, message: calls.append((token, channel)) or True)
    assert notify.slack("hola") is True
    assert calls == [("personal", notify.DEFAULT_CHANNEL)]


def test_sesion_caducada_intenta_renovar_y_cae_a_la_clave_de_servicio(tmp_path, monkeypatch):
    _credentials(tmp_path, monkeypatch, -10)
    renewals = []
    monkeypatch.setattr(notify, "_renew_personal_session", lambda: renewals.append(1))
    monkeypatch.setattr(notify, "_service_token", lambda: "servicio")
    calls = []
    monkeypatch.setattr(notify, "_post", lambda token, channel, message: calls.append(token) or True)
    assert notify.slack("hola", "#canal") is True
    assert renewals == [1] and calls == ["servicio"]


def test_sin_permiso_en_ninguna_identidad_devuelve_false(tmp_path, monkeypatch):
    _credentials(tmp_path, monkeypatch, 3600)
    monkeypatch.setattr(notify, "_service_token", lambda: "servicio")
    calls = []
    monkeypatch.setattr(notify, "_post", lambda token, channel, message: calls.append(token) and False)
    assert notify.slack("hola") is False
    assert calls == ["personal", "servicio"]


def test_sin_credenciales_no_lanza(tmp_path, monkeypatch):
    monkeypatch.setattr(notify, "CLAUDE_CREDENTIALS", tmp_path / "no-existe.json")
    monkeypatch.setattr(notify, "_service_token", lambda: None)
    assert notify.slack("hola") is False


def test_canal_por_variable_de_entorno(tmp_path, monkeypatch):
    _credentials(tmp_path, monkeypatch, 3600)
    monkeypatch.setattr(notify, "_service_token", lambda: None)
    monkeypatch.setenv("FUNI_SLACK_CHANNEL", "#avisos")
    calls = []
    monkeypatch.setattr(notify, "_post", lambda token, channel, message: calls.append(channel) or True)
    notify.slack("hola")
    assert calls == ["#avisos"]
