import json
from anthropic import AsyncAnthropic
from config.settings import settings

_client = AsyncAnthropic(api_key=settings.anthropic_api_key)


def _has_anger_keyword(text: str) -> bool:
    keywords = [k.strip().lower() for k in settings.anger_keywords.split(",")]
    lower = text.lower()
    return any(k in lower for k in keywords if k)


async def detect_anger(text: str, history: list[dict]) -> str:
    """
    Returns 'low', 'medium', or 'high'.
    Fast path: keyword hit → 'high' without API call.
    Slow path: Claude Haiku evaluates the conversation.
    """
    if _has_anger_keyword(text):
        return "high"

    messages = [*history, {"role": "user", "content": text}]
    resp = await _client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=30,
        system=(
            "Evalúa el nivel de enfado del interlocutor en la conversación. "
            'Responde SOLO con JSON válido: {"anger_level": "low"} '
            'o {"anger_level": "medium"} o {"anger_level": "high"}.'
        ),
        messages=messages,
    )
    try:
        data = json.loads(resp.content[0].text.strip())
        level = data.get("anger_level", "low")
        return level if level in ("low", "medium", "high") else "low"
    except (json.JSONDecodeError, IndexError, KeyError):
        return "low"
