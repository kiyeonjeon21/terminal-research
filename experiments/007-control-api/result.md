# Result — 007-control-api

> New axis: the terminal's own programmatic control surface. Facts cite
> `file:line` (under `../../projects/`); interpretation marked _(interpretation)_.

## Answer

**A build-on surface does exist — for three of the four — but it's a patchwork,
split across two interaction models, and none of them closes the
command→output→exit-code gap.**

- **Ghostty** — essentially nothing. Its whole IPC is `new_window` +
  `toggle_quick_terminal` (`src/apprt/ipc.zig:56-64`); the rest of the CLI is
  config introspection. An agent can open a window and nothing else.
- **Kitty** — a real RPC: `kitty @` over a DCS escape or a socket, with
  `send-text` (input), `run` (exec + capture off-screen), `ls` (state),
  `signal-child`, and `get-text --extent last_cmd_output` (fetches a command's
  output via OSC-133 marks). **Request/response only — poll for changes.** Best
  security model of the four (per-command password scoping + AES-GCM).
- **WezTerm** — three surfaces: `wezterm cli` (external, one-shot, unix/TLS/SSH),
  Lua (in-process, richest — the only path to `get_semantic_zones`), and the
  codec protocol (a persistent client gets *pushed* render deltas + user-var
  alerts). Command structure is reachable only from Lua, not from the cli.
- **tmux** — the outlier and, for an agent, the most interesting: **control mode
  (`-CC`) pushes a live `%output` firehose of every pane's bytes**
  (`control.c:575`) plus structural `%…` events and `%begin/%end` command
  framing. No polling — the controller *watches* the session.

## The two axes

### 1. Pull vs. push
Kitty is **pull** (RPC, poll). tmux is **push** (event stream). WezTerm straddles
(one-shot cli + a persistent codec client that receives pushed deltas + in-proc
Lua events). Ghostty has neither.

_(interpretation)_ **tmux's `%output` stream is the closest thing to an
agent-native event bus that already ships** — a program outside the terminal
receives every byte and every structural change as it happens. That is exactly
the shape an agent wants; tmux just doesn't put any *semantic* layer on top of
the raw bytes.

### 2. The command→exit-code gap reappears from the API side
Experiments 001/002/006 found the terminal never retains a command record, and
the shell only emits markers interactively. This experiment asks whether the
*control API* recovers it. Result:
- **Output**: reachable — Kitty `get-text last_cmd_output` (cleanest), tmux
  `%output` (raw, re-parse OSC 133 yourself), WezTerm (Lua zones only).
- **Exit code**: exposed by **none**. Kitty tracks `last_cmd_exit_status` but
  omits it from `get-text`; tmux discards `133;D`; WezTerm discards it.

So even the richest control surface hands an agent, at best, *reconstructable
output* and no clean exit code — the same structural gap as the shell-integration
axis, now confirmed from the API direction too.

## Why it matters (interpretation)

_(interpretation)_ This reframes the whole arc's payoff. An agent-native terminal
is **not** starting from zero: Kitty's RPC (with a machine-readable schema and a
real security model), tmux's `%output` push stream, and WezTerm's cli+Lua are
concrete, shippable prior art. The missing piece is narrow and specific: a
**uniform, structured, event-driven** surface that pushes `command.start`,
`command.output`, `command.end{exit_code}` — combining tmux's push model, Kitty's
schema/security, and the OSC-133 structure everyone already computes but no API
fully exposes. See `../../ideas/terminal-protocol.md` and
`../../comparisons/agent-opportunities.md` (Finding #4).

## Open questions / next
- Empirically drive each API (`kitty @`, `wezterm cli`, `tmux -CC`) in a PTY
  harness like exp 003 — confirm the capabilities and the exit-code gap live.
- WezTerm named events (`user-var-changed`, `augment-command-line`) — locate the
  emit sites in `wezterm-gui`.
- Does any third-party tool already bolt a structured layer onto tmux `%output`?
