"""Entrypoint for IncidentOS AI Engine."""

from fastapi import FastAPI

app = FastAPI(title="IncidentOS AI Engine")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
