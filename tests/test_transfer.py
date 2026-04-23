import json
from src.notifications.transfer import build_end_session


def test_build_end_session_type():
    msg = build_end_session("+34612345678")
    assert msg["type"] == "endSession"


def test_build_end_session_handoff_data():
    msg = build_end_session("+34612345678", reason="transfer_operator")
    data = json.loads(msg["handoffData"])
    assert data["transferTo"] == "+34612345678"
    assert data["reason"] == "transfer_operator"


def test_build_end_session_with_fallback():
    msg = build_end_session(
        "+34699000001",
        reason="transfer_concha",
        fallback_email_to="concha@despacho.com",
        fallback_email_subject="Consulta club",
        fallback_email_body="Vecino esperando respuesta.",
    )
    data = json.loads(msg["handoffData"])
    assert data["fallbackEmailTo"] == "concha@despacho.com"
    assert data["fallbackEmailSubject"] == "Consulta club"


def test_build_end_session_default_reason():
    msg = build_end_session("+34600000000")
    data = json.loads(msg["handoffData"])
    assert data["reason"] == ""
