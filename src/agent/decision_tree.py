from dataclasses import dataclass, field
from datetime import datetime
from config.settings import settings


@dataclass
class CallAction:
    type: str                          # transfer | whatsapp_urgent | email_normal | dates | note | busy
    transfer_to: list[str] = field(default_factory=list)
    notify_phones: list[str] = field(default_factory=list)
    notify_to: str = ""
    notify_message: str = ""
    caller_reply: str = ""
    fallback_email_to: str = ""
    fallback_email_subject: str = ""
    fallback_email_body: str = ""


def decide(
    block: str,
    urgency: str,
    is_office: bool,
    anger_level: str,
    caller_name: str,
    community: str,
    phone: str,
    issue: str,
) -> CallAction:
    if anger_level == "high":
        return CallAction(
            type="transfer",
            transfer_to=_operator_phones(),
            caller_reply=(
                "Entiendo su preocupación. Déjeme transferirle con uno de nuestros "
                "gestores ahora mismo para que le atiendan personalmente."
            ),
        )

    if block == "A":
        return _block_a(urgency, is_office, caller_name, community, phone, issue)
    if block == "B":
        return _block_b(caller_name, community, phone, issue)
    if block == "C":
        return _block_c()
    if block == "D":
        return _block_d()
    return CallAction(
        type="note",
        caller_reply="He anotado su consulta. Le contactaremos pronto. Hasta luego.",
    )


def _block_a(urgency: str, is_office: bool, name: str, community: str, phone: str, issue: str) -> CallAction:
    notify_msg = (
        f"AVERÍA en {community}\n"
        f"Vecino: {name} · Tel: {phone}\n"
        f"Descripción: {issue}"
    )
    if urgency == "urgent" and is_office:
        return CallAction(
            type="transfer",
            transfer_to=_operator_phones(),
            caller_reply="Es una avería urgente. Le paso con uno de nuestros gestores ahora mismo.",
        )
    if urgency == "urgent" and not is_office:
        return CallAction(
            type="whatsapp_urgent",
            notify_phones=[settings.monica_whatsapp, settings.luis_whatsapp],
            notify_message=f"🚨 URGENTE (fuera de horario)\n{notify_msg}",
            caller_reply=(
                "Es fuera de horario de oficina, pero hemos avisado urgentemente a nuestros gestores. "
                "Le contactarán lo antes posible. Hasta luego."
            ),
        )
    return CallAction(
        type="email_normal",
        notify_to=settings.monica_email,
        notify_message=notify_msg,
        caller_reply=(
            "He registrado la avería y se la comunicamos a nuestra gestora Mónica. "
            "Le contactarán en horario de oficina. Hasta luego."
        ),
    )


def _block_b(name: str, community: str, phone: str, issue: str) -> CallAction:
    if _is_dates_query(issue):
        start = _fmt_date(settings.club_membership_start)
        end = _fmt_date(settings.club_membership_end)
        return CallAction(
            type="dates",
            caller_reply=(
                f"El periodo de socio del club es del {start} al {end}. "
                "¿Necesita alguna otra información?"
            ),
        )
    return CallAction(
        type="transfer",
        transfer_to=[settings.concha_phone],
        caller_reply="Le paso con Concha, que gestiona el club.",
        fallback_email_to=settings.concha_email,
        fallback_email_subject=f"Consulta club — {name} ({community})",
        fallback_email_body=(
            f"Vecino: {name} · Comunidad: {community} · Tel: {phone}\n"
            f"Consulta: {issue}\n\n(Concha no respondió a la transferencia)"
        ),
    )


def _block_c() -> CallAction:
    return CallAction(
        type="note",
        caller_reply=(
            "He anotado su gestión. Nuestro equipo la revisará y le contactará. Hasta luego."
        ),
    )


def _block_d() -> CallAction:
    return CallAction(
        type="busy",
        caller_reply=(
            "El administrador está atendiendo otras gestiones en este momento. "
            "He tomado nota de su llamada para que le devuelva el contacto. Hasta luego."
        ),
    )


def _operator_phones() -> list[str]:
    order = [p.strip().lower() for p in settings.operator_priority.split(",")]
    mapping = {
        "monica": settings.monica_phone,
        "concha": settings.concha_phone,
        "luis": settings.luis_phone,
    }
    return [mapping[op] for op in order if op in mapping and mapping[op]]


def _is_dates_query(issue: str) -> bool:
    keywords = ["fecha", "socio", "periodo", "cuándo", "cuando", "plazo", "inscripción", "inscripcion", "temporada"]
    return any(k in issue.lower() for k in keywords)


def _fmt_date(iso: str) -> str:
    months = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
    ]
    try:
        dt = datetime.strptime(iso, "%Y-%m-%d")
        return f"{dt.day} de {months[dt.month - 1]} de {dt.year}"
    except ValueError:
        return iso
