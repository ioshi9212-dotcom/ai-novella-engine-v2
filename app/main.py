from __future__ import annotations

import json
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

from app.core.storage import ensure_runtime_storage, get_storage_paths, read_state, storage_debug_info

PUBLIC_BASE_URL = "https://ai-novella-engine-v2-production.up.railway.app"
MAX_CONTEXT_FILE_CHARS = 12000
MAX_PROMPT_CONTEXT_CHARS = 18000

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


def repo_path(relative_path: str):
    root = get_storage_paths().project_root
    path = (root / relative_path).resolve()
    if root not in path.parents and path != root:
        raise ValueError("unsafe path")
    return path


def read_repo_text(relative_path: str, limit: int = MAX_CONTEXT_FILE_CHARS) -> str:
    text = repo_path(relative_path).read_text(encoding="utf-8", errors="replace")
    if len(text) > limit:
        return text[:limit].rstrip() + "\n\n[TRUNCATED]"
    return text


def read_repo_json(relative_path: str) -> dict[str, Any]:
    text = repo_path(relative_path).read_text(encoding="utf-8", errors="replace")
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


def truncate(value: Any, limit: int = 700) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."


def dump_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def compact_list(value: Any, limit: int = 6) -> Any:
    if not isinstance(value, list):
        return value
    if len(value) <= limit:
        return value
    return value[:limit] + [f"...ещё {len(value) - limit} пунктов скрыто"]


def compact_dict(value: dict[str, Any], list_limit: int = 6) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, item in value.items():
        if isinstance(item, str):
            result[key] = truncate(item, 900)
        elif isinstance(item, list):
            result[key] = [truncate(x, 700) if isinstance(x, str) else x for x in compact_list(item, list_limit)]
        elif isinstance(item, dict):
            result[key] = compact_dict(item, list_limit=4)
        else:
            result[key] = item
    return result


def compact_scene(scene: dict[str, Any]) -> dict[str, Any]:
    return {
        "scene_id": scene.get("scene_id"),
        "scene_type": scene.get("scene_type"),
        "title": scene.get("title"),
        "location_id": scene.get("location_id"),
        "current_date": scene.get("current_date"),
        "time": scene.get("time"),
        "scene_tags": scene.get("scene_tags", []),
        "first_turn_output_mode": scene.get("first_turn_output_mode"),
        "text": scene.get("text", "") if scene.get("first_turn_output_mode") == "verbatim_text_only" else truncate(scene.get("text"), 2600),
        "participants": scene.get("participants", []),
        "active_character_ids": scene.get("active_character_ids", []),
        "nearby_character_ids": scene.get("nearby_character_ids", []),
        "conditional_character_ids": scene.get("conditional_character_ids", []),
        "required_character_ids": scene.get("required_character_ids", []),
        "required_files": scene.get("required_files", []),
        "conditional_required_files": scene.get("conditional_required_files", {}),
        "scene_participants": scene.get("scene_participants", []),
        "knowledge_table": scene.get("knowledge_table", {}),
        "conditions": compact_dict(scene.get("conditions", {})),
    }


def compact_character(raw: dict[str, Any]) -> dict[str, Any]:
    keep = {
        "character_id": raw.get("character_id"),
        "name": raw.get("name"),
        "aliases": raw.get("aliases", []),
        "role": truncate(raw.get("role"), 900),
        "status": raw.get("status"),
        "known_to_player": raw.get("known_to_player"),
        "age": raw.get("age"),
        "gender": raw.get("gender"),
        "height_cm": raw.get("height_cm"),
    }
    important = [
        "appearance", "style", "short_scene_use", "base_behavior", "speech_style",
        "toward_akira", "toward_raiden", "toward_irey", "knowledge", "relationships",
        "scene_rules", "forbidden", "do_not_break", "triggers", "reveal_rules",
        "energy", "combat_behavior", "current_state", "memory_rules",
    ]
    for field in important:
        if field not in raw:
            continue
        value = raw[field]
        if isinstance(value, dict):
            keep[field] = compact_dict(value)
        elif isinstance(value, list):
            keep[field] = [truncate(x, 700) if isinstance(x, str) else x for x in compact_list(value)]
        else:
            keep[field] = truncate(value, 900)
    return keep


def add_scene_required_files(files: list[str], scene_id: str, file_errors: dict[str, str]) -> dict[str, Any]:
    scene_path = f"data/scenes/{scene_id}.json"
    add_unique(files, [scene_path])
    try:
        scene_data = read_repo_json(scene_path)
    except Exception as exc:
        file_errors[scene_path] = str(exc)
        return {}

    add_unique(files, scene_data.get("required_files", []))
    add_unique(files, scene_data.get("required_canon_files", []))

    character_ids = scene_data.get("required_character_ids", [])
    for character_id in character_ids:
        if isinstance(character_id, str):
            add_unique(files, [f"data/characters/main/{character_id}.json"])

    return scene_data


def build_api_context(files: list[str], scene_data: dict[str, Any], file_errors: dict[str, str]) -> dict[str, Any]:
    characters: list[dict[str, Any]] = []
    rules_and_canon: dict[str, str] = {}

    for filename in files:
        try:
            if filename.startswith("data/characters/main/") and filename.endswith(".json"):
                characters.append(compact_character(read_repo_json(filename)))
            elif filename.startswith("data/canon/") or filename.startswith("data/rules/") or filename.startswith("data/gpt/"):
                rules_and_canon[filename] = read_repo_text(filename, limit=2200)
        except FileNotFoundError:
            continue
        except Exception as exc:
            file_errors[filename] = str(exc)

    return {
        "scene": compact_scene(scene_data) if scene_data else {},
        "characters": characters,
        "rules_and_canon": rules_and_canon,
    }


def build_prompt_context(player_input: str, state: dict[str, Any], api_context: dict[str, Any], files: list[str]) -> str:
    current = state.get("current_state.json", {}) if isinstance(state, dict) else {}
    knowledge = state.get("knowledge_state.json", {})
    relationships = state.get("relationships.json", {})
    inventory = state.get("inventory_state.json", {})
    history = state.get("scene_history.json", [])

    if not isinstance(current, dict):
        current = {}

    prompt = f"""
SUMMARY:
Краткой памяти пока нет или она хранится в scene_history.

STATE:
- scene: {current.get('current_scene_id')}
- date: {current.get('current_date')}
- time_of_day: {current.get('time_of_day')}
- location: {current.get('location_id')}
- active: {current.get('active_characters')}
- nearby: {current.get('nearby_characters')}
- turn_number: {current.get('turn_number')}
- story_flags: {dump_json(current.get('story_flags', {}))}

KNOWLEDGE_STATE:
{dump_json(knowledge)}

RELATIONSHIPS:
{dump_json(relationships)}

INVENTORY:
{dump_json(inventory)}

SCENE_HISTORY:
{dump_json(history[-4:] if isinstance(history, list) else history)}

ACTIVE_SCENE_PASSPORT:
{dump_json(api_context.get('scene', {}))}

API_CONTEXT:
{dump_json(api_context)}

REQUIRED_FILES:
{dump_json(files)}

PLAYER_INPUT:
{player_input}

TASK:
Продолжить сцену, используя только STATE, ACTIVE_SCENE_PASSPORT, API_CONTEXT, SCENE_HISTORY, RELATIONSHIPS, KNOWLEDGE_STATE, INVENTORY и PLAYER_INPUT.
Если scene=start_scene и story_flags.start_scene_first_turn_output=false, вывести text из ACTIVE_SCENE_PASSPORT дословно и не продолжать сверх него.
Не раскрывать hidden-lore без основания. Не писать выбор за Акиру. Не показывать JSON пользователю.
""".strip()

    if len(prompt) > MAX_PROMPT_CONTEXT_CHARS:
        return prompt[:MAX_PROMPT_CONTEXT_CHARS].rstrip() + "\n\n[CONTEXT_TRUNCATED]"
    return prompt


@app.post("/api/v1/turn/context", operation_id="getTurnContext")
def turn_context(payload: TurnContextRequest) -> dict[str, Any]:
    state, state_errors = read_all_state()
    current_state = state.get("current_state.json", {})
    files = list(BASE_CONTEXT_FILES)
    file_errors: dict[str, str] = {}
    scene_data: dict[str, Any] = {}

    scene_id = current_state.get("current_scene_id") if isinstance(current_state, dict) else None
    if isinstance(scene_id, str) and scene_id:
        scene_data = add_scene_required_files(files, scene_id, file_errors)

    api_context = build_api_context(files, scene_data, file_errors)
    prompt_context = build_prompt_context(payload.player_input, state, api_context, files)

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
        "api_context": api_context,
        "prompt_context": prompt_context,
        "file_contents": file_contents,
        "storage": storage_debug_info(),
        "next_step": "Use prompt_context as the main instruction/context for the next scene.",
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
                    "summary": "Get novella context for the next player turn",
                    "description": "Returns compact prompt_context, state and optional file contents. This server does not call OpenAI.",
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": {
                            "type": "object",
                            "required": ["player_input"],
                            "properties": {
                                "player_input": {"type": "string"},
                                "include_file_contents": {"type": "boolean", "default": True}
                            }
                        }}}
                    },
                    "responses": {"200": {"description": "Context bundle for Custom GPT"}}
                }
            }
        }
    }
