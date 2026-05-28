from __future__ import annotations

import json
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.core.storage import ensure_runtime_storage, get_storage_paths, read_state, storage_debug_info

PUBLIC_BASE_URL = "https://ai-novella-engine-v2-production.up.railway.app"

app = FastAPI(
    title="ai-novella-engine-v2",
    servers=[{"url": PUBLIC_BASE_URL}],
)

STATE_FILES = [
    "current_state.json",
    "knowledge_state.json",
    "relationships.json",
    "inventory_state.json",
    "scene_history.json",
]


class TurnContextRequest(BaseModel):
    player_input: str


class FileContentRequest(BaseModel):
    path: str
    json_field: str | None = None


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


def repo_path(relative_path: str):
    root = get_storage_paths().project_root
    path = (root / relative_path).resolve()
    if root not in path.parents and path != root:
        raise HTTPException(status_code=400, detail="unsafe path")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="file not found")
    return path


def read_state_safe(filename: str) -> Any:
    try:
        return read_state(filename)
    except Exception:
        return {} if filename != "scene_history.json" else []


def build_hard_rules(scene_id: str) -> list[str]:
    if scene_id != "start_scene":
        return []
    return [
        "До 03:10 запрещено вводить людей Самуэля, официальную группу, блокировку дома, команды по связи, фразы 'объект подтверждён', 'дом блокировать', 'цель подтверждена' и любые аналоги.",
        "До 03:10 линия Самуэля существует только как скрытый мотив Эммы; она не проявляется внешними людьми, радио, командами или машинами.",
        "До 03:02 внешнее напряжение можно давать только нейтрально: шум дороги, ветер, мотор вдалеке, шаги, реакция энергии. Не идентифицировать это как людей Самуэля.",
        "Райден появляется только около 03:02 и только если уже сработал emma_energy_impulse_occurred, energy_flare_occurred или akira_escaped_to_road.",
        "Если время раньше 03:02, Райден может быть только подготовлен нейтральным шумом мотора/дороги; он не обязан появляться и не знает Акиру.",
        "Эхо в start_scene запрещены. Энергия Эммы воды/давления разрешена и не считается Эхо.",
        "Не использовать слово 'объект' для Акиры в ранней сцене: это звучит как люди Самуэля и ломает тайминг."
    ]


@app.post("/api/v1/file/content", operation_id="getFileContent")
def get_file_content(payload: FileContentRequest) -> dict[str, Any]:
    path = repo_path(payload.path)
    raw_text = path.read_text(encoding="utf-8", errors="replace")

    if payload.json_field:
        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail=f"invalid json: {exc}") from exc
        if not isinstance(data, dict) or payload.json_field not in data:
            raise HTTPException(status_code=404, detail="json field not found")
        value = data[payload.json_field]
        return {
            "status": "ok",
            "path": payload.path,
            "json_field": payload.json_field,
            "content": value,
        }

    return {
        "status": "ok",
        "path": payload.path,
        "content": raw_text,
    }


@app.post("/api/v1/turn/context", operation_id="getTurnContext")
def turn_context(payload: TurnContextRequest) -> dict[str, Any]:
    current_state = read_state_safe("current_state.json")
    if not isinstance(current_state, dict):
        current_state = {}

    scene_id = current_state.get("current_scene_id") or "start_scene"
    scene_file = f"data/scenes/{scene_id}.json"

    return {
        "status": "ok",
        "mode": "minimal_context",
        "player_input": payload.player_input,
        "current_scene_id": scene_id,
        "current_date": current_state.get("current_date"),
        "time_of_day": current_state.get("time_of_day"),
        "location_id": current_state.get("location_id"),
        "turn_number": current_state.get("turn_number", 0),
        "story_flags": current_state.get("story_flags", {}),
        "primary_file": scene_file,
        "format_file": "data/gpt/scene_format.md",
        "hard_rules": build_hard_rules(scene_id),
        "next_step": "Call getFileContent with path=primary_file. For start_scene first output, use json_field=text and print it verbatim. For later scene turns, also call getFileContent with path=format_file and keep that format. Always obey hard_rules.",
    }


@app.get("/actions/openapi.json", include_in_schema=False)
def actions_openapi() -> dict[str, Any]:
    return {
        "openapi": "3.1.0",
        "info": {"title": "AI Novella Engine V2 Actions", "version": "1.0.0"},
        "servers": [{"url": PUBLIC_BASE_URL}],
        "paths": {
            "/api/v1/turn/context": {
                "post": {
                    "operationId": "getTurnContext",
                    "summary": "Get minimal current scene pointer",
                    "description": "Returns minimal state, primary scene file, format file and small hard_rules. Then call getFileContent for needed files.",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["player_input"],
                                    "properties": {"player_input": {"type": "string"}}
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "Minimal scene pointer with hard rules"}}
                }
            },
            "/api/v1/file/content": {
                "post": {
                    "operationId": "getFileContent",
                    "summary": "Get one repository file or one JSON field",
                    "description": "Returns only the requested file content. Use json_field=text for start_scene text. Use path=data/gpt/scene_format.md for mandatory scene format.",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["path"],
                                    "properties": {
                                        "path": {"type": "string", "description": "Repository file path, for example data/scenes/start_scene.json or data/gpt/scene_format.md"},
                                        "json_field": {"type": "string", "description": "Optional JSON field to return, for example text"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "Single file content"}}
                }
            }
        }
    }
