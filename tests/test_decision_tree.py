import pytest


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    monkeypatch.setenv("MONICA_PHONE", "+34600000001")
    monkeypatch.setenv("CONCHA_PHONE", "+34600000002")
    monkeypatch.setenv("LUIS_PHONE", "+34600000003")
    monkeypatch.setenv("MONICA_WHATSAPP", "+34600000001")
    monkeypatch.setenv("LUIS_WHATSAPP", "+34600000003")
    monkeypatch.setenv("MONICA_EMAIL", "monica@despacho.com")
    monkeypatch.setenv("CONCHA_EMAIL", "concha@despacho.com")
    monkeypatch.setenv("OPERATOR_PRIORITY", "monica,luis,concha")
    monkeypatch.setenv("CLUB_MEMBERSHIP_START", "2025-09-01")
    monkeypatch.setenv("CLUB_MEMBERSHIP_END", "2025-09-30")


def _call(block, urgency="normal", is_office=True, anger="low"):
    from src.agent.decision_tree import decide
    return decide(block, urgency, is_office, anger, "Juan García", "Los Pinos", "612111111", "avería en portal")


# ── Bloque A ──────────────────────────────────────────────────────────────────

def test_block_a_urgent_in_hours_transfers():
    action = _call("A", urgency="urgent", is_office=True)
    assert action.type == "transfer"
    assert "+34600000001" in action.transfer_to  # Mónica primero


def test_block_a_urgent_out_hours_whatsapp():
    action = _call("A", urgency="urgent", is_office=False)
    assert action.type == "whatsapp_urgent"
    assert "+34600000001" in action.notify_phones
    assert "+34600000003" in action.notify_phones
    assert "URGENTE" in action.notify_message


def test_block_a_normal_sends_email():
    action = _call("A", urgency="normal")
    assert action.type == "email_normal"
    assert "monica@despacho.com" in action.notify_to


# ── Bloque B ──────────────────────────────────────────────────────────────────

def test_block_b_dates_query_returns_dates():
    from src.agent.decision_tree import decide
    action = decide("B", "", True, "low", "María", "Club Norte", "699000000", "cuándo son las fechas de socio")
    assert action.type == "dates"
    assert "2025" in action.caller_reply


def test_block_b_other_transfers_to_concha():
    from src.agent.decision_tree import decide
    action = decide("B", "", True, "low", "Pedro", "Club Sur", "699000000", "quiero apuntarme")
    assert action.type == "transfer"
    assert "+34600000002" in action.transfer_to
    assert action.fallback_email_to == "concha@despacho.com"


# ── Bloque C ──────────────────────────────────────────────────────────────────

def test_block_c_takes_note():
    action = _call("C")
    assert action.type == "note"
    assert action.caller_reply  # tiene texto de cierre


# ── Bloque D ──────────────────────────────────────────────────────────────────

def test_block_d_normal_returns_busy():
    action = _call("D", anger="low")
    assert action.type == "busy"


def test_block_d_angry_transfers():
    action = _call("D", anger="high")
    assert action.type == "transfer"
    assert action.transfer_to  # tiene al menos un número


# ── Enfado override ───────────────────────────────────────────────────────────

def test_anger_high_overrides_block_c():
    action = _call("C", anger="high")
    assert action.type == "transfer"


def test_anger_high_overrides_block_b_normal():
    action = _call("B", anger="high")
    assert action.type == "transfer"
