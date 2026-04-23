# Agente IA Fincas — Plan A: Foundation + Voice Integration

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Levantar el servidor Python, conectarlo a Twilio ConversationRelay y conseguir que una llamada real entre, el agente salude y responda con eco de voz.

**Architecture:** FastAPI recibe el webhook de Twilio en `/incoming-call` y devuelve TwiML con `<ConversationRelay>`. Twilio gestiona STT (Deepgram) y TTS (ElevenLabs) internamente. El servidor recibe texto por WebSocket y devuelve texto. SQLite guarda el registro de llamada. Railway hostea el servidor.

**Tech Stack:** Python 3.12 · FastAPI · uvicorn · pydantic-settings · twilio SDK · pytest · Railway

---

## File Map

| Archivo | Responsabilidad |
|---|---|
| `requirements.txt` | Dependencias del proyecto |
| `.env.example` | Plantilla de configuración (sin secretos) |
| `config/settings.py` | Carga `.env` con pydantic-settings |
| `src/main.py` | App FastAPI, startup, rutas |
| `src/storage/models.py` | Dataclass `CallRecord` |
| `src/storage/db.py` | `init_db()`, `save_call()` con SQLite |
| `src/agent/schedule_checker.py` | `is_office_hours(dt?)` |
| `src/voice/twilio_handler.py` | `/incoming-call`, `/ws`, `/call-ended` |
| `tests/test_schedule_checker.py` | Tests de lógica horaria |
| `tests/test_db.py` | Tests de SQLite |
| `tests/conftest.py` | Fixture de .env para tests |
| `railway.toml` | Configuración Railway deploy |
| `pytest.ini` | Configuración pytest |

---

## Task 1: Estructura del proyecto y dependencias

**Files:**
- Create: `requirements.txt`
- Create: `pytest.ini`
- Create: `railway.toml`
- Create: `.gitignore`

- [ ] **Step 1: Crear `requirements.txt`**

```
fastapi==0.115.6
uvicorn[standard]==0.32.1
python-dotenv==1.0.1
pydantic-settings==2.6.1
twilio==9.3.7
anthropic==0.40.0
httpx==0.28.1
pytest==8.3.4
pytest-asyncio==0.24.0
httpx==0.28.1
```

- [ ] **Step 2: Crear `pytest.ini`**

```ini
[pytest]
testpaths = tests
asyncio_mode = auto
```

- [ ] **Step 3: Crear `railway.toml`**

```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "uvicorn src.main:app --host 0.0.0.0 --port $PORT"
restartPolicyType = "ON_FAILURE"
```

- [ ] **Step 4: Crear `.gitignore`**

```
.env
data/
__pycache__/
*.pyc
.pytest_cache/
```

- [ ] **Step 5: Instalar dependencias y verificar**

```bash
pip install -r requirements.txt
python -c "import fastapi, twilio, anthropic; print('OK')"
```
Esperado: `OK`

- [ ] **Step 6: Commit**

```bash
git init
git add requirements.txt pytest.ini railway.toml .gitignore
git commit -m "feat: bootstrap project structure"
```

---

## Task 2: Configuración con pydantic-settings

**Files:**
- Create: `config/__init__.py`
- Create: `config/settings.py`
- Create: `.env.example`

- [ ] **Step 1: Crear `config/__init__.py`** (vacío)

- [ ] **Step 2: Crear `config/settings.py`**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""

    # Operadores
    monica_phone: str = ""
    concha_phone: str = ""
    luis_phone: str = ""
    operator_priority: str = "monica,luis,concha"

    # Notificaciones
    monica_whatsapp: str = ""
    luis_whatsapp: str = ""
    monica_email: str = ""
    concha_email: str = ""
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_host: str = "smtp.office365.com"
    smtp_port: int = 587

    # Horario L-V 9-14h / 16-19h
    office_hours_start: str = "09:00"
    office_hours_mid_end: str = "14:00"
    office_hours_mid_start: str = "16:00"
    office_hours_end: str = "19:00"
    office_days: str = "0,1,2,3,4"

    # Club — fechas periodo de socio
    club_membership_start: str = "2025-09-01"
    club_membership_end: str = "2025-09-30"

    # IA
    anthropic_api_key: str = ""
    deepgram_api_key: str = ""
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""

    # WhatsApp (Green API)
    green_api_base_url: str = "https://api.green-api.com"
    green_api_instance: str = ""
    green_api_token: str = ""

    # Despacho
    office_name: str = "Administración de Fincas"

    # Palabras clave de enfado (separadas por coma)
    anger_keywords: str = (
        "inaceptable,escándalo,denuncia,vergüenza,exijo,"
        "inmediatamente,ridículo,incompetentes,mala gestión,legal"
    )

    model_config = {"env_file": ".env", "case_sensitive": False}


settings = Settings()
```

- [ ] **Step 3: Crear `.env.example`**

```env
# Twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+34xxxxxxxxx

# Operadores del despacho
MONICA_PHONE=+34xxxxxxxxx
CONCHA_PHONE=+34xxxxxxxxx
LUIS_PHONE=+34xxxxxxxxx
OPERATOR_PRIORITY=monica,luis,concha

# WhatsApp (números sin +)
MONICA_WHATSAPP=+34xxxxxxxxx
LUIS_WHATSAPP=+34xxxxxxxxx

# Email
MONICA_EMAIL=monica@despacho.com
CONCHA_EMAIL=concha@despacho.com
SMTP_USER=correo@outlook.com
SMTP_PASSWORD=your_password
SMTP_HOST=smtp.office365.com
SMTP_PORT=587

# Horario de oficina
OFFICE_HOURS_START=09:00
OFFICE_HOURS_MID_END=14:00
OFFICE_HOURS_MID_START=16:00
OFFICE_HOURS_END=19:00
OFFICE_DAYS=0,1,2,3,4

# Club — actualizar cada temporada
CLUB_MEMBERSHIP_START=2025-09-01
CLUB_MEMBERSHIP_END=2025-09-30

# IA
ANTHROPIC_API_KEY=sk-ant-xxxx
DEEPGRAM_API_KEY=xxxx
ELEVENLABS_API_KEY=xxxx
ELEVENLABS_VOICE_ID=xxxx

# Green API (WhatsApp)
GREEN_API_INSTANCE=1234567890
GREEN_API_TOKEN=xxxx

# Despacho
OFFICE_NAME=Administración de Fincas García
ANGER_KEYWORDS=inaceptable,escándalo,denuncia,vergüenza,exijo,inmediatamente,ridículo,incompetentes
```

- [ ] **Step 4: Crear `.env` copiando `.env.example`** (sin commits de este archivo)

```bash
cp .env.example .env
```

- [ ] **Step 5: Verificar que settings carga sin errores**

```bash
python -c "from config.settings import settings; print(settings.office_name)"
```
Esperado: `Administración de Fincas`

- [ ] **Step 6: Commit**

```bash
git add config/ .env.example
git commit -m "feat: add pydantic-settings config"
```

---

## Task 3: FastAPI app con health check

**Files:**
- Create: `src/__init__.py`
- Create: `src/main.py`

- [ ] **Step 1: Crear `src/__init__.py`** (vacío)

- [ ] **Step 2: Escribir test primero** — `tests/__init__.py` (vacío) y `tests/test_health.py`

```python
# tests/test_health.py
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_health_returns_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
```

- [ ] **Step 3: Verificar que el test falla**

```bash
pytest tests/test_health.py -v
```
Esperado: FAILED — `ModuleNotFoundError: No module named 'src.main'`

- [ ] **Step 4: Crear `src/main.py`**

```python
from fastapi import FastAPI

app = FastAPI(title="Agente IA Fincas")


@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 5: Verificar que el test pasa**

```bash
pytest tests/test_health.py -v
```
Esperado: PASSED

- [ ] **Step 6: Commit**

```bash
git add src/ tests/
git commit -m "feat: add FastAPI app with health check"
```

---

## Task 4: SQLite — modelos y base de datos

**Files:**
- Create: `src/storage/__init__.py`
- Create: `src/storage/models.py`
- Create: `src/storage/db.py`
- Create: `tests/test_db.py`

- [ ] **Step 1: Crear `src/storage/__init__.py`** (vacío)

- [ ] **Step 2: Crear `src/storage/models.py`**

```python
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CallRecord:
    call_sid: str
    caller_name: str = ""
    community: str = ""
    phone: str = ""
    block: str = ""           # A, B, C, D
    resolution: str = ""      # "transfer", "email_sent", "whatsapp_sent", "note_taken"
    anger_level: str = "low"  # low, medium, high
    created_at: datetime = field(default_factory=datetime.now)
```

- [ ] **Step 3: Escribir tests** — `tests/test_db.py`

```python
import sqlite3
from pathlib import Path
import pytest
import src.storage.db as db_module
from src.storage.models import CallRecord

TEST_DB = Path("/tmp/test_calls_fincas.db")


@pytest.fixture(autouse=True)
def clean_db(tmp_path, monkeypatch):
    db_path = tmp_path / "calls.db"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    db_module.init_db()
    yield
    db_path.unlink(missing_ok=True)


def test_init_creates_call_records_table():
    with sqlite3.connect(db_module.DB_PATH) as conn:
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()]
    assert "call_records" in tables


def test_save_call_persists_all_fields():
    record = CallRecord(
        call_sid="CA123abc",
        caller_name="Ana López",
        community="Comunidad Las Rosas 4",
        phone="612345678",
        block="A",
        resolution="email_sent",
        anger_level="low",
    )
    db_module.save_call(record)

    with sqlite3.connect(db_module.DB_PATH) as conn:
        row = conn.execute(
            "SELECT caller_name, community, block FROM call_records WHERE call_sid=?",
            ("CA123abc",),
        ).fetchone()
    assert row == ("Ana López", "Comunidad Las Rosas 4", "A")


def test_save_call_with_defaults():
    db_module.save_call(CallRecord(call_sid="CA_minimal"))
    with sqlite3.connect(db_module.DB_PATH) as conn:
        count = conn.execute("SELECT COUNT(*) FROM call_records").fetchone()[0]
    assert count == 1
```

- [ ] **Step 4: Verificar que los tests fallan**

```bash
pytest tests/test_db.py -v
```
Esperado: FAILED — `No module named 'src.storage.db'`

- [ ] **Step 5: Crear `src/storage/db.py`**

```python
import sqlite3
from pathlib import Path
from .models import CallRecord

DB_PATH = Path("data/calls.db")


def init_db() -> None:
    DB_PATH.parent.mkdir(exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS call_records (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                call_sid     TEXT    NOT NULL,
                caller_name  TEXT    DEFAULT '',
                community    TEXT    DEFAULT '',
                phone        TEXT    DEFAULT '',
                block        TEXT    DEFAULT '',
                resolution   TEXT    DEFAULT '',
                anger_level  TEXT    DEFAULT 'low',
                created_at   TEXT    NOT NULL
            )
        """)


def save_call(record: CallRecord) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """INSERT INTO call_records
               (call_sid, caller_name, community, phone, block, resolution, anger_level, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                record.call_sid, record.caller_name, record.community,
                record.phone, record.block, record.resolution,
                record.anger_level, record.created_at.isoformat(),
            ),
        )
```

- [ ] **Step 6: Verificar que los tests pasan**

```bash
pytest tests/test_db.py -v
```
Esperado: 3 PASSED

- [ ] **Step 7: Conectar `init_db` al startup de FastAPI** — editar `src/main.py`

```python
from fastapi import FastAPI
from src.storage.db import init_db

app = FastAPI(title="Agente IA Fincas")


@app.on_event("startup")
async def startup():
    init_db()


@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 8: Verificar todos los tests pasan**

```bash
pytest -v
```
Esperado: 4 PASSED

- [ ] **Step 9: Commit**

```bash
git add src/storage/ tests/test_db.py src/main.py
git commit -m "feat: add SQLite storage with CallRecord model"
```

---

## Task 5: Comprobador de horario de oficina

**Files:**
- Create: `src/agent/__init__.py`
- Create: `src/agent/schedule_checker.py`
- Create: `tests/test_schedule_checker.py`

- [ ] **Step 1: Crear `src/agent/__init__.py`** (vacío)

- [ ] **Step 2: Escribir tests** — `tests/test_schedule_checker.py`

```python
from datetime import datetime, timedelta
import pytest
from src.agent.schedule_checker import is_office_hours


def _dt(weekday: int, hour: int, minute: int = 0) -> datetime:
    """Crea datetime con día de semana y hora dados. 0=lunes."""
    base = datetime(2024, 1, 1)  # Lunes
    offset = (weekday - base.weekday()) % 7
    return (base + timedelta(days=offset)).replace(hour=hour, minute=minute, second=0)


def test_monday_morning_is_office_hours():
    assert is_office_hours(_dt(0, 10)) is True


def test_monday_afternoon_is_office_hours():
    assert is_office_hours(_dt(0, 17)) is True


def test_midday_gap_is_not_office_hours():
    assert is_office_hours(_dt(0, 15)) is False


def test_before_morning_is_not_office_hours():
    assert is_office_hours(_dt(0, 8, 59)) is False


def test_after_closing_is_not_office_hours():
    assert is_office_hours(_dt(0, 19, 1)) is False


def test_saturday_is_not_office_hours():
    assert is_office_hours(_dt(5, 10)) is False


def test_sunday_is_not_office_hours():
    assert is_office_hours(_dt(6, 10)) is False


def test_friday_afternoon_is_office_hours():
    assert is_office_hours(_dt(4, 17)) is True
```

- [ ] **Step 3: Verificar que los tests fallan**

```bash
pytest tests/test_schedule_checker.py -v
```
Esperado: FAILED — `ModuleNotFoundError`

- [ ] **Step 4: Crear `src/agent/schedule_checker.py`**

```python
from datetime import datetime, time as dtime
from config.settings import settings


def is_office_hours(now: datetime | None = None) -> bool:
    """Devuelve True si `now` cae dentro del horario L-V 9-14h / 16-19h."""
    if now is None:
        now = datetime.now()

    office_days = [int(d) for d in settings.office_days.split(",")]
    if now.weekday() not in office_days:
        return False

    current = now.time()
    start = _t(settings.office_hours_start)
    mid_end = _t(settings.office_hours_mid_end)
    mid_start = _t(settings.office_hours_mid_start)
    end = _t(settings.office_hours_end)

    return (start <= current <= mid_end) or (mid_start <= current <= end)


def _t(hhmm: str) -> dtime:
    h, m = hhmm.split(":")
    return dtime(int(h), int(m))
```

- [ ] **Step 5: Verificar que los tests pasan**

```bash
pytest tests/test_schedule_checker.py -v
```
Esperado: 8 PASSED

- [ ] **Step 6: Ejecutar todos los tests**

```bash
pytest -v
```
Esperado: 12 PASSED

- [ ] **Step 7: Commit**

```bash
git add src/agent/ tests/test_schedule_checker.py
git commit -m "feat: add schedule checker with office hours logic"
```

---

## Task 6: Twilio ConversationRelay — webhook y WebSocket básico

**Files:**
- Create: `src/voice/__init__.py`
- Create: `src/voice/twilio_handler.py`
- Create: `tests/test_twilio_handler.py`
- Modify: `src/main.py` — registrar router

**Nota arquitectónica:** ConversationRelay gestiona STT/TTS internamente (Deepgram + ElevenLabs como providers). El servidor solo maneja texto. Mucho más simple que Media Streams raw.

- [ ] **Step 1: Crear `src/voice/__init__.py`** (vacío)

- [ ] **Step 2: Escribir tests** — `tests/test_twilio_handler.py`

```python
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_incoming_call_returns_twiml():
    resp = client.post("/incoming-call")
    assert resp.status_code == 200
    assert "text/xml" in resp.headers["content-type"]
    assert "<ConversationRelay" in resp.text
    assert 'language="es-ES"' in resp.text


def test_call_ended_returns_empty_twiml():
    resp = client.post("/call-ended")
    assert resp.status_code == 200
    assert "<Response" in resp.text
```

- [ ] **Step 3: Verificar que los tests fallan**

```bash
pytest tests/test_twilio_handler.py -v
```
Esperado: FAILED — rutas no existen

- [ ] **Step 4: Crear `src/voice/twilio_handler.py`**

```python
import json
from fastapi import APIRouter, Request, Response, WebSocket
from config.settings import settings

router = APIRouter()


@router.post("/incoming-call")
async def incoming_call(request: Request):
    base = str(request.base_url).rstrip("/")
    ws_base = base.replace("https://", "wss://").replace("http://", "ws://")

    twiml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<Response>\n"
        f'  <Connect action="{base}/call-ended">\n'
        "    <ConversationRelay\n"
        f'      url="{ws_base}/ws"\n'
        f'      welcomeGreeting="Hola, bienvenido a {settings.office_name}. '
        "Para ayudarle, dígame su nombre y apellidos, "
        'el nombre de su comunidad o edificio, y un teléfono de contacto."\n'
        '      language="es-ES"\n'
        '      ttsProvider="ElevenLabs"\n'
        '      transcriptionProvider="Deepgram"\n'
        '      interruptible="any"\n'
        "    />\n"
        "  </Connect>\n"
        "</Response>"
    )
    return Response(twiml, media_type="text/xml")


@router.post("/call-ended")
async def call_ended():
    return Response('<?xml version="1.0" encoding="UTF-8"?><Response/>', media_type="text/xml")


@router.websocket("/ws")
async def websocket_handler(websocket: WebSocket):
    await websocket.accept()
    session: dict = {}

    async for raw in websocket.iter_text():
        msg = json.loads(raw)

        if msg["type"] == "setup":
            session["call_sid"] = msg.get("callSid", "unknown")

        elif msg["type"] == "prompt":
            user_text = msg.get("voicePrompt", "")
            reply = await _handle_turn(session, user_text)
            await websocket.send_text(json.dumps({
                "type": "text",
                "token": reply,
                "last": True,
            }))


async def _handle_turn(session: dict, user_text: str) -> str:
    # Placeholder — reemplazado por call_handler en Plan B
    return "Le he escuchado. En breve le atendemos. ¿Puede repetirme su nombre, comunidad y teléfono?"
```

- [ ] **Step 5: Registrar el router en `src/main.py`**

```python
from fastapi import FastAPI
from src.storage.db import init_db
from src.voice.twilio_handler import router as twilio_router

app = FastAPI(title="Agente IA Fincas")


@app.on_event("startup")
async def startup():
    init_db()


@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(twilio_router)
```

- [ ] **Step 6: Verificar que los tests pasan**

```bash
pytest -v
```
Esperado: 14 PASSED

- [ ] **Step 7: Commit**

```bash
git add src/voice/ tests/test_twilio_handler.py src/main.py
git commit -m "feat: add Twilio ConversationRelay webhook and WebSocket handler"
```

---

## Task 7: Despliegue en Railway

**Files:**
- Create: `Procfile` (alternativa a railway.toml si falla)

- [ ] **Step 1: Crear repo en GitHub y subir el código**

```bash
git remote add origin https://github.com/TU_USUARIO/ProyectoIaTalk.git
git push -u origin main
```

- [ ] **Step 2: Crear proyecto en Railway**

1. Ir a [railway.app](https://railway.app)
2. New Project → Deploy from GitHub repo → seleccionar `ProyectoIaTalk`
3. Railway detecta `railway.toml` automáticamente

- [ ] **Step 3: Añadir variables de entorno en Railway**

En Railway → Variables → añadir como mínimo:
```
TWILIO_ACCOUNT_SID=ACxxx
TWILIO_AUTH_TOKEN=xxx
TWILIO_PHONE_NUMBER=+34xxx
OFFICE_NAME=Administración de Fincas García
ANTHROPIC_API_KEY=sk-ant-xxx
```
Las demás quedan vacías por ahora — el servidor arranca igual.

- [ ] **Step 4: Verificar que el servidor arranca**

```bash
curl https://TU-APP.railway.app/health
```
Esperado: `{"status":"ok"}`

- [ ] **Step 5: Configurar webhook en Twilio Console**

1. Twilio Console → Phone Numbers → el número VoIP
2. Voice Configuration → Webhook: `https://TU-APP.railway.app/incoming-call`
3. Method: HTTP POST

- [ ] **Step 6: Configurar desvío de llamada en el móvil 6xx**

En el móvil que no se usa: activar desvío de todas las llamadas al número Twilio.
- iOS: Ajustes → Teléfono → Desvío de llamadas
- Android: Teléfono → Menú → Ajustes → Más ajustes → Desvío de llamadas

- [ ] **Step 7: Prueba end-to-end**

Llamar al móvil 6xx desde otro teléfono.
Esperado: El agente contesta con el saludo en español y responde "Le he escuchado..."

- [ ] **Step 8: Commit final del Plan A**

```bash
git add .
git commit -m "feat: complete Plan A — foundation and voice integration deployed"
```

---

## Verificación del Plan A

Ejecutar antes de marcar el Plan A como completo:

```bash
# Todos los tests pasan localmente
pytest -v

# Servidor arranca correctamente
uvicorn src.main:app --reload &
curl http://localhost:8000/health

# TwiML tiene la estructura correcta
curl -X POST http://localhost:8000/incoming-call | grep ConversationRelay
```

**Prueba manual:**
1. Llamar al número del despacho (o al Twilio directamente)
2. El agente contesta con el saludo
3. El vecino dice algo
4. El agente responde "Le he escuchado..."
5. Aparece el log en Railway con el call_sid

---

## Siguiente: Plan B

Una vez completado este Plan A (servidor desplegado, llamadas entrando), continuar con:
`docs/superpowers/plans/2026-04-21-plan-B-agent-brain.md`

Plan B implementa:
- Árbol de decisiones A/B/C/D con Claude Haiku
- Detector de enfado
- Recogida de datos del llamante
- Notificaciones: WhatsApp, email, transferencias
