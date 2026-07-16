"""
model_router.py - Unified local/cloud LLM access for the watcher system.

Wraps LiteLLM so Night (safety review) and Light (module drafting) can both
call an LLM without caring whether the backend is a local Ollama model or
a cloud API. Tries local first for "fast" calls, falls back to cloud only
if local is unavailable; "smart" calls go straight to the cloud chain.

No API keys ever live in this file. LiteLLM reads them from environment
variables per its own convention - set them in .env, never here, never in chat.
"""

import os

try:
    from litellm import completion
except ImportError:
    completion = None

LOCAL_FAST_MODEL = os.environ.get("WATCHER_LOCAL_MODEL", "ollama/qwen3.5:9b")
OLLAMA_BASE = os.environ.get("OLLAMA_API_BASE", "http://localhost:11434")

CLOUD_FALLBACKS = [
    m.strip() for m in os.environ.get(
        "WATCHER_CLOUD_MODELS",
        "openrouter/deepseek/deepseek-chat,openrouter/meta-llama/llama-3.3-70b-instruct"
    ).split(",") if m.strip()
]


def _ollama_alive():
    try:
        import requests
        requests.get(OLLAMA_BASE, timeout=1)
        return True
    except Exception:
        return False


def ask(system_prompt, user_prompt, prefer="fast", max_tokens=400):
    """
    Send one prompt through the router. prefer=''fast'' tries local Ollama
    first (falls back to cloud if unreachable); prefer=''smart'' skips
    straight to the cloud fallback chain.

    Returns the response text, or raises RuntimeError if every backend fails.
    """
    if completion is None:
        raise RuntimeError("litellm not installed - pip install litellm")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    candidates = []
    if prefer == "fast" and _ollama_alive():
        candidates.append(LOCAL_FAST_MODEL)
    candidates.extend(CLOUD_FALLBACKS)

    if not candidates:
        raise RuntimeError("No model backends configured (Ollama unreachable, no cloud fallbacks set)")

    last_err = None
    for model in candidates:
        try:
            kwargs = {"model": model, "messages": messages, "max_tokens": max_tokens, "timeout": 15}
            if model.startswith("ollama/"):
                kwargs["api_base"] = OLLAMA_BASE
            resp = completion(**kwargs)
            return resp["choices"][0]["message"]["content"]
        except Exception as e:
            last_err = e
            continue

    raise RuntimeError(f"All model backends failed. Last error: {last_err}")

