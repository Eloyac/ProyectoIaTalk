# CLAUDE.md — Agente IA de Llamadas · Administración de Fincas

## Qué es este proyecto
Agente de voz IA en español que responde llamadas del despacho, hace triaje de incidencias, notifica por WhatsApp/email y transfiere llamadas urgentes. Sustituye el filtro de la secretaría.

## Stack
- **Python + FastAPI** — servidor principal
- **Twilio** — telefonía VoIP + ConversationRelay (STT/TTS gestionado)
- **Claude Haiku** — LLM del agente (árbol de decisiones, detección de enfado)
- **Deepgram** — STT español (vía ConversationRelay)
- **ElevenLabs** — TTS español natural (vía ConversationRelay)
- **Green API** — WhatsApp personal (avisos urgentes a Mónica y Luis)
- **SMTP Outlook** — email a Mónica/Concha
- **SQLite** — registro de llamadas
- **Railway** — hosting (free tier)

## Estructura de módulos
- `src/agent/` — decision_tree, anger_detector, schedule_checker, call_handler
- `src/voice/` — WebSocket ConversationRelay
- `src/notifications/` — WhatsApp, email, transferencia
- `src/storage/` — SQLite models y db
- `config/settings.py` — pydantic-settings carga .env

## Spec de diseño
`docs/superpowers/specs/2026-04-21-agente-llamadas-fincas-design.md`

## Skills relevantes
- `twilio-voice-agent` — ConversationRelay + Media Streams patterns
- `green-api-whatsapp` — WhatsApp con Green API
- `claude-api` — Anthropic SDK

## Conventions
- Todo configurable en `.env` — sin hardcode de números ni horarios
- Mantener cambios mínimos
- No inventar datos
- Explicar riesgos antes de cambios grandes
- Logs estructurados por llamada

## Important paths
- `src/` — código fuente
- `config/` — settings
- `scripts/` — utilidades
- `logs/` — logs de llamadas
- `docs/` — specs y documentación

## Working preferences
- Respuestas breves por defecto
- Proponer logging si falta observabilidad
- Documentar solo con datos reales