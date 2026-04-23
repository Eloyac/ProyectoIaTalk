import json
import logging
from dataclasses import dataclass, field
from anthropic import AsyncAnthropic
from config.settings import settings
from src.agent.anger_detector import detect_anger
from src.agent.decision_tree import decide, CallAction
from src.agent.schedule_checker import is_office_hours

logger = logging.getLogger(__name__)

_client = AsyncAnthropic(api_key=settings.anthropic_api_key)

_SYSTEM = (
    f"Eres el agente de voz de {settings.office_name}, un despacho de administración de fincas. "
    "Atiendes llamadas en español de forma cordial y natural. "
    "Recoge: nombre y apellidos, nombre de la comunidad o edificio, y teléfono de contacto. "
    "Clasifica el motivo: A=Avería técnica, B=Consulta sobre el Club, "
    "C=Gestión de comunidad (no avería), D=Quiere hablar con el administrador. "
    "Para averías, determina si es urgente (peligro inmediato, corte agua/luz, inundación) o normal. "
    "Responde SIEMPRE con JSON válido y nada más."
)

_JSON_SCHEMA = (
    '{"reply":"respuesta natural en español",'
    '"name":"nombre extraído o null",'
    '"community":"comunidad extraída o null",'
    '"phone":"teléfono extraído o null",'
    '"block":"A|B|C|D o null",'
    '"urgency":"urgent|normal o null",'
    '"issue":"resumen breve del problema o null"}'
)

_sessions: dict[str, "CallState"] = {}


@dataclass
class CallState:
    call_sid: str
    phase: str = "collecting"   # collecting | confirming | done
    name: str = ""
    community: str = ""
    phone: str = ""
    issue: str = ""
    block: str = ""
    urgency: str = ""
    anger_level: str = "low"
    history: list[dict] = field(default_factory=list)


@dataclass
class TurnResult:
    reply: str
    action: dict | None = None  # None = solo texto; dict = endSession/whatsapp/email


async def handle_turn(call_sid: str, user_text: str) -> TurnResult:
    state = _sessions.setdefault(call_sid, CallState(call_sid=call_sid))

    if state.phase == "done":
        return TurnResult(reply="")

    state.anger_level = await detect_anger(user_text, state.history)
    state.history.append({"role": "user", "content": user_text})

    if state.anger_level == "high":
        action = decide(
            state.block or "A", "urgent", is_office_hours(), "high",
            state.name, state.community, state.phone, user_text,
        )
        state.phase = "done"
        return _to_result(action)

    if state.phase == "collecting":
        return await _collecting_turn(state)
    if state.phase == "confirming":
        return _confirming_turn(state, user_text)

    return TurnResult(reply="Un momento, por favor.")


async def _collecting_turn(state: CallState) -> TurnResult:
    extracted = await _ask_claude(state)

    if extracted.get("name"):
        state.name = extracted["name"]
    if extracted.get("community"):
        state.community = extracted["community"]
    if extracted.get("phone"):
        state.phone = extracted["phone"]
    if extracted.get("block"):
        state.block = extracted["block"]
    if extracted.get("urgency"):
        state.urgency = extracted["urgency"]
    if extracted.get("issue"):
        state.issue = extracted["issue"]

    reply = extracted.get("reply") or "¿Puede repetirme su nombre, comunidad y teléfono?"
    state.history.append({"role": "assistant", "content": reply})

    if state.name and state.community and state.phone and state.block:
        confirm = _build_confirm(state)
        state.phase = "confirming"
        state.history.append({"role": "assistant", "content": confirm})
        return TurnResult(reply=confirm)

    return TurnResult(reply=reply)


def _confirming_turn(state: CallState, user_text: str) -> TurnResult:
    lower = user_text.lower()
    yes_words = ["sí", "si", "correcto", "exacto", "efectivamente", "eso es", "afirmativo"]
    no_words = ["no", "incorrecto", "mal", "error", "equivocado", "negativo"]

    if any(w in lower for w in yes_words):
        action = decide(
            state.block, state.urgency, is_office_hours(), state.anger_level,
            state.name, state.community, state.phone, state.issue,
        )
        state.phase = "done"
        return _to_result(action)

    if any(w in lower for w in no_words):
        state.phase = "collecting"
        state.block = ""
        reply = "Disculpe, volvamos a empezar. ¿Puede repetirme su nombre, comunidad y teléfono?"
        state.history.append({"role": "assistant", "content": reply})
        return TurnResult(reply=reply)

    reply = "¿Puede confirmar con un 'sí' o 'no' si los datos que he leído son correctos?"
    return TurnResult(reply=reply)


def _to_result(action: CallAction) -> TurnResult:
    from src.notifications.transfer import build_end_session

    if action.type == "transfer":
        phone = action.transfer_to[0] if action.transfer_to else ""
        end_session = build_end_session(
            phone,
            reason=action.type,
            fallback_email_to=action.fallback_email_to,
            fallback_email_subject=action.fallback_email_subject,
            fallback_email_body=action.fallback_email_body,
        )
        return TurnResult(reply=action.caller_reply, action=end_session)

    if action.type == "whatsapp_urgent":
        return TurnResult(
            reply=action.caller_reply,
            action={
                "type": "whatsapp",
                "phones": action.notify_phones,
                "message": action.notify_message,
            },
        )

    if action.type == "email_normal":
        return TurnResult(
            reply=action.caller_reply,
            action={
                "type": "email",
                "to": action.notify_to,
                "subject": "Incidencia registrada",
                "body": action.notify_message,
            },
        )

    return TurnResult(reply=action.caller_reply)


def _build_confirm(state: CallState) -> str:
    desc = {
        "A": "una avería",
        "B": "una consulta sobre el club",
        "C": "una gestión de comunidad",
        "D": "hablar con el administrador",
    }.get(state.block, "una consulta")
    return (
        f"Entonces, {state.name}, tiene {desc} en {state.community} "
        f"y le contactamos al {state.phone}. ¿Es correcto?"
    )


async def _ask_claude(state: CallState) -> dict:
    transcript = "\n".join(
        f"{'Vecino' if m['role'] == 'user' else 'Agente'}: {m['content']}"
        for m in state.history
    )
    known = (
        f"Nombre: {state.name or '(pendiente)'}\n"
        f"Comunidad: {state.community or '(pendiente)'}\n"
        f"Teléfono: {state.phone or '(pendiente)'}\n"
        f"Bloque: {state.block or '(pendiente)'}"
    )
    prompt = (
        f"TRANSCRIPCIÓN:\n{transcript}\n\n"
        f"DATOS RECOGIDOS HASTA AHORA:\n{known}\n\n"
        f"Responde SOLO con este JSON:\n{_JSON_SCHEMA}"
    )
    resp = await _client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=250,
        system=_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    try:
        text = resp.content[0].text.strip()
        start = text.find("{")
        end = text.rfind("}") + 1
        return json.loads(text[start:end]) if start >= 0 else {}
    except (json.JSONDecodeError, IndexError):
        return {"reply": "¿Puede repetirme su nombre, comunidad y teléfono?"}


def clear_session(call_sid: str) -> None:
    _sessions.pop(call_sid, None)
