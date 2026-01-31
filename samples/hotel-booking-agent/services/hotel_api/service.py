from __future__ import annotations

from importlib import util as importlib_util
import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from booking import router as booking_router
from search import router as search_router

logger = logging.getLogger(__name__)

_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=_env_path, override=False)

app = FastAPI(title="Hotel Booking API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=86400,
)


def _load_policy_ingest_module():
    ingest_path = Path(__file__).resolve().parent / "ingest.py"
    if not ingest_path.exists():
        logger.warning("policy ingest script not found at %s", ingest_path)
        return None
    spec = importlib_util.spec_from_file_location("policy_ingest", ingest_path)
    if spec is None or spec.loader is None:
        logger.warning("unable to load policy ingest module from %s", ingest_path)
        return None
    module = importlib_util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _default_policies_dir() -> Path:
    return Path(__file__).resolve().parent / "resources" / "policy_pdfs"


def _ensure_policy_index() -> None:
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    if not pinecone_api_key:
        logger.info("PINECONE_API_KEY not set; skipping policy ingest")
        return

    try:
        from pinecone import Pinecone
    except Exception:
        logger.exception("pinecone client not available; skipping policy ingest")
        return

    index_name = os.getenv("PINECONE_INDEX_NAME", "hotelbookingdb")
    try:
        pc = Pinecone(api_key=pinecone_api_key)
        index_names = pc.list_indexes().names()
        if index_name in index_names:
            logger.info("policy index '%s' already exists; skipping ingest", index_name)
            return
    except Exception:
        logger.exception("failed to check Pinecone index; skipping policy ingest")
        return

    ingest_module = _load_policy_ingest_module()
    if ingest_module is None:
        return

    policies_dir = os.getenv("POLICIES_DIRS") or str(_default_policies_dir())
    try:
        ingestion = ingest_module.PolicyIngestion()
        ingestion.ingest_all_policies(policies_dir=policies_dir)
        logger.info("policy ingest completed")
    except Exception:
        logger.exception("policy ingest failed")


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(booking_router)
app.include_router(search_router)


@app.on_event("startup")
def bootstrap_policy_index() -> None:
    _ensure_policy_index()
