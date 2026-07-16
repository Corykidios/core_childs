"""
protocols/sn.py - The Sideritis Necklace. Night's own self-introspection.

Named for Night's jewel: the "Speaking Stone," which grants accurate
prophecies to those bold enough to listen. Fittingly, this is Night
reporting on herself - status, recent activity, what's pending.

Pure read of night.log plus whatever state night.py pushes in via
set_state(). No side effects, nothing written.
"""

import datetime
import os

TAG = "sn"

LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "night.log")

_state = {"started_at": None, "pending_tag": None}


def set_state(started_at=None, pending_tag=None):
    """night.py calls this to push live state in, avoiding a circular import."""
    if started_at is not None:
        _state["started_at"] = started_at
    _state["pending_tag"] = pending_tag


def _tail_log(n=10):
    if not os.path.isfile(LOG_PATH):
        return []
    with open(LOG_PATH, encoding="utf-8") as f:
        lines = f.readlines()
    return [l.rstrip("\n") for l in lines[-n:]]


def dispatch(cmd):
    action = cmd.get("action", "status").lower().strip()

    if action == "status":
        uptime = "unknown"
        if _state["started_at"]:
            delta = datetime.datetime.now() - _state["started_at"]
            uptime = str(delta).split(".")[0]
        pending = _state["pending_tag"] or "(none)"
        return (
            "[SN STATUS] Night is watching.\n"
            f"  Uptime: {uptime}\n"
            f"  Pending confirmation: {pending}"
        )

    elif action == "recent":
        count = int(cmd.get("count", 10))
        lines = _tail_log(count)
        if not lines:
            return "[SN RECENT] (log is empty or not found yet)"
        return "[SN RECENT]\n" + "\n".join(f"  {l}" for l in lines)

    elif action == "flagged":
        count = int(cmd.get("count", 10))
        lines = [l for l in _tail_log(500) if "FLAGGED" in l or "CONFIRMED" in l][-count:]
        if not lines:
            return "[SN FLAGGED] No flags in recent history."
        return "[SN FLAGGED]\n" + "\n".join(f"  {l}" for l in lines)

    else:
        return f"[SN ERROR] Unknown action: {action!r}\n  Valid: status | recent | flagged"
