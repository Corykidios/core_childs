# The Watcher - Night & Light

The dyad. Night is the always-on governor; Light is the on-demand developer.
Both build on the clipboard-relay pattern proven in `call_of_core`: any AI,
on any platform, that can output a fenced ```tag ... ``` block can trigger
real local actions, no platform tool-support required.

See NIGHT_LIGHT_DESIGN.md for the full architecture writeup.

## Quick start

    pip install -r requirements.txt
    copy .env.example .env
    # fill in .env with your own tokens/keys - never paste them into chat

    python night.py     # leave running in the background
    python light.py new "description of a new capability" --tag mytag

## Files

- `watcher_core.py` - generic clipboard-watch + protocol-dispatch engine
- `model_router.py` - local/cloud LLM routing via LiteLLM
- `protocols/mp.py`, `protocols/ua.py` - the two existing protocols, adapted
  from call_of_core to the shared TAG/dispatch(cmd) contract
- `night.py` - always-on: watches, safety-reviews, dispatches
- `light.py` - on-demand: drafts new protocol modules with AI help, shows
  you the code before writing anything

## The jewel tags

Six two-letter tags, one per hexad piece. sn (Sideritis Necklace, Night)
and cd (Crystal Diadem, Light) are live. e, ce, je, 
e are
reserved names for the four elemental pieces, not yet buildable since
those pieces don't exist yet. Full table in NIGHT_LIGHT_DESIGN.md.
