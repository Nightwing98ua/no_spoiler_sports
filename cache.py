import json
import os
import time
from config import CACHE_FILE, CACHE_TTL_SECONDS

_memory_cache = {}


def _load_disk_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_disk_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)


if not _memory_cache:
    _memory_cache = _load_disk_cache()


def get_or_fetch(key, fetch_fn):
    """
    key: наприклад "football:2026-09-10"
    fetch_fn: функція без аргументів, яка робить реальний запит до API
    """
    entry = _memory_cache.get(key)
    now = time.time()

    if entry and (now - entry["ts"]) < CACHE_TTL_SECONDS:
        return entry["data"]

    data = fetch_fn()
    _memory_cache[key] = {"ts": now, "data": data}
    _save_disk_cache(_memory_cache)
    return data
