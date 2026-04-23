import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    monkeypatch.setenv("ANGER_KEYWORDS", "inaceptable,escándalo,denuncia")


def test_keyword_returns_high_without_claude():
    """Keyword match nunca llama a Claude."""
    with patch("src.agent.anger_detector._client") as mock_client:
        import asyncio
        # Reimport to pick up patched _client
        import importlib
        import src.agent.anger_detector as mod
        importlib.reload(mod)
        level = asyncio.get_event_loop().run_until_complete(
            mod.detect_anger("esto es inaceptable", [])
        )
        mock_client.messages.create.assert_not_called()
    assert level == "high"


@pytest.mark.asyncio
async def test_no_keyword_calls_claude_and_returns_level():
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='{"anger_level": "medium"}')]

    with patch("src.agent.anger_detector._client") as mock_client:
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        from src.agent.anger_detector import detect_anger
        level = await detect_anger("cuándo me llaman", [])

    assert level == "medium"


@pytest.mark.asyncio
async def test_claude_malformed_json_returns_low():
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="no es json")]

    with patch("src.agent.anger_detector._client") as mock_client:
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        from src.agent.anger_detector import detect_anger
        level = await detect_anger("quiero información", [])

    assert level == "low"


@pytest.mark.asyncio
async def test_claude_unknown_level_returns_low():
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='{"anger_level": "furious"}')]

    with patch("src.agent.anger_detector._client") as mock_client:
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        from src.agent.anger_detector import detect_anger
        level = await detect_anger("quiero información", [])

    assert level == "low"
