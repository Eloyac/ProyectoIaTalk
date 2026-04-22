from fastapi import FastAPI
from src.storage.db import init_db
from src.voice.twilio_handler import router as twilio_router

app = FastAPI(title="Agente IA Fincas")


@app.on_event("startup")
async def startup():
    init_db()


@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(twilio_router)
