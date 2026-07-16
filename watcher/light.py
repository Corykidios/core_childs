"""
light.py - The on-demand developer.

Not a background service - run this when you want to add a new protocol
to the watcher system (a new ```tag ... ``` block type Night and Light
both understand). It asks a strong model to draft a new protocols/<tag>.py
file following the same contract as mp.py and ua.py, shows the draft
before anything is written, and only saves it once you say yes.

Usage:
    python light.py new "reads a local file and returns its text content" --tag file

This does NOT touch git or push anything, and does NOT auto-register the
new protocol into night.py - it prints the two lines to add by hand.
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import model_router

PROTOCOLS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "protocols")

DRAFT_SYSTEM_PROMPT = """You write Python protocol handler modules for a clipboard-watcher system. Every handler module must define exactly:

  TAG = "<tag>"                   # the fence language, e.g. "file"
  def dispatch(cmd: dict) -> str:  # cmd is the parsed JSON from the block;
                                     return a short human-readable result string

Conventions to follow exactly:
- No top-level side effects on import (no network calls, no file I/O at import time).
- dispatch() should validate cmd.get("action") and return a clear
  "[<TAG> ERROR] ..." string for anything invalid, rather than raising.
- Keep dependencies to the Python standard library unless the task clearly
  needs something else (e.g. requests for an HTTP call) - if so, say what
  to add to requirements.txt in a comment at the top of the file.
- Output should be plain text formatted for a human to read after pasting
  from the clipboard, not JSON.

Respond with ONLY the Python file contents. No explanation, no markdown fences, just the code."""


def draft(tag, description):
    prompt = f'Tag: "{tag}"\nWhat this protocol should do: {description}'
    code = model_router.ask(DRAFT_SYSTEM_PROMPT, prompt, prefer="smart", max_tokens=1200)
    code = re.sub(r"^```(?:python)?\s*", "", code.strip())
    code = re.sub(r"```\s*$", "", code)
    return code.strip() + "\n"


def main():
    parser = argparse.ArgumentParser(description="Draft a new watcher protocol.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    new_p = sub.add_parser("new", help="Draft a new protocol handler")
    new_p.add_argument("description", help="Plain-language description of what it should do")
    new_p.add_argument("--tag", required=True, help="Fence tag, e.g. ''file''")

    args = parser.parse_args()

    if args.cmd == "new":
        tag = args.tag.lower().strip()
        if not re.match(r"^[a-z][a-z0-9_]*$", tag):
            print(f"Tag must be lowercase, start with a letter: got {tag!r}")
            sys.exit(1)

        target = os.path.join(PROTOCOLS_DIR, f"{tag}.py")
        if os.path.exists(target):
            print(f"protocols/{tag}.py already exists - pick a different tag.")
            sys.exit(1)

        print(f"Drafting protocols/{tag}.py ...\n")
        code = draft(tag, args.description)
        print("=" * 70)
        print(code)
        print("=" * 70)

        answer = input(f"\nWrite this to protocols/{tag}.py? [y/N] ").strip().lower()
        if answer == "y":
            os.makedirs(PROTOCOLS_DIR, exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(code)
            print("Written. Register it by adding to night.py:")
            print(f"  from protocols import {tag} as {tag}_protocol")
            print(f"  watcher_core.register({tag}_protocol.TAG, {tag}_protocol.dispatch)")
        else:
            print("Discarded - nothing written.")


if __name__ == "__main__":
    main()
