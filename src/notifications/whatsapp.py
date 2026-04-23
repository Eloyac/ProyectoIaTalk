import httpx
from config.settings import settings


async def send_whatsapp(phone: str, message: str) -> bool:
    """
    Envía WhatsApp vía Green API.
    phone: número español con o sin +34 (ej: '612345678' o '+34612345678').
    """
    digits = phone.lstrip("+")
    if not digits.startswith("34"):
        digits = f"34{digits}"
    chat_id = f"{digits}@c.us"

    url = (
        f"{settings.green_api_base_url}"
        f"/waInstance{settings.green_api_instance}"
        f"/sendMessage/{settings.green_api_token}"
    )
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(url, json={"chatId": chat_id, "message": message})
    return resp.status_code == 200
