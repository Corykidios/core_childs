"""
protocols/mp.py - MemoryPlugin protocol handler.

Adapted from the original call_of_core/mp-watcher.py. Same API calls, same
action set, shaped to the TAG + dispatch(cmd) contract watcher_core.py expects.

Requires: requests
Requires env var: MEMORY_PLUGIN_TOKEN
"""

import datetime
import os

import requests

TAG = "mp"

BASE_URL = "https://www.memoryplugin.com"
SOURCE = "core-watcher"


def _headers():
    token = os.environ.get("MEMORY_PLUGIN_TOKEN", "")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _today_utc():
    return datetime.datetime.utcnow().strftime("%Y-%m-%d")


def _api_search(query, count=10, bucket_id=None):
    params = {"query": query, "count": count, "source": SOURCE, "v": 2}
    if bucket_id:
        params["bucketId"] = bucket_id
    r = requests.get(f"{BASE_URL}/api/v2/memory", headers=_headers(), params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def _api_get(all_=False, latest=False, count=10, bucket_id=None):
    params = {"source": SOURCE, "v": 2, "count": count}
    if all_:
        params["all"] = "true"
    if latest:
        params["latest"] = "true"
    if bucket_id:
        params["bucketId"] = bucket_id
    r = requests.get(f"{BASE_URL}/api/v2/memory", headers=_headers(), params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def _api_store(text, bucket_id=None):
    dated = f"{_today_utc()} {text}"
    body = {"text": dated, "source": SOURCE}
    if bucket_id:
        body["bucketId"] = bucket_id
    r = requests.post(f"{BASE_URL}/api/memory", headers=_headers(), json=body, timeout=15)
    r.raise_for_status()
    return r.json()


def _api_get_buckets():
    r = requests.get(f"{BASE_URL}/api/buckets", headers=_headers(), timeout=15)
    r.raise_for_status()
    return r.json()


def _api_recall_chat(query):
    body = {"query": query, "source": SOURCE}
    r = requests.post(f"{BASE_URL}/api/chat-history/recall", headers=_headers(), json=body, timeout=30)
    r.raise_for_status()
    return r.json()


def _unpack(result):
    if isinstance(result, list):
        return result, []
    memories = result.get("memories") or result.get("data") or []
    buckets = result.get("buckets") or []
    return memories, buckets


def _fmt_memories(memories, buckets, header):
    lines = [header]
    if not memories:
        lines.append("  (none)")
    else:
        for i, m in enumerate(memories, 1):
            text = m.get("text") if isinstance(m, dict) else m
            lines.append(f"  {i}. {text}")
    if buckets:
        lines.append("")
        bstr = ", ".join(f"{b.get('name','?')} (id={b.get('id','?')})" for b in buckets)
        lines.append("[BUCKETS] " + bstr)
    return "\n".join(lines)


def dispatch(cmd):
    if not os.environ.get("MEMORY_PLUGIN_TOKEN"):
        return "[MP ERROR] MEMORY_PLUGIN_TOKEN not set in environment"

    action = cmd.get("action", "").lower().strip()
    bucket_id = cmd.get("bucketId") or cmd.get("bucket_id")

    if action == "search":
        result = _api_search(cmd["query"], cmd.get("count", 10), bucket_id)
        memories, buckets = _unpack(result)
        return _fmt_memories(memories, buckets, "[MP SEARCH RESULTS]")

    elif action == "get":
        result = _api_get(cmd.get("all", False), cmd.get("latest", False), cmd.get("count", 10), bucket_id)
        memories, buckets = _unpack(result)
        return _fmt_memories(memories, buckets, "[MP MEMORIES]")

    elif action == "store":
        text = cmd.get("text") or cmd.get("content") or cmd.get("memory")
        if not text:
            return "[MP ERROR] store requires a 'text' field"
        _api_store(text, bucket_id)
        return f'[MP STORED] OK: "{text}"'

    elif action == "get_buckets":
        result = _api_get_buckets()
        buckets = result if isinstance(result, list) else result.get("data", [])
        if not buckets:
            return "[MP BUCKETS] (none)"
        lines = ["[MP BUCKETS]"]
        for b in buckets:
            lines.append(f"  id={b.get('id')}  name={b.get('name')}  count={b.get('memoryCount','?')}  {b.get('description','')}")
        return "\n".join(lines)

    elif action in ("recall_chat", "recall"):
        result = _api_recall_chat(cmd["query"])
        summary = result.get("summary") or result.get("data") or str(result)
        return f"[MP CHAT RECALL]\n{summary}"

    else:
        return f"[MP ERROR] Unknown action: {action!r}\n  Valid: search | get | store | get_buckets | recall_chat"
