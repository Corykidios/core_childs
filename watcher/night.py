"""
night.py - The always-on governor.

Watches the clipboard the same way the original call_of_core watcher did,
but adds one thing before dispatching anything: a fast safety-review pass
through model_router. Most blocks pass through instantly and silently -
this isn''t meant to add friction to routine mp/ua calls. It exists for the
rare block that looks like it''s asking to do something destructive,
exfiltrate a secret, or otherwise deserves a second look before it fires.

Flagged blocks aren''t silently blocked - they surface a local notification
explaining the concern, get logged, and require the exact same block to be
copied a second time to actually run (deliberate confirmation, not a
permanent block).

Run this once, leave it running. Ctrl-C to stop.
"""

import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import watcher_core
import model_router
from protocols import mp as mp_protocol
from protocols import ua as ua_protocol

LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "night.log")

REVIEW_SYSTEM_PROMPT = (
    "You are a fast safety reviewer for a personal automation watcher. "
    "You will see a JSON command about to be dispatched to a tool (memory "
    "storage/search, or local knowledge-graph queries). Almost everything "
    "you see is routine and safe. Respond with exactly one word: SAFE or "
    "FLAG. Only respond FLAG if the command looks like it could delete "
    "data irreversibly and unexpectedly, exfiltrate secrets, or otherwise "
    "cause harm beyond what its stated action implies. When genuinely "
    "unsure, prefer SAFE - this is a low-stakes personal tool, not a "
    "production system, and false alarms erode trust in the review step."
)

_pending_confirmation = {"raw": None}


def _log(line):
    ts = datetime.datetime.now().isoformat(timespec="seconds")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {line}\n")


def _notify(title, message):
    try:
        from plyer import notification
        notification.notify(title=title, message=message, timeout=10)
    except Exception:
        pass  # convenience only - the log file is the source of truth


def review(tag, cmd, raw):
    """review_fn contract: (tag, cmd, raw) -> (allowed: bool, reason: str)"""
    try:
        verdict = model_router.ask(
            REVIEW_SYSTEM_PROMPT,
            json.dumps({"tag": tag, "command": cmd}),
            prefer="fast",
            max_tokens=5,
        ).strip().upper()
    except Exception as e:
        _log(f"REVIEW UNAVAILABLE ({e}) - passed through: {tag} {raw[:80]}")
        return True, ""

    if "FLAG" in verdict:
        if _pending_confirmation["raw"] == raw:
            _log(f"CONFIRMED after flag: {tag} {raw[:120]}")
            _pending_confirmation["raw"] = None
            return True, ""

        _pending_confirmation["raw"] = raw
        _log(f"FLAGGED: {tag} {raw[:120]}")
        _notify(
            "Night - review flagged",
            f"A {tag} block was flagged and not run. Copy it again to confirm.",
        )
        return False, "Flagged for review - copy the same block again to confirm and run it."

    _log(f"safe: {tag} {raw[:80]}")
    return True, ""


def main():
    watcher_core.register(mp_protocol.TAG, mp_protocol.dispatch)
    watcher_core.register(ua_protocol.TAG, ua_protocol.dispatch)
    watcher_core.watch(on_fire_label="Night", review_fn=review)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nNight stopped.")
