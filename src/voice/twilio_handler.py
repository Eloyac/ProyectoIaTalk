import json
import logging
from fastapi import APIRouter, Request, Response, WebSocket
from config.settings import settings
from src.agent.call_handler import handle_turn, clear_session
from src.notifications.email import send_email

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/incoming-call")
async def incoming_call(request: Request):
    base = str(request.base_url).rstrip("/")
    ws_base = base.replace("https://", "wss://").replace("http://", "ws://")
    twiml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<Response>\n"
        f'  <Connect action="{base}/action">\n'
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


@router.post("/action")
async def action(request: Request):
    """Twilio llama aquí cuando ConversationRelay termina. Ejecuta la transferencia si hay HandoffData."""
    form = await request.form()
    handoff_raw = form.get("HandoffData", "{}")
    try:
        handoff = json.loads(handoff_raw)
    except (json.JSONDecodeError, TypeError):
        handoff = {}

    transfer_to = handoff.get("transferTo", "")
    base = str(request.base_url).rstrip("/")

    if transfer_to:
        twiml = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            "<Response>\n"
            f'  <Dial timeout="20" action="{base}/dial-fallback">\n'
            f"    <Number>{transfer_to}</Number>\n"
            "  </Dial>\n"
            "</Response>"
        )
    else:
        twiml = '<?xml version="1.0" encoding="UTF-8"?><Response/>'

    return Response(twiml, media_type="text/xml")


@router.post("/dial-fallback")
async def dial_fallback(request: Request):
    """Twilio llama aquí si el Dial falla (no contesta, ocupado, timeout)."""
    form = await request.form()
    handoff_raw = form.get("HandoffData", "{}")
    try:
        handoff = json.loads(handoff_raw)
    except (json.JSONDecodeError, TypeError):
        handoff = {}

    fallback_to = handoff.get("fallbackEmailTo", "")
    if fallback_to:
        await send_email(
            to=fallback_to,
            subject=handoff.get("fallbackEmailSubject", "Llamada sin atender"),
            body=handoff.get("fallbackEmailBody", ""),
        )
        logger.info("dial_fallback: email enviado a %s", fallback_to)

    twiml = '<?xml version="1.0" encoding="UTF-8"?><Response/>'
    return Response(twiml, media_type="text/xml")


@router.websocket("/ws")
async def websocket_handler(websocket: WebSocket):
    await websocket.accept()
    call_sid = "unknown"

    try:
        async for raw in websocket.iter_text():
            msg = json.loads(raw)

            if msg["type"] == "setup":
                call_sid = msg.get("callSid", "unknown")
                logger.info("call_started call_sid=%s", call_sid)

            elif msg["type"] == "prompt":
                user_text = msg.get("voicePrompt", "")
                result = await handle_turn(call_sid, user_text)

                await websocket.send_text(
                    json.dumps({"type": "text", "token": result.reply, "last": True})
                )

                if result.action:
                    await websocket.send_text(json.dumps(result.action))

                    if result.action.get("type") == "whatsapp":
                        from src.notifications.whatsapp import send_whatsapp
                        for phone in result.action.get("phones", []):
                            await send_whatsapp(phone, result.action.get("message", ""))
                        logger.info("whatsapp_sent call_sid=%s", call_sid)

                    elif result.action.get("type") == "email":
                        await send_email(
                            to=result.action["to"],
                            subject=result.action["subject"],
                            body=result.action["body"],
                        )
                        logger.info("email_sent call_sid=%s to=%s", call_sid, result.action["to"])

    except Exception as exc:
        logger.error("ws_error call_sid=%s error=%s", call_sid, exc)
    finally:
        clear_session(call_sid)
        logger.info("call_ended call_sid=%s", call_sid)
