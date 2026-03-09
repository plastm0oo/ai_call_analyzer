from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(
    title="Call Analyzer Backend",
    description="Backend for sales call transcription and multi-agent analysis",
    version="1.0.0"
)

app.include_router(router)


@app.get("/health")
def health_check():
    return {"status": "ok"}