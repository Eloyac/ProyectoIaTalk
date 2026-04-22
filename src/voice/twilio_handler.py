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
    return Response(
        '<?xml version="1.0" encoding="UTF-8"?><Response/>',
        media_type="text/xml",
    )


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
    # Placeholder — replaced by call_handler in Plan B
    return (
        "Le he escuchado. En breve le atendemos. "
        "¿Puede repetirme su nombre, comunidad y teléfono?"
    )
