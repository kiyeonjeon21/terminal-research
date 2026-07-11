# Agent-native Terminal Protocol

> Raw idea. No need to be right — capture it before it evaporates.

## The idea
A protocol extension letting an agent query and drive terminal state reliably (command graph, semantic scrollback, snapshots).

## Why it might matter for coding agents
If `structured-terminal.md` says *retain* the command→output→exit-code join,
this is the *access* half: a stable query/drive API so an agent (local or
remote) can ask "give me command N's output", "wait until the current command
ends", "what was its exit code" — without screen-scraping or racing the byte
stream.

## Prior art / closest existing thing
The closest existing query surfaces, both verified in
`../experiments/002-command-model/`:
- **WezTerm Lua** — `pane:get_semantic_zones` /
  `pane:get_text_from_semantic_zone` (`lua-api-crates/mux/src/pane.rs:305-378`).
  Returns geometric regions recomputed from cell tags; **no exit code, no
  command identity**.
- **Kitty remote control** — `@ get-text` output selectors
  (`boss.py:276-283`) route through the `find_cmd_output` mark-scan
  (`screen.c:4522`); same limitation.

Both prove the *access pattern* is wanted (people built query APIs) but expose
only reconstructed geometry, not command records. The protocol gap is a typed,
stable schema over retained command state — plus an event/subscription channel
(`command.start` / `command.end`) so an agent can await completion instead of
polling. See `structured-terminal.md`.

**The full control-surface survey (`../experiments/007-control-api/`) shows the
design pieces already exist, just not combined:**
- **Transport & model** — the pull-vs-push choice is live in the wild. Kitty is
  request/response (poll); **tmux control mode (`-CC`) already *pushes* a
  `%output` stream + structural `%…` events** to an external controller — the
  nearest thing to the event bus this idea wants. A protocol should push, like
  tmux, not force polling like Kitty.
- **Schema & security** — Kitty's remote control has a machine-readable command
  schema (auto-generates a Go client) and the best security model
  (per-command password scoping, AES-GCM, replay guard). That's the template for
  the "typed, stable, gated" part.
- **What's still missing everywhere** — none of the four surfaces exposes a
  command's **exit code**, and command *output* is only reachable by
  reconstruction (Kitty `last_cmd_output`, tmux raw `%output` bytes, WezTerm Lua
  zones). The protocol's whole value-add is putting the retained
  `command→output→exit-code` record (from `structured-terminal.md`) onto a
  tmux-style push channel with Kitty-style schema/security.

## Open questions
- Transport: extend an existing IPC (WezTerm mux, Kitty remote control) or a new
  local socket? What does a headless/remote agent need?
- Schema: is a flat command list enough, or is the "command graph" (nested /
  backgrounded / subshell commands, via OSC 133 `aid`) worth modeling? Note all
  four terminals currently parse-and-ignore `aid`.
- Security: a query API that returns full command output is a capability worth
  gating — who can read another pane's history?
