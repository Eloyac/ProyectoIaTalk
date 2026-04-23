import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _make_claude_response(json_str: str) -> MagicMock:
    resp = MagicMock()
    resp.content = [MagicMock(text=json_str)]
    return resp


@pytest.mark.asyncio
async def test_collecting_phase_updates_state():
    """Claude extrae nombre/comunidad/teléfono; el estado se actualiza."""
    claude_json = (
        '{"reply":"Gracias Juan. ¿Cuál es el motivo de su llamada?",'
        '"name":"Juan García","community":"Los Pinos","phone":"612111111",'
        '"block":null,"urgency":null,"issue":null}'
    )
    with (
        patch("src.agent.call_handler._client") as mock_cl,
        patch("src.agent.call_handler.detect_anger", new=AsyncMock(return_value="low")),
    ):
        mock_cl.messages.create = AsyncMock(return_value=_make_claude_response(claude_json))

        from src.agent.call_handler import handle_turn, clear_session
        clear_session("test-sid-1")
        result = await handle_turn("test-sid-1", "Hola, soy Juan García, llamo de Los Pinos, mi teléfono es 612111111")

    assert "Gracias Juan" in result.reply
    assert result.action is None


@pytest.mark.asyncio
async def test_confirming_phase_on_complete_data():
    """Cuando Claude devuelve todos los datos, el agente pide confirmación."""
    claude_json = (
        '{"reply":"Entendido.",'
        '"name":"Ana López","community":"Residencial Norte","phone":"699000000",'
        '"block":"A","urgency":"urgent","issue":"Agua en el portal"}'
    )
    with (
        patch("src.agent.call_handler._client") as mock_cl,
        patch("src.agent.call_handler.detect_anger", new=AsyncMock(return_value="low")),
    ):
        mock_cl.messages.create = AsyncMock(return_value=_make_claude_response(claude_json))

        from src.agent.call_handler import handle_turn, clear_session
        clear_session("test-sid-2")
        result = await handle_turn("test-sid-2", "Ana López, Residencial Norte, 699000000, avería de agua urgente")

    # Debe pedir confirmación
    assert "correcto" in result.reply.lower() or "confirma" in result.reply.lower()


@pytest.mark.asyncio
async def test_anger_high_triggers_transfer_immediately():
    """Enfado high provoca endSession independientemente del bloque."""
    claude_json = '{"reply":"ok","name":null,"community":null,"phone":null,"block":null,"urgency":null,"issue":null}'
    with (
        patch("src.agent.call_handler._client") as mock_cl,
        patch("src.agent.call_handler.detect_anger", new=AsyncMock(return_value="high")),
    ):
        mock_cl.messages.create = AsyncMock(return_value=_make_claude_response(claude_json))

        from src.agent.call_handler import handle_turn, clear_session
        clear_session("test-sid-3")
        result = await handle_turn("test-sid-3", "esto es un escándalo, exijo hablar ya")

    assert result.action is not None
    assert result.action["type"] == "endSession"


@pytest.mark.asyncio
async def test_confirmation_yes_executes_action():
    """Confirmar datos en fase 'confirming' ejecuta la acción."""
    from src.agent.call_handler import handle_turn, clear_session, _sessions, CallState

    # Inyectar estado ya en confirming
    state = CallState(
        call_sid="test-sid-4",
        phase="confirming",
        name="Pedro Ruiz",
        community="Torre Azul",
        phone="644000000",
        block="C",
        urgency="normal",
    )
    _sessions["test-sid-4"] = state

    with patch("src.agent.call_handler.detect_anger", new=AsyncMock(return_value="low")):
        result = await handle_turn("test-sid-4", "sí, correcto")

    # Bloque C → type="note", no hay endSession
    assert result.action is None
    assert result.reply


@pytest.mark.asyncio
async def test_confirmation_no_resets_to_collecting():
    """Negar confirmación vuelve a la fase de recogida de datos."""
    from src.agent.call_handler import handle_turn, clear_session, _sessions, CallState

    state = CallState(
        call_sid="test-sid-5",
        phase="confirming",
        name="Luis Marta",
        community="Portal 3",
        phone="655000000",
        block="A",
    )
    _sessions["test-sid-5"] = state

    with patch("src.agent.call_handler.detect_anger", new=AsyncMock(return_value="low")):
        result = await handle_turn("test-sid-5", "no, me he equivocado")

    assert state.phase == "collecting"
    assert state.block == ""


@pytest.mark.asyncio
async def test_clear_session_removes_state():
    from src.agent.call_handler import clear_session, _sessions, CallState
    _sessions["x"] = CallState(call_sid="x")
    clear_session("x")
    assert "x" not in _sessions
