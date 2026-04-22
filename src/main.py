from fastapi import FastAPI

app = FastAPI(title="Agente IA Fincas")


@app.get("/health")
async def health():
    return {"status": "ok"}
