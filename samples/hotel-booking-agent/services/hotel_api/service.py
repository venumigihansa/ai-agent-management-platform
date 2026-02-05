from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI
from dotenv import load_dotenv

from booking import router as booking_router
from ingest import ensure_policy_index
from search import router as search_router

_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=_env_path, override=False)

app = FastAPI(title="Hotel Booking API")


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(booking_router)
app.include_router(search_router)


@app.on_event("startup")
def bootstrap_policy_index() -> None:
    ensure_policy_index()
