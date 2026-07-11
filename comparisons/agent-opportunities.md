# Agent Opportunities

> The point of this repo: where could a coding-agent-native terminal do better?

For each idea: what is missing today, which project comes closest, and what a
new design could expose. Link to `../ideas/*` and `../experiments/*`.

## Candidates
- Structured command boundaries & outputs (beyond OSC 133)
- Machine-readable scrollback / semantic events
- Session capture & replay for agents
- A stable programmatic API into terminal state

---

## Finding #1 — No terminal keeps a durable command record

**Evidence:** four independently-built terminals, four languages, one design.
Traced in `../experiments/001-command-boundary/` (Ghostty) and
`../experiments/002-command-model/` (WezTerm, Kitty, tmux).

| Terminal | Durable artifact | Exit code (OSC 133;D) |
| --- | --- | --- |
| Ghostty (Zig) | per-cell + per-row tag (`page.zig:2072`, `:1972`) | surfaced then dropped (`Surface.zig:1128`) |
| WezTerm (Rust) | per-cell 2-bit `SemanticType` (`wezterm-cell/src/lib.rs:211`) | discarded (`performer.rs:900-902`) |
| Kitty (C) | 2-bit per-line `prompt_kind` (`line.h:84`) | transient scalar (`window.py:260`) |
| tmux (C) | 2 line-flag bits (`tmux.h:805-806`) | not handled; reverted (`6fd9987`) |

**The pattern:** every terminal *computes* command boundaries — enough to jump
between prompts and select a command's output — but stores only a **≤2-bit
semantic tag on the grid**. Command identity, output ranges, and exit codes are
reconstructed on demand (Ghostty `selectOutput`, Kitty `find_cmd_output`, tmux
copy-mode scan, WezTerm lazy zone cache) or thrown away.

### Why it matters for coding agents
A coding agent driving a terminal today must **screen-scrape**: it receives a
byte stream and re-derives where each command started, ended, what it output,
and how it exited — exactly the work the terminal already does internally and
then discards. The terminal knows the boundaries; it just never exposes them as
retained, queryable data. There is no API to ask *"what did command N output and
what was its exit code?"*

### The tmux revert is the sharpest evidence
tmux's HEAD (`6fd9987`) reverts `f3c6b4f` "Add formats and events for OSC 133
commands, as well as a -T flag." A durable-records version was built and
**deliberately removed**. So the gap is not an oversight — it is an un-landed
capability. That suggests the opportunity is real but has non-trivial design
cost (config surface, maintenance, spec ambiguity) that a from-scratch
agent-native design could take on directly instead of retrofitting.

### The opportunity
Retain and *join* what the terminal already computes:
`command → input text → output range → exit code → duration`, as a durable,
queryable structure with a stable API (and ideally an event stream). This is
developed in:
- `../ideas/structured-terminal.md` — expose commands/outputs/state as
  structured events instead of a byte stream.
- `../ideas/terminal-protocol.md` — a protocol/query API over that state.

## Notes
- Closest existing surface today: WezTerm's Lua `get_semantic_zones` /
  `get_text_from_semantic_zone` and Kitty's `@ get-text` output selectors — but
  both recompute geometric regions from grid tags and carry **no exit code and
  no command identity**. They are reconstruction helpers, not a command store.
- Open threads: OSC 7 (cwd) coverage, and whether any IPC layer (WezTerm mux,
  Kitty remote control) could carry retained command records.
