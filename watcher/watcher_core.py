"""
watcher_core.py - Shared clipboard-watching + protocol-dispatch engine.

The generic engine both night.py and light.py build on. It knows nothing
about MemoryPlugin or Understand-Anything specifically - it just:
  1. Polls the clipboard for fenced `<tag> ... ` blocks
  2. Looks up a registered handler for each tag
  3. Dispatches, collects results, writes them back to the clipboard

Protocol handlers live in protocols/ and register themselves by calling
register(tag, dispatch_fn).

Extracted from the original call_of_core/mp-watcher.py pattern - same
cancel-window UX, same clipboard-diffing, generalized to N protocols
instead of two hardcoded ones.
"""

import datetime
import json
import re
import time

import pyperclip

POLL_INTERVAL = 0.5
FIRE_DELAY = 2.0

_REGISTRY = {}
_BLOCK_RE_CACHE = {}


def register(tag, dispatch_fn):
    """Register a protocol handler. tag is the fence language (e.g. 'mp')."""
    tag = tag.lower()
    _REGISTRY[tag] = dispatch_fn
    _BLOCK_RE_CACHE[tag] = re.compile(r"`" + re.escape(tag) + r"\s*([\s\S]*?)`", re.IGNORECASE)


def registered_tags():
    return sorted(_REGISTRY.keys())


def find_blocks(text):
    """Return [(tag, raw_json_str), ...] across all registered protocols, in document order."""
    results = []
    for tag, rx in _BLOCK_RE_CACHE.items():
        for m in rx.finditer(text):
            results.append((m.start(), tag, m.group(1).strip()))
    results.sort(key=lambda x: x[0])
    return [(tag, raw) for _, tag, raw in results]


def process(text, review_fn=None):
    """
    Run every detected block through its handler.
    If review_fn is given, called as review_fn(tag, cmd, raw) -> (allowed, reason)
    before dispatch. Night uses this hook for the safety-review pass; leave
    None to skip review entirely.
    """
    results = []
    for tag, raw in find_blocks(text):
        try:
            cmd = json.loads(raw)
        except json.JSONDecodeError as e:
            results.append(f"[{tag.upper()} PARSE ERROR] {e}\n  Raw: {raw[:120]}")
            continue

        if review_fn:
            allowed, reason = review_fn(tag, cmd, raw)
            if not allowed:
                results.append(f"[{tag.upper()} BLOCKED] {reason}")
                continue

        handler = _REGISTRY.get(tag)
        if not handler:
            results.append(f"[{tag.upper()} ERROR] No handler registered for this tag")
            continue

        try:
            results.append(handler(cmd))
        except Exception as e:
            results.append(f"[{tag.upper()} ERROR] {type(e).__name__}: {e}")

    return "\n\n".join(results) if results else None


def watch(on_fire_label="Watcher", review_fn=None, quiet=False):
    """Generic clipboard poll loop. Blocks forever (Ctrl-C to stop)."""
    if not quiet:
        print(f"-- {on_fire_label} watcher -----------------------------------")
        tags_str = ", ".join(registered_tags()) or "(none)"
        print(f"  Registered protocols: {tags_str}")
        print(f"  Poll: {POLL_INTERVAL}s   Fire delay: {FIRE_DELAY}s   Ctrl-C to stop")
        print("  Copy anything else within the fire delay to cancel.")
        print("--------------------------------------------------------------\n")

    try:
        last_seen = pyperclip.paste()
    except Exception:
        last_seen = ""
    last_result = ""

    while True:
        try:
            clip = pyperclip.paste()
        except Exception:
            time.sleep(POLL_INTERVAL)
            continue

        if clip == last_result or clip == last_seen:
            time.sleep(POLL_INTERVAL)
            continue

        last_seen = clip

        if not find_blocks(clip):
            time.sleep(POLL_INTERVAL)
            continue

        ts = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {on_fire_label}: block detected - firing in {FIRE_DELAY:.0f}s (copy anything else to cancel)...")

        cancelled = False
        for _ in range(int(FIRE_DELAY / 0.1)):
            time.sleep(0.1)
            try:
                current = pyperclip.paste()
            except Exception:
                continue
            if current != clip:
                print("  -> Cancelled.\n")
                last_seen = current
                cancelled = True
                break

        if cancelled:
            continue

        result = process(clip, review_fn=review_fn)
        if result:
            ts2 = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"[{ts2}] {on_fire_label}: FIRED")
            print(result[:500] + ("..." if len(result) > 500 else ""))
            print("-> Result on clipboard.\n")
            pyperclip.copy(result)
            last_result = result
            last_seen = result

        time.sleep(POLL_INTERVAL)
