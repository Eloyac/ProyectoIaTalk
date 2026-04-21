from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""

    # Operadores
    monica_phone: str = ""
    concha_phone: str = ""
    luis_phone: str = ""
    operator_priority: str = "monica,luis,concha"

    # Notificaciones
    monica_whatsapp: str = ""
    luis_whatsapp: str = ""
    monica_email: str = ""
    concha_email: str = ""
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_host: str = "smtp.office365.com"
    smtp_port: int = 587

    # Horario L-V 9-14h / 16-19h
    office_hours_start: str = "09:00"
    office_hours_mid_end: str = "14:00"
    office_hours_mid_start: str = "16:00"
    office_hours_end: str = "19:00"
    office_days: str = "0,1,2,3,4"

    # Club — fechas periodo de socio
    club_membership_start: str = "2025-09-01"
    club_membership_end: str = "2025-09-30"

    # IA
    anthropic_api_key: str = ""
    deepgram_api_key: str = ""
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""

    # WhatsApp (Green API)
    green_api_base_url: str = "https://api.green-api.com"
    green_api_instance: str = ""
    green_api_token: str = ""

    # Despacho
    office_name: str = "Administración de Fincas"

    # Palabras clave de enfado (separadas por coma)
    anger_keywords: str = (
        "inaceptable,escándalo,denuncia,vergüenza,exijo,"
        "inmediatamente,ridículo,incompetentes,mala gestión,legal"
    )

    model_config = {"env_file": ".env", "case_sensitive": False}


settings = Settings()
