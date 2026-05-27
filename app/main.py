from __future__ import annotations

from fastapi import FastAPI

from app.core.storage import ensure_runtime_storage, storage_debug_info

app = FastAPI(title="ai-novella-engine-v2")


@app.on_event("startup")
def startup() -> None:
    ensure_runtime_storage()


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok", "service": "ai-novella-engine-v2"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/debug/storage")
def debug_storage() -> dict[str, str]:
    ensure_runtime_storage()
    return storage_debug_info()
