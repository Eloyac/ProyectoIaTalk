# Diseño: Agente IA de Llamadas — Administración de Fincas

**Fecha**: 2026-04-21  
**Estado**: Aprobado  
**Stack**: Python · Twilio · Claude Haiku · Deepgram · ElevenLabs · Green API · SMTP Outlook

---

## Contexto

El despacho de administración de fincas recibe 10-30 llamadas diarias. El objetivo es un agente de voz IA en español que sustituya el filtro de la secretaría: triaje, toma de notas, notificaciones y transferencias. Coste objetivo: 13-50€/mes, escalable.

---

## Arquitectura

```
Vecino llama al 6xx (móvil del despacho)
  → Desvío de llamada del operador → número Twilio VoIP
  → Twilio: POST /incoming-call → TwiML con WebSocket
  → WS /media-stream → audio en tiempo real
  → Deepgram STT → texto
  → Claude Haiku: árbol de decisiones + detección enfado
  → ElevenLabs TTS → audio → vecino
  → Acción: email SMTP / WhatsApp Green API / Twilio <Dial>
  → SQLite: registro de llamada
```

---

## Flujo conversacional

### Fase obligatoria (siempre al inicio)
Recoger nombre, comunidad/edificio, teléfono.  
Confirmar antes de cerrar: *"Entonces es [caso] en [comunidad] y le llamamos al [teléfono], ¿correcto?"*

### Bloque A — Averías
| Caso | Acción |
|---|---|
| Urgente · en horario (L-V 9-14h / 16-19h) | Twilio `<Dial>` operador de turno |
| Urgente · fuera de horario | WhatsApp Green API a Mónica + Luis |
| Normal | Email SMTP Outlook a Mónica + mensaje cierre |

### Bloque B — Clubs
| Caso | Acción |
|---|---|
| Fechas de socio | Respuesta locutada con fechas del `.env` |
| Otra consulta | Dial a Concha; si no contesta en 20s → email a Concha |

### Bloque C — Comunidades (no avería)
Mensaje de cierre + registro en SQLite.

### Bloque D — Hablar con el administrador
| Caso | Acción |
|---|---|
| Tono normal | Mensaje "está ocupado" + registro SQLite |
| Tono enfadado | Mensaje empatía + Dial operador inmediato |

### Detección de enfado
- Palabras clave configurables en `.env` (`ANGER_KEYWORDS`)
- Claude Haiku devuelve `anger_level: low|medium|high` en cada turno
- Si `high`: transferencia inmediata, independiente del bloque activo

---

## Estructura de módulos

```
src/
├── main.py                   # FastAPI: /incoming-call, /media-stream
├── agent/
│   ├── call_handler.py       # orquesta turno a turno
│   ├── decision_tree.py      # lógica A/B/C/D
│   ├── anger_detector.py     # Claude → anger_level
│   └── schedule_checker.py  # is_office_hours()
├── voice/
│   ├── stt.py                # Deepgram streaming ES
│   ├── tts.py                # ElevenLabs → audio
│   └── twilio_ws.py          # WebSocket media stream
├── notifications/
│   ├── whatsapp.py           # Green API
│   ├── email.py              # SMTP Outlook
│   └── transfer.py           # Twilio <Dial> + fallback
└── storage/
    ├── db.py                 # SQLite
    └── models.py             # CallRecord, Incident
config/settings.py            # pydantic-settings carga .env
scripts/seed_config.py        # setup interactivo del .env
```

---

## Configuración (.env)

Variables clave (ver `.env.example` para la lista completa):
- Twilio: account SID, auth token, número VoIP
- Operadores: teléfonos de Mónica, Concha, Luis + orden de prioridad
- Notificaciones: WhatsApp, emails, SMTP Outlook
- Horario: horas inicio/fin mañana y tarde, días laborables
- Club: fechas de inicio y fin del periodo de socio
- IA: API keys Anthropic, Deepgram, ElevenLabs, Green API
- Enfado: lista de palabras clave separadas por coma

---

## Servicios y coste estimado

| Servicio | Free tier | Coste 10-30 llamadas/día |
|---|---|---|
| Twilio | 15$ crédito inicial | ~8-25€ |
| Claude Haiku | — | ~5-15€ |
| Deepgram | 200h/mes | ~0€ |
| ElevenLabs | 10k chars/mes | ~0-5€ |
| Green API | 500 msg/mes | ~0€ |
| SMTP Outlook | gratuito | ~0€ |
| Railway | free tier | ~0-5€ |
| **Total** | | **~13-50€/mes** |

---

## Fases de implementación

| Fase | Contenido | Duración |
|---|---|---|
| 1 | Fundamentos: estructura, config, DB, schedule_checker, Railway | 1 semana |
| 2 | Telefonía: Twilio WebSocket, Deepgram STT, ElevenLabs TTS | 1 semana |
| 3 | Cerebro: anger_detector, decision_tree, guiones ES, recogida datos | 1-2 semanas |
| 4 | Notificaciones: email, WhatsApp, transferencias, integración árbol | 1 semana |
| 5 | Pulido: logging, error handling, tests, seed_config, pruebas reales | 1 semana |

**Total estimado**: 5-6 semanas

---

## Verificación

- Llamada completa: saludo → recogida datos → confirmación → acción correcta
- Avería urgente fuera de horario → WhatsApp a Mónica Y Luis
- Palabras de enfado → transferencia inmediata
- Club fechas → agente da las del `.env`
- Concha no contesta → fallback email
- `.env.example` sin credenciales en git
- SQLite contiene registros de todas las llamadas de prueba
