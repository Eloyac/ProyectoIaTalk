from fastapi.testclient import TestClient
from src.main import app
import pytest

client = TestClient(app)


def test_incoming_call_returns_twiml():
    resp = client.post("/incoming-call")
    assert resp.status_code == 200
    assert "text/xml" in resp.headers["content-type"]
    assert "<ConversationRelay" in resp.text
    assert 'language="es-ES"' in resp.text


def test_action_endpoint_returns_empty_twiml():
    # /call-ended was renamed to /action; with no HandoffData it returns empty Response
    resp = client.post("/action")
    assert resp.status_code == 200
    assert "<Response" in resp.text


# ── Tests nuevos Task 14 ──────────────────────────────────────────────────────

import json as _json
from unittest.mock import AsyncMock as _AsyncMock, MagicMock as _MagicMock, patch as _patch


@pytest.mark.asyncio
async def test_action_endpoint_dials_transfer_number(client):
    handoff = _json.dumps({
        "transferTo": "+34600000001",
        "reason": "transfer_operator",
        "fallbackEmailTo": "",
        "fallbackEmailSubject": "",
        "fallbackEmailBody": "",
    })
    resp = await client.post(
        "/action",
        data={"HandoffData": handoff},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200
    assert b"Dial" in resp.content
    assert b"+34600000001" in resp.content


@pytest.mark.asyncio
async def test_action_endpoint_no_handoff_returns_hangup(client):
    resp = await client.post(
        "/action",
        data={},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200
    assert b"Response" in resp.content


@pytest.mark.asyncio
async def test_dial_fallback_sends_email_and_closes(client):
    handoff = _json.dumps({
        "transferTo": "+34600000002",
        "fallbackEmailTo": "concha@despacho.com",
        "fallbackEmailSubject": "Consulta club",
        "fallbackEmailBody": "Vecino esperando.",
    })
    with _patch("src.voice.twilio_handler.send_email", new=_AsyncMock(return_value=True)):
        resp = await client.post(
            "/dial-fallback",
            data={"HandoffData": handoff, "DialCallStatus": "no-answer"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    assert resp.status_code == 200
    assert b"Response" in resp.content


@pytest.mark.asyncio
async def test_websocket_calls_handle_turn(client):
    turn_result_mock = _MagicMock()
    turn_result_mock.reply = "Hola, le escucho."
    turn_result_mock.action = None

    with _patch("src.voice.twilio_handler.handle_turn", new=_AsyncMock(return_value=turn_result_mock)):
        async with client.websocket_connect("/ws") as ws:
            await ws.send_text(_json.dumps({"type": "setup", "callSid": "CA123"}))
            await ws.send_text(_json.dumps({"type": "prompt", "voicePrompt": "Hola"}))
            raw = await ws.receive_text()
            msg = _json.loads(raw)

    assert msg["type"] == "text"
    assert msg["token"] == "Hola, le escucho."
    assert msg["last"] is True


@pytest.mark.asyncio
async def test_websocket_action_endSession_forwarded(client):
    end_session = {"type": "endSession", "handoffData": '{"transferTo":"+34600000001"}'}
    turn_result_mock = _MagicMock()
    turn_result_mock.reply = "Le paso ahora."
    turn_result_mock.action = end_session

    with _patch("src.voice.twilio_handler.handle_turn", new=_AsyncMock(return_value=turn_result_mock)):
        async with client.websocket_connect("/ws") as ws:
            await ws.send_text(_json.dumps({"type": "setup", "callSid": "CA456"}))
            await ws.send_text(_json.dumps({"type": "prompt", "voicePrompt": "exijo hablar ya"}))
            raw1 = await ws.receive_text()
            msg1 = _json.loads(raw1)
            raw2 = await ws.receive_text()
            msg2 = _json.loads(raw2)

    assert msg1["type"] == "text"
    assert msg2["type"] == "endSession"
