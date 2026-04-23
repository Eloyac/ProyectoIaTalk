import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_send_whatsapp_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200

    with patch("src.notifications.whatsapp.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        from src.notifications.whatsapp import send_whatsapp
        result = await send_whatsapp("612345678", "Hola, mensaje de prueba")

    assert result is True
    mock_client.post.assert_called_once()
    call_kwargs = mock_client.post.call_args
    payload = call_kwargs.kwargs["json"]
    assert payload["chatId"] == "34612345678@c.us"
    assert payload["message"] == "Hola, mensaje de prueba"


@pytest.mark.asyncio
async def test_send_whatsapp_normalizes_phone_with_prefix():
    mock_resp = MagicMock()
    mock_resp.status_code = 200

    with patch("src.notifications.whatsapp.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        from src.notifications.whatsapp import send_whatsapp
        result = await send_whatsapp("+34612345678", "mensaje")

    payload = mock_client.post.call_args.kwargs["json"]
    assert payload["chatId"] == "34612345678@c.us"
    assert result is True


@pytest.mark.asyncio
async def test_send_whatsapp_failure_returns_false():
    mock_resp = MagicMock()
    mock_resp.status_code = 403

    with patch("src.notifications.whatsapp.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        from src.notifications.whatsapp import send_whatsapp
        result = await send_whatsapp("612345678", "mensaje")

    assert result is False
