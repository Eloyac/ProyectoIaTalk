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
