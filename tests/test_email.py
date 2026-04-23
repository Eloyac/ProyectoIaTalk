import pytest
from unittest.mock import MagicMock, patch


@pytest.mark.asyncio
async def test_send_email_success():
    mock_smtp = MagicMock()
    mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
    mock_smtp.__exit__ = MagicMock(return_value=False)

    with patch("src.notifications.email.smtplib.SMTP", return_value=mock_smtp):
        from src.notifications.email import send_email
        result = await send_email(
            to="monica@despacho.com",
            subject="Avería en Comunidad Los Pinos",
            body="Vecino Juan García notifica avería en portal.",
        )

    assert result is True
    mock_smtp.starttls.assert_called_once()
    mock_smtp.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_send_email_smtp_error_returns_false():
    mock_smtp = MagicMock()
    mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
    mock_smtp.__exit__ = MagicMock(return_value=False)
    mock_smtp.starttls.side_effect = Exception("SMTP connection failed")

    with patch("src.notifications.email.smtplib.SMTP", return_value=mock_smtp):
        from src.notifications.email import send_email
        result = await send_email("monica@despacho.com", "Asunto", "Cuerpo")

    assert result is False


@pytest.mark.asyncio
async def test_send_email_sets_correct_headers():
    captured = {}
    mock_smtp = MagicMock()
    mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
    mock_smtp.__exit__ = MagicMock(return_value=False)

    def capture_send(msg):
        captured["subject"] = msg["Subject"]
        captured["to"] = msg["To"]

    mock_smtp.send_message.side_effect = capture_send

    with patch("src.notifications.email.smtplib.SMTP", return_value=mock_smtp):
        from src.notifications.email import send_email
        await send_email("monica@despacho.com", "Avería urgente", "Descripción")

    assert captured["subject"] == "Avería urgente"
    assert captured["to"] == "monica@despacho.com"
