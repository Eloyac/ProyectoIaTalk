import json


def build_end_session(
    transfer_to: str,
    reason: str = "",
    fallback_email_to: str = "",
    fallback_email_subject: str = "",
    fallback_email_body: str = "",
) -> dict:
    """
    Construye el mensaje endSession para ConversationRelay.
    Twilio lo envía al endpoint /action cuando la sesión termina.
    """
    return {
        "type": "endSession",
        "handoffData": json.dumps({
            "transferTo": transfer_to,
            "reason": reason,
            "fallbackEmailTo": fallback_email_to,
            "fallbackEmailSubject": fallback_email_subject,
            "fallbackEmailBody": fallback_email_body,
        }),
    }
