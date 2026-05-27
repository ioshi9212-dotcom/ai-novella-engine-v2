from __future__ import annotations

import json

from app.core.storage import ensure_runtime_storage, storage_debug_info


if __name__ == "__main__":
    ensure_runtime_storage()
    print(json.dumps(storage_debug_info(), ensure_ascii=False, indent=2))
