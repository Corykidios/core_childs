# Core Childs — Project State

*A living snapshot. Rewrite as things change; git history is the record of how we got here.*

## What this is
Core Childs is the repo for Core — the persona/collaborator identity Cory built within We Tiripodiko, his worldbuilding + software infrastructure project. Distinct from Mini Meri (ChatGPT-resident) and the two Eternal Seekers (Light = Cory's in-story analog; Night = ChatGPT persona). Core never appears in-story — dev-space only, the "kernel" paradigm underlying everything, Cory's stated main collaborator/partner.

## The hexad: six functional roles
Hexad = tetrad (4 elemental) + dyad (2, light/night). Planned as separate lightweight Docker containers, using Compose profiles so people install/run only what they need.

### Tetrad — built by synthesizing existing repo ecosystems
| Element | Settler | Role | Status |
|---|---|---|---|
| Fire | Coru | GitHub commander | Research phase — see `hob_hup_mcp` below |
| Air | Cori | Letta agent-file (self-editing memory) | Not started |
| Earth | Cora | Quick-summon Core (portable seed-prompt, any high-context AI) | Open brainstorm |
| Water | Coro | Discord/Telegram/WhatsApp poobah, specifically the Eliza OS framework | Research needed — crypto/DAO entanglement flagged, framework must be separated from token layer |

### Dyad — built from scratch
| Pole | Role | Container | Status |
|---|---|---|---|
| Night | Watcher-script governor (security/safety review) | Always-on | Built — see `watcher/`. Local syntax + live dispatch tested; local Ollama model (qwen3.5:9b) currently OOMs on this machine, falls through to cloud (needs an API key set in .env) |
| Light | Watcher-script developer (module-builder) | On-demand | Built — see `watcher/light.py`. Drafts new protocol modules via LLM, requires manual y/n confirmation before writing, does not auto-register |

## Jewelry / visual reference (narrative use)
- Light: crown chain + forehead-gem pendant, white
- Night: necklace, black
- Fire/GitHub: red earring, upper right ear
- Earth/quick-summon: green earring, lower right ear
- Air/Letta: yellow earring, upper left ear
- Water/Eliza-OS: blue earring, lower left ear

## GitHub commander — research notes
Approach: neither the official GitHub SDK nor building from absolute scratch — research and synthesize a small set of purpose-built tools.

**hob_hup_mcp** (github.com/Corykidios/hob_hup_mcp) — Cory's own earlier prototype, from an attempt to build all four elemental-zone tools as "god-tier, minimalist, all-encompassing MCP" servers. Single-file Python MCP server, 10 tools: `fs`, `shell`, `search`, `project`, `task` (general local dev-agent) plus `repo`, `repo_file`, `issue`, `branch_pr` (GitHub-specific, thin wrapper, PAT-based auth via `.env`). Strong candidate to revive/trim rather than start from zero — already validates "thin purpose-built tools, not a bulky SDK."

Auth pattern for this piece: GitHub PAT in a local `.env` file, set by Cory directly on Nyx — never handled in chat.

## Quick-summon Core — open brainstorm, not settled
Roughly increasing sophistication:
1. One long, well-built seed prompt, pasted manually into any sufficiently high-context chat (Cory wants >=256k tokens, ideally ~1M).
2. Seed split into files (identity/voice/relationships/current-state), concatenated by a small script.
3. Script assembles and fires the seed at a chosen backend automatically (using Cory's free/high-limit API keys).
4. Script pulls current state live from this repo each time, rather than a frozen local copy — the "soul" concept made operational, not just metaphorical.
5. Speculative: two-way connection back into the watcher script.

Prior art worth studying: "character card" formats from SillyTavern-adjacent ecosystems. Cory has direct experience here — ran SillyTavern, built an improved fork called **Luker**, part of an intentional "L" naming family alongside Letta.

## Technical patterns established so far
- **Docker:** selective startup via `docker compose up <service>` or **profiles** — install everything, run only what's needed. Learned the hard way: the `protocore` stack (~10 containers incl. Neo4j+pgvector+Qdrant simultaneously) overwhelmed Cory's 16GB/no-GPU laptop. Lesson: right-size to hardware; make selective startup a first-class feature. Small lightweight scripts (like the watcher dyad) are fine to split into separate containers — the lesson was about redundant *heavy* services, not container count.
- **Version pinning:** for any wrapped official platform (e.g. Letta server + Postgres/pgvector + pgAdmin), pin image versions explicitly rather than `:latest`.
- **Credentials:** never handled in chat. GitHub auth for this repo and `the_liminaria` uses `git config --global credential.helper manager` (OAuth via browser, stored by Windows). Any PAT-based tool (like `hob_hup_mcp`) needs its `.env` set up by Cory directly on the machine.
- **Local repo convention:** all cloned repos live under `C:\git\<repo-name>` on Nyx.

## Related repos
- `the_luminaria` — Core's home-base AI platform (pixel-art GUI), not yet started.
- `the_liminaria` — "Esoterica for all!", ancient-language source-text library (Orphic Lithica underway), `sources/orphic-lithica.md` placeholder live.
- `hob_hup_mcp` — prototype GitHub/dev-agent MCP server, candidate for the GitHub-commander piece.

## Content structure for Core herself (Sidekick Holon)
Seven planetary blocks total; two are foundational:
- **Sun block** (exemplar response): one idealized response that *shows* the character — voice, format, length, narrative approach, all at once.
- **Venus block** (strand analysis): the *telling* equivalent. Three sections x two subjects x two strands = 12 strands:
  - Outer: Appearance (Figure, Fashion), Activity (Movement, Mannerisms)
  - Inner: Voice (Wordcraft, Wit), Values (Beliefs, Bearings)
  - Intra/Inter: Context (Origin, Occupation), Connection (Demeanor, Dynamics)
  - Braiding principle throughout: strands integrate into shared sentences rather than listing separately.

A character is fully "seated" once Sun + Venus exist together — the seed crystal. Core's own Sun/Venus blocks haven't been formally written yet.


