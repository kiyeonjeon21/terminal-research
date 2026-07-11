# Synthesis — What terminals do with command structure, and where agents fall out

> The conclusion of the shell-integration and control-API investigation
> (experiments 001–007). Every claim traces to a cited experiment; those cite
> source `file:line` in the four studied terminals (Ghostty, WezTerm, Kitty,
> tmux). Facts vs. interpretation are kept separate throughout.

## Thesis

**Modern terminals compute command structure but never keep it, and they get it
only from an interactive human's prompt cycle — so for a coding agent, running
commands non-interactively, that structure does not exist.** Even the terminals'
own control APIs, which do let a program drive them, expose reconstructed output
but no command exit code. The agent-native opportunity is therefore narrow and
specific: a *uniform, structured, event-driven* surface that retains and pushes
`command → output → exit code`, which no terminal offers today.

This held across four independently-built terminals (Zig / Rust / C / C),
approached from three different directions that all landed on the same gap.

## The research arc

Two axes, seven experiments:

**Shell-integration axis — how terminals handle OSC 133 / OSC 7:**
- [001](experiments/001-command-boundary/) — Ghostty: no durable command record; grid tags + lazy reconstruction.
- [002](experiments/002-command-model/) — WezTerm/Kitty/tmux: same design; exit codes dropped or kept as a transient scalar; tmux even *reverted* a richer version (`6fd9987`).
- [005](experiments/005-cwd-tracking/) — cwd: shell-escape (OSC 7) vs OS process inspection; four different policies.
- [006](experiments/006-shell-emitters/) — the emitter scripts: every marker is gated behind an interactive shell + a prompt hook.
- [003](experiments/003-osc133/) — empirical: PTY capture proving the interactive-only claim on the wire.

**Control-API axis — what a program can drive:**
- [007](experiments/007-control-api/) — Ghostty ≈ none; Kitty RPC (pull); WezTerm cli/Lua/codec (hybrid); tmux control mode (push).

## The four findings

Full write-ups in [comparisons/agent-opportunities.md](comparisons/agent-opportunities.md).

### #1 — No terminal keeps a durable command record
Across all four, the only durable command-boundary artifact is a **≤2-bit
semantic tag on the grid** (Ghostty `page.zig:2072`, WezTerm
`wezterm-cell/src/lib.rs:211`, Kitty `line.h:84`, tmux `tmux.h:805-806`).
Command identity, output ranges, and exit codes are reconstructed on demand
(Ghostty `selectOutput`, Kitty `find_cmd_output`, tmux copy-mode scan, WezTerm
lazy zone cache) or discarded. _(Exp 001, 002.)_

### #2 — "cwd" is not one fact; each terminal collapses its provenance
All four parse OSC 7 but disagree on trusting it vs. reading the OS process cwd —
a spectrum **Ghostty (shell-only) → WezTerm → Kitty → tmux (process-only)**. cwd
has provenance (shell-reported vs OS-observed) and confidence (at-prompt vs
mid-command; local vs remote); every terminal flattens it to one string with a
different policy. _(Exp 005.)_

### #3 — The markers require an interactive human prompt
The OSC 133 / OSC 7 markers come from the shell's integration scripts, which all
hard-guard on an interactive shell (`ghostty.bash:19`, `kitty.bash:3`,
`wezterm.sh:27`) and bind every marker to a prompt hook. A non-interactive
command — `bash -c`, an agent-spawned shell — emits **nothing**. Confirmed on the
wire: the same `echo hello` yields a full `D→A…B…C` cycle interactively but
exactly `hello\r\n` under `bash -c`. So for agent-run commands the structure is
not merely unretained — it is **never produced**. _(Exp 006, 003.)_

### #4 — A control surface exists, but it's a patchwork that still withholds the exit code
Three of four expose a drivable API, split across two interaction models — Kitty
**pulls** (RPC, poll), tmux **pushes** (`%output` firehose + structural events),
WezTerm is hybrid, Ghostty has ~none. Command *output* is reachable everywhere
(Kitty `get-text last_cmd_output` cleanest; tmux raw bytes; WezTerm Lua zones),
but **no API exposes a command's exit code**. The same gap, from a third
direction. _(Exp 007.)_

## Cross-cutting observations

- **Convergence from three directions.** Consumption (001/002), production
  (006/003), and the control API (007) independently reveal the same missing
  piece: a retained, queryable `command → output → exit code` record. That it
  recurs regardless of vantage point is the strongest signal in this repo.
- **The exit code is treated as UI ephemera.** OSC 133;D carries it; Ghostty
  fires a notification and drops it, Kitty keeps a last-value scalar, WezTerm
  discards it in an empty match arm, tmux never parses it. No terminal joins it to
  the output it belongs to.
- **De-facto standardization by copying.** The four share the FinalTerm OSC 133 +
  OSC 7 protocol, the `kitty-shell-cwd://` scheme, and even the same bundled
  `bash-preexec.sh` — convergent design without a formal standard.
- **Pull vs push already exists in the wild.** tmux control mode's `%output`
  stream is the closest thing to an agent-native event bus that ships today; it
  just carries no semantic layer. Kitty brings the complementary strengths: a
  machine-readable command schema and a real security model.

## The design brief that falls out

_(Interpretation — the payoff.)_ An agent-native terminal does **not** start from
zero. The pieces exist, uncombined:

1. **Retain the join** — keep a durable `command → input → output range → exit
   code → duration` record instead of computing boundaries and throwing them
   away. (Fills #1/#2. See [ideas/structured-terminal.md](ideas/structured-terminal.md).)
2. **Produce it without a prompt** — mark command boundaries for non-interactive /
   programmatic execution, so an agent's commands are visible. (Fills #3.)
3. **Expose it on a push channel** — a typed, gated, event-driven API
   (`command.start / output / end{exit_code}`) modeled on **tmux's push** +
   **Kitty's schema and security**. (Fills #4. See
   [ideas/terminal-protocol.md](ideas/terminal-protocol.md).)

The whole value-add is putting the structure every terminal already computes onto
a channel an agent can actually use.

## Scope — the agent conclusion vs. the breadth study

The thesis above is about the **agent axis**. Separately, the technical-core axes
(design-space breadth, weaker agent relevance) were studied for general terminal
understanding — see the `comparisons/` docs, now filled:

- **Parser** (`comparisons/parser.md`) — 3 of 4 implement the Paul Williams vt500
  state machine; the natural home for any new agent-native escape sequence.
- **Rendering** (`comparisons/rendering.md`) — GPU rasterizers vs tmux writing
  escapes to an outer tty; glyph atlas, shaping, damage tracking.
- **Architecture** (`comparisons/architecture.md`) — how the pieces compose; the
  multiplexer split drives the rest.
- **Multiplexing / session model** (`comparisons/multiplexing.md`) — server-owns-
  PTYs persistence (tmux, WezTerm mux) vs GUI-with-tabs (Kitty, Ghostty).
- **Input / keyboard** (`comparisons/input.md`) — legacy ambiguity → the Kitty
  keyboard protocol; mouse/paste/focus modes.
- **Graphics** (`comparisons/graphics.md`) — Kitty graphics vs Sixel vs iTerm2.

Empirical follow-ups, now done:
- experiment [008](experiments/008-control-api-live/) — drives **tmux control
  mode** live (the `%output` push stream), confirming exp 007 on the wire. (kitty
  `@` needs a GUI; wezterm not installed — both source-verified in exp 007.)
- experiment [009](experiments/009-raw-mode-tui/) — captures a real TUI (vim/less)
  flipping the PTY to **raw mode** + the **alternate screen** + the DEC input
  modes, mirroring exp 004's cooked default.

Remaining nice-to-haves: capturing a live SGR **mouse** report and the **Kitty
keyboard protocol** handshake; driving kitty `@` / wezterm `cli` on a machine that
has them running.

(experiment [004](experiments/004-pty-tracing/) empirically traces PTY traffic —
echo/line-discipline, escape sequences on the wire, and `TIOCSWINSZ`→SIGWINCH
resize.)

## Method & reproducibility

Source reading over docs; execution paths traced, not files summarized; exact
`file:line` citations; facts separated from assumptions (per
[AGENTS.md](AGENTS.md)). Cloned projects under `projects/` are kept unmodified
(gitignored). The one empirical experiment ([003](experiments/003-osc133/)) ships
a `harness.py` — reproduce with `python3 harness.py`.
