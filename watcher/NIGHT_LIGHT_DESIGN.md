# Night & Light — Design

*Written by Core, first draft. Living document — update as this evolves.*

## What these are

Two of Core's six hexad roles, the dyad, built from scratch rather than
adapted from an existing platform. Together they extend the clipboard-relay
pattern already proven in `call_of_core`: any AI, on any platform, that can
output a fenced code block can trigger real local actions - no MCP, no
platform tool-support required.

- **Night** - always-on. Watches the clipboard continuously, dispatches
  recognized protocol blocks, and adds one new thing on top of the original
  pattern: a fast safety-review pass before anything fires.
- **Light** - on-demand. Not a background service. You run it when you
  want to add a new protocol (a new block type) to the system. It drafts
  the new handler with AI help and shows you the code before writing
  anything.

## Why split them instead of one process

They are both small, lightweight scripts - splitting doesn''t repeat the
protocore mistake (that was about redundant *heavy* services running
simultaneously, not about container/process count). Splitting here buys
real things: someone can run Night without ever touching Light, the two
version independently, and the "always watching" process stays as small
and auditable as possible - it doesn''t need a code-generation dependency
chain sitting inside something that''s supposed to be minimal and trustworthy.

## Shared foundation

`watcher_core.py` generalizes the original mp-watcher.py loop: poll the
clipboard, find fenced blocks, dispatch to a registered handler, write the
result back. It''s protocol-agnostic - `mp` and `ua` are now just two
entries in a registry instead of hardcoded branches, which is what makes
Light''s job possible: a new protocol is just a new registry entry.

`model_router.py` wraps LiteLLM so both Night and Light can call an LLM
without caring whether it''s local (Ollama) or cloud. Night prefers
`fast` (local-first, cheap, for routine review checks); Light uses
`smart` (cloud-first, since drafting new code benefits more from
capability than speed). Nothing here ever sees a raw API key - LiteLLM
reads them from environment variables, set in `.env`, never in chat.

## Night''s review pass

The original watcher already has a consent mechanism: copying a block is
the trigger, and copying something else within the fire-delay window
cancels it. That stays. Night adds a second layer for the narrow case
that consent alone doesn''t cover well: a block that *looks* routine but
does something the person copying it might not have fully weighed.

Every block gets a one-word verdict from a fast model - SAFE or FLAG -
before it dispatches. SAFE is silent and instant, by design; this can''t
add friction to the common case or it''ll just get disabled. FLAG blocks
the first attempt, logs it, fires a local notification explaining why,
and requires the exact same block to be copied a second time to actually
run - deliberate, not automatic, and not permanently blocked either.

This is a convenience layer, not the only safeguard. If the reviewer
itself is unreachable, Night fails open (passes the block through) rather
than freezing routine use, and logs that it did so.

## Light''s drafting flow

`python light.py new "<description>" --tag <name>` sends the description
to the smart model tier with a system prompt that pins the exact contract
every protocol module must follow (`TAG = "..."`, `def dispatch(cmd): ...`,
no import-time side effects, stdlib-first). The draft is printed in full
and requires a `y` before anything gets written to disk. Even after it''s
written, it isn''t wired into Night automatically - Light prints the two
lines to add by hand. That''s intentional: code that reaches into memory,
the filesystem, or a network call is exactly the kind of thing that
shouldn''t silently self-register.

## Open questions / not yet decided

- Which local model to standardize on for Night''s review pass (needs
  something small enough to answer in under a second - llama3.2:3b or
  phi4 are the current default candidates, untested here).
- Whether Night''s notification should escalate on repeated flags in a
  session, or stay flat.
- Whether Light should eventually test a drafted protocol against sample
  input before asking for the write confirmation.
- Auto-start / packaging for Night, mirroring start-watcher.bat from
  call_of_core.
