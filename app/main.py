from __future__ import annotations

import json
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

from app.core.storage import ensure_runtime_storage, get_storage_paths, read_state, storage_debug_info

PUBLIC_BASE_URL = "https://ai-novella-engine-v2-production.up.railway.app"

app = FastAPI(
    title="ai-novella-engine-v2",
    servers=[{"url": PUBLIC_BASE_URL}],
)

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


def read_repo_json(relative_path: str) -> dict[str, Any]:
    text = read_repo_text(relative_path)
    data = json.loads(text)
    return data if isinstance(data, dict) else {}


def read_all_state() -> tuple[dict[str, Any], dict[str, str]]:
    ensure_runtime_storage()
    result: dict[str, Any] = {}
    errors: dict[str, str] = {}
    for filename in STATE_FILES:
        try:
            result[filename] = read_state(filename)
        except Exception as exc:
            result[filename] = {}
            errors[filename] = str(exc)
    return result, errors


def add_unique(items: list[str], new_items: list[str]) -> None:
    for item in new_items:
        if isinstance(item, str) and item and item not in items:
            items.append(item)


def add_scene_required_files(files: list[str], scene_id: str, file_errors: dict[str, str]) -> None:
    scene_path = f"data/scenes/{scene_id}.json"
    add_unique(files, [scene_path])
    try:
        scene_data = read_repo_json(scene_path)
    except Exception as exc:
        file_errors[scene_path] = str(exc)
        return

    add_unique(files, scene_data.get("required_files", []))
    add_unique(files, scene_data.get("required_canon_files", []))

    character_ids = scene_data.get("required_character_ids", [])
    for character_id in character_ids:
        if isinstance(character_id, str):
            add_unique(files, [f"data/characters/main/{character_id}.json"])


@app.post("/api/v1/turn/context", operation_id="getTurnContext")
def turn_context(payload: TurnContextRequest) -> dict[str, Any]:
    state, state_errors = read_all_state()
    current_state = state.get("current_state.json", {})
    files = list(BASE_CONTEXT_FILES)
    file_errors: dict[str, str] = {}

    scene_id = current_state.get("current_scene_id") if isinstance(current_state, dict) else None
    if isinstance(scene_id, str) and scene_id:
        add_scene_required_files(files, scene_id, file_errors)

    file_contents: dict[str, str] = {}
    missing_files: list[str] = []
    if payload.include_file_contents:
        for filename in files:
            try:
                file_contents[filename] = read_repo_text(filename)
            except FileNotFoundError:
                missing_files.append(filename)
            except Exception as exc:
                file_errors[filename] = str(exc)

    return {
        "status": "ok",
        "mode": "context_only",
        "player_input": payload.player_input,
        "required_files": files,
        "missing_files": missing_files,
        "state_errors": state_errors,
        "file_errors": file_errors,
        "state": state,
        "file_contents": file_contents,
        "storage": storage_debug_info(),
        "next_step": "Use this returned context to write the next scene in ChatGPT.",
    }


@app.get("/actions/openapi.json", include_in_schema=False)
def actions_openapi() -> dict[str, Any]:
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "AI Novella Engine V2 Actions",
            "version": "1.0.0",
        },
        "servers": [{"url": PUBLIC_BASE_URL}],
        "paths": {
            "/api/v1/turn/context": {
                "post": {
                    "operationId": "getTurnContext",
                    "summary": "Get novella context for the next player turn",
                    "description": "Returns context for the Custom GPT. This server does not call OpenAI.",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["player_input"],
                                    "properties": {
                                        "player_input": {
                                            "type": "string",
                                            "description": "The player's latest action or dialogue."
                                        },
                                        "include_file_contents": {
                                            "type": "boolean",
                                            "default": True
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Context bundle for Custom GPT",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string"},
                                            "mode": {"type": "string"},
                                            "player_input": {"type": "string"},
                                            "required_files": {"type": "array", "items": {"type": "string"}},
                                            "missing_files": {"type": "array", "items": {"type": "string"}},
                                            "state_errors": {"type": "object", "additionalProperties": {"type": "string"}},
                                            "file_errors": {"type": "object", "additionalProperties": {"type": "string"}},
                                            "state": {"type": "object", "additionalProperties": True},
                                            "file_contents": {"type": "object", "additionalProperties": {"type": "string"}},
                                            "storage": {"type": "object", "additionalProperties": {"type": "string"}},
                                            "next_step": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
