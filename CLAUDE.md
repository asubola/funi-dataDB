# funi-dataDB

Librería personal Python para conexiones transversales a bases de datos. Permite que cualquier proyecto del usuario use `from funi_data import connect` sin reconfigurar credenciales por proyecto.

## Propósito
Centralizar el acceso a MySQL/PostgreSQL/Vertica/etc. con un único modelo de credenciales (Windows Credential Manager) y una API unificada por encima de SQLAlchemy.

## Stack
- Python 3.11+
- `keyring` → Windows Credential Manager (DPAPI)
- `pyyaml` + `pydantic` → metadatos de conexión
- `SQLAlchemy 2.x` → abstracción de motores (Fase 2+)
- `pymysql` / `psycopg` / `sqlalchemy-vertica-python` → drivers (extras opcionales)
- `pandas` → DataFrames de query (Fase 2+)
- `pytest` → tests

## Estructura
```
funi-dataDB/
├── pyproject.toml
├── CLAUDE.md
├── .gitignore
├── connections.yaml.example     # plantilla a copiar a ~/.funidelia/
├── funi_data/
│   ├── __init__.py
│   ├── __main__.py              # python -m funi_data
│   ├── cli.py                   # comandos setup/list/check/delete
│   ├── connections.py           # carga y valida ~/.funidelia/connections.yaml
│   ├── credentials.py           # keyring wrapper + setup wizard
│   ├── engine.py                # (Fase 2) factory SQLAlchemy
│   ├── client.py                # (Fase 2) connect() context manager
│   └── connectors/              # (Fase 2/3) drivers por motor
└── tests/
```

## Modelo de seguridad
- **Credenciales:** Windows Credential Manager bajo namespace `funi-dataDB/<connection_name>` (claves separadas `_user` y `_password`).
- **Metadatos no sensibles:** `~/.funidelia/connections.yaml` (host, port, database, schema, descripción).
- **Usuarios de BD:** se recomienda read-only por proyecto.
- **Setup wizard:** si falta credencial al ejecutar `ensure_credentials()`, prompt CLI (`getpass`) y guarda en vault.
- **No portable:** DPAPI cifra con clave del usuario+máquina. Cada máquina/usuario requiere su propio setup. **Nunca** embeber credenciales en .exe (PyInstaller no cifra el bytecode).

## Uso desde otros proyectos

```bash
# instalar como dependencia editable
pip install -e C:/Users/eanzu/projects/funi-dataDB
```

```python
from funi_data import connect, ensure_credentials

ensure_credentials("mysql-funidelia")           # lanza wizard si falta
with connect("mysql-funidelia") as db:          # (Fase 2)
    df = db.query("SELECT * FROM ventas LIMIT 10")
```

## Cómo añadir una conexión nueva
1. Editar `~/.funidelia/connections.yaml` con metadatos (host, port, db, type).
2. `python -m funi_data setup <nombre>` → introduce usuario y contraseña.
3. `python -m funi_data check <nombre>` para verificar.
4. Usar desde código.

## Comandos CLI
```bash
python -m funi_data list                        # listar conexiones y estado de credenciales
python -m funi_data setup <connection>          # configurar credenciales (prompt seguro)
python -m funi_data check <connection>          # verificar que hay credenciales guardadas
python -m funi_data delete <connection>         # borrar credenciales del vault
```

## Tests
```bash
pip install -e ".[dev]"
pytest
```

## Roadmap
- **Fase 1 (en curso):** credenciales + CLI + smoke test MySQL.
- **Fase 2:** SQLAlchemy + `connect()` + integración en Purchase Tool.
- **Fase 3:** conectores PostgreSQL y Vertica.

## Reglas para Claude
- Mantener este `CLAUDE.md` actualizado cuando se añadan módulos o cambien decisiones estructurales.
- DRY: el patrón de añadir un motor nuevo debe vivir en una sola plantilla; cada `connectors/<motor>.py` debe ser ~30 líneas.
- No commitear sin que el usuario lo pida explícitamente.
- No embeber secretos en el código bajo ninguna circunstancia.
