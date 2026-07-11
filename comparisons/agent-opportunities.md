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

## Finding #2 — "cwd" is not one fact; each terminal collapses its provenance

**Evidence:** `../experiments/005-cwd-tracking/`. All four terminals parse OSC 7,
but disagree on whether to trust it — a spectrum from shell-trusting to
OS-trusting:

| Terminal | Authoritative cwd source | Process-cwd fallback |
| --- | --- | --- |
| Ghostty | shell escape only (OSC 7 / OSC 1337) | no |
| WezTerm | OSC 7 primary, else process | yes (`localpane.rs:1061`) |
| Kitty | process default; OSC 7 only at prompt & not remote (`window.py:166`) | yes |
| tmux | OS process inspection only (`osdep_get_cwd`) | yes (authoritative) |

**The pattern:** cwd has **provenance** (shell-reported vs OS-observed) and
**confidence** (at-prompt vs mid-command; local vs remote) — Kitty's gating logic
is precisely an attempt to reason about that confidence. Yet every terminal
exposes cwd as a single lossy string and picks a different policy for resolving
it.

### Why it matters for coding agents
An agent needs a *reliable* cwd, and each policy fails differently: OSC 7 needs
shell integration and is stale mid-command; process inspection races on the
foreground process and can't see through ssh. An agent can't tell which it's
getting. **Opportunity:** expose cwd *with* provenance + confidence (e.g.
`{path, source: shell|os, at_prompt: bool, remote: bool}`) instead of one string
— cheap to add (the terminal already computes all of it) and directly useful.

## Finding #3 — the markers require an interactive human prompt (agent commands are invisible)

**Evidence:** `../experiments/006-shell-emitters/`. The OSC 133 / OSC 7 signals
that Findings #1 and #2 are about don't originate in the terminal — the shell
emits them, via the integration scripts each terminal ships. Every one of those
scripts (Ghostty, Kitty, WezTerm × bash/zsh/fish) does two things:

1. **hard-guards on an interactive shell** — `ghostty.bash:19`, `kitty.bash:3`,
   `wezterm.sh:27`, and the zsh/fish equivalents; and
2. **binds every marker to a prompt hook** — `precmd`/`PROMPT_COMMAND` (A, D,
   OSC 7), `preexec`/`PS0` (C).

**The consequence:** a command run non-interactively — `bash -c "…"`, or an agent
spawning a shell without an interactive prompt — fires **zero** markers. No
prompt cycle, nothing emitted.

**Empirically confirmed** in `../experiments/003-osc133/`: the same integration +
same `echo hello`, captured off a real PTY, yields the full `D→A…B…C` marker
cycle interactively but exactly `hello\r\n` (zero markers) under `bash -c`. The
real `kitty.bash`/`ghostty.bash` guards trip identically when sourced
non-interactively.

### Why this reframes Findings #1 and #2
Those findings were about the terminal not *retaining* structure. This is deeper:
for agent-run commands the structure is **never produced**. The entire
command-boundary + cwd apparatus is downstream of a human typing at a prompt;
remove the prompt and the terminal sees the same undifferentiated byte stream a
coding agent sees today.

**Opportunity:** the gap is *production*, not just retention. An agent-native
design would either (a) emit command structure for **non-interactive /
programmatic** execution (a marker protocol that doesn't depend on a prompt
cycle), or (b) let the agent **drive terminal state directly** rather than
depending on shell prompt hooks. See `../ideas/structured-terminal.md` and
`../ideas/terminal-protocol.md`.

## Notes
- Closest existing surface today: WezTerm's Lua `get_semantic_zones` /
  `get_text_from_semantic_zone` and Kitty's `@ get-text` output selectors — but
  both recompute geometric regions from grid tags and carry **no exit code and
  no command identity**. They are reconstruction helpers, not a command store.
- Open threads: OSC 7 (cwd) coverage, and whether any IPC layer (WezTerm mux,
  Kitty remote control) could carry retained command records.
