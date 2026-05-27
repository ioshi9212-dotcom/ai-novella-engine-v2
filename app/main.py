from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

from app.core.storage import ensure_runtime_storage, get_storage_paths, read_state, storage_debug_info

app = FastAPI(title="ai-novella-engine-v2")

BASE_CONTEXT_FILES = [
    "data/canon/novella_goal.md",
    "data/canon/inner_subtext_style.md",
    "data/gpt/engine_prompt.md",
    "data/gpt/scene_format.md",
    "data/rules/source_loading_rules.md",
    "data/rules/knowledge_rules.md",
    "data/rules/player_control_rules.md",
    "data/canon/canon_index.md",
    "data/calendar/character_availability.json",
    "data/characters/character_id_index.json",
    "data/characters/main/akira.json",
]

STATE_FILES = [
    "current_state.json",
    "knowledge_state.json",
    "relationships.json",
    "inventory_state.json",
    "scene_history.json",
]


class TurnContextRequest(BaseModel):
    player_input: str
    include_file_contents: bool = True


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


def read_repo_text(relative_path: str) -> str:
    root = get_storage_paths().project_root
    path = (root / relative_path).resolve()
    if root not in path.parents and path != root:
        raise ValueError("unsafe path")
    text = path.read_text(encoding="utf-8", errors="replace")
    return text[:12000]


def read_all_state() -> dict[str, Any]:
    ensure_runtime_storage()
    result: dict[str, Any] = {}
    for filename in STATE_FILES:
        result[filename] = read_state(filename)
    return result


@app.post("/api/v1/turn/context")
def turn_context(payload: TurnContextRequest) -> dict[str, Any]:
    state = read_all_state()
    current_state = state.get("current_state.json", {})
    files = list(BASE_CONTEXT_FILES)

    scene_id = current_state.get("current_scene_id") if isinstance(current_state, dict) else None
    if isinstance(scene_id, str) and scene_id:
        files.append(f"data/scenes/{scene_id}.json")

    file_contents: dict[str, str] = {}
    missing_files: list[str] = []
    if payload.include_file_contents:
        for filename in files:
            try:
                file_contents[filename] = read_repo_text(filename)
            except FileNotFoundError:
                missing_files.append(filename)

    return {
        "status": "ok",
        "mode": "context_only",
        "player_input": payload.player_input,
        "required_files": files,
        "missing_files": missing_files,
        "state": state,
        "file_contents": file_contents,
        "next_step": "Use this returned context to write the next scene in ChatGPT.",
    }
