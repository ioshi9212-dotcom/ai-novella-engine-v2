"""Persistent runtime storage helpers.

Canon files live in the repository.
Runtime state lives in Railway Volume or local runtime_data.
"""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any


STATE_FILENAMES: tuple[str, ...] = (
    "current_state.json",
    "knowledge_state.json",
    "relationships.json",
    "inventory_state.json",
    "scene_history.json",
)

RUNTIME_SUBDIRS: tuple[str, ...] = (
    "state",
    "sessions",
    "logs",
    "backups",
    "exports",
    "tmp",
)


@dataclass(frozen=True)
class StoragePaths:
    """Resolved runtime storage paths."""

    project_root: Path
    runtime_root: Path
    state_root: Path
    sessions_root: Path
    logs_root: Path
    backups_root: Path
    exports_root: Path
    tmp_root: Path
    state_templates_root: Path


def project_root() -> Path:
    """Return repository root based on this file location."""

    return Path(__file__).resolve().parents[2]


def resolve_runtime_root() -> Path:
    """Resolve runtime data root.

    Priority:
    1. NOVELLA_RUNTIME_DATA_ROOT
    2. RAILWAY_VOLUME_MOUNT_PATH
    3. ./runtime_data for local development
    """

    root = (
        os.getenv("NOVELLA_RUNTIME_DATA_ROOT")
        or os.getenv("RAILWAY_VOLUME_MOUNT_PATH")
        or str(project_root() / "runtime_data")
    )
    return Path(root).expanduser().resolve()


def get_storage_paths() -> StoragePaths:
    """Return all important storage paths."""

    root = project_root()
    runtime_root = resolve_runtime_root()
    return StoragePaths(
        project_root=root,
        runtime_root=runtime_root,
        state_root=runtime_root / "state",
        sessions_root=runtime_root / "sessions",
        logs_root=runtime_root / "logs",
        backups_root=runtime_root / "backups",
        exports_root=runtime_root / "exports",
        tmp_root=runtime_root / "tmp",
        state_templates_root=root / "data" / "state",
    )


def ensure_runtime_storage() -> StoragePaths:
    """Create runtime dirs and initialize missing state files.

    This must run at application startup, not at build time.
    Existing runtime state files are never overwritten.
    """

    paths = get_storage_paths()

    for subdir in RUNTIME_SUBDIRS:
        (paths.runtime_root / subdir).mkdir(parents=True, exist_ok=True)

    paths.state_templates_root.mkdir(parents=True, exist_ok=True)

    for filename in STATE_FILENAMES:
        target = paths.state_root / filename
        template = paths.state_templates_root / filename
        if target.exists():
            continue
        if template.exists():
            shutil.copy2(template, target)
        else:
            target.write_text("{}\n", encoding="utf-8")

    return paths


def state_file_path(filename: str) -> Path:
    """Return path to a runtime state file.

    Raises ValueError for unexpected names to avoid accidental writes.
    """

    if filename not in STATE_FILENAMES:
        raise ValueError(f"Unsupported state file: {filename}")
    return get_storage_paths().state_root / filename


def read_json(path: Path) -> dict[str, Any]:
    """Read JSON object from path. Empty files are treated as {}."""

    if not path.exists():
        return {}
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return {}
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return data


def write_json_atomic(path: Path, data: dict[str, Any]) -> None:
    """Atomically write JSON object to path."""

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(tmp_path, path)


def read_state(filename: str) -> dict[str, Any]:
    """Read a runtime state JSON file from the volume/local runtime root."""

    ensure_runtime_storage()
    return read_json(state_file_path(filename))


def write_state(filename: str, data: dict[str, Any]) -> None:
    """Write a runtime state JSON file to the volume/local runtime root."""

    ensure_runtime_storage()
    write_json_atomic(state_file_path(filename), data)


def storage_debug_info() -> dict[str, str]:
    """Return paths useful for debug endpoints/logs."""

    paths = get_storage_paths()
    return {
        "project_root": str(paths.project_root),
        "runtime_root": str(paths.runtime_root),
        "state_root": str(paths.state_root),
        "sessions_root": str(paths.sessions_root),
        "logs_root": str(paths.logs_root),
        "backups_root": str(paths.backups_root),
        "exports_root": str(paths.exports_root),
        "tmp_root": str(paths.tmp_root),
        "state_templates_root": str(paths.state_templates_root),
    }


if __name__ == "__main__":
    resolved = ensure_runtime_storage()
    print(json.dumps(storage_debug_info(), ensure_ascii=False, indent=2))
