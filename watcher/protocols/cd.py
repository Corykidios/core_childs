"""
protocols/cd.py - The Crystal Diadem. Light's drafting capability, exposed
through the clipboard instead of requiring a manual terminal call.

Named for Light's jewel: Rock Crystal, which "arouses holy fire from
dried wood" - sparks something dormant into being. Fitting: this is the
protocol that sparks a brand new protocol into existence.

Two actions, deliberately mirroring the "do it twice to mean it" pattern
Night already uses for flagged blocks:

  draft   - generate code for a new protocol and return it on the
            clipboard for review. Nothing is written to disk.
  write   - given the exact same tag + description as a prior draft call,
            actually write protocols/<tag>.py.

This keeps Light's core safety property even when triggered remotely: a
human still has to see the code and deliberately ask for it twice before
anything touches disk. Every block dispatched through Night - including
this one - also still passes through Night's own SAFE/FLAG review first;
this file does not bypass that.
"""

import os
import re
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_WATCHER_DIR = os.path.join(_THIS_DIR, "..")
if _WATCHER_DIR not in sys.path:
    sys.path.insert(0, _WATCHER_DIR)

TAG = "cd"

_last_draft = {"tag": None, "description": None, "code": None}


def dispatch(cmd):
    action = cmd.get("action", "draft").lower().strip()
    tag = (cmd.get("tag") or "").lower().strip()
    description = cmd.get("description", "").strip()

    if action == "draft":
        if not tag or not description:
            return "[CD ERROR] draft requires 'tag' and 'description' fields"
        if not re.match(r"^[a-z][a-z0-9_]*$", tag):
            return f"[CD ERROR] tag must be lowercase, start with a letter: got {tag!r}"

        target = os.path.join(_THIS_DIR, f"{tag}.py")
        if os.path.exists(target):
            return f"[CD ERROR] protocols/{tag}.py already exists - pick a different tag"

        try:
            import light
            code = light.draft(tag, description)
        except Exception as e:
            return f"[CD ERROR] Drafting failed: {type(e).__name__}: {e}"

        _last_draft["tag"] = tag
        _last_draft["description"] = description
        _last_draft["code"] = code

        confirm_hint = (
            '{"action": "write", "tag": "' + tag + '", "description": "' + description + '"}'
        )
        return (
            f"[CD DRAFT] protocols/{tag}.py\n\n{code}\n"
            f"[CD] Nothing written yet. To save this exact draft, send:\n  {confirm_hint}"
        )

    elif action == "write":
        if (_last_draft["tag"] != tag or _last_draft["description"] != description
                or _last_draft["code"] is None):
            return ("[CD ERROR] No matching draft pending. Call 'draft' first with the "
                    "exact same tag and description, then 'write' to confirm.")

        target = os.path.join(_THIS_DIR, f"{tag}.py")
        if os.path.exists(target):
            return f"[CD ERROR] protocols/{tag}.py now exists (created elsewhere?) - not overwriting"

        with open(target, "w", encoding="utf-8") as f:
            f.write(_last_draft["code"])

        _last_draft["tag"] = None
        _last_draft["description"] = None
        _last_draft["code"] = None

        return (
            f"[CD WRITTEN] protocols/{tag}.py saved.\n"
            f"Register it in night.py by adding:\n"
            f"  from protocols import {tag} as {tag}_protocol\n"
            f"  watcher_core.register({tag}_protocol.TAG, {tag}_protocol.dispatch)"
        )

    else:
        return f"[CD ERROR] Unknown action: {action!r}\n  Valid: draft | write"
