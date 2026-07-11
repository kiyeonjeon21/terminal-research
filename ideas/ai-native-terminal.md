# Designing an AI-native terminal

> The capstone idea note: if you built a terminal for coding agents from scratch,
> what would you consider? Grounded in this repo's findings — every point ties to
> a cited experiment. Consolidates `structured-terminal.md` (retain the record)
> and `terminal-protocol.md` (expose it) into one design frame. Facts vs.
> interpretation kept separate; the design itself is interpretation.

## The core reframe — separate *execution/structure* from *display/emulation*

Today a coding agent **screen-scrapes the human's view**. But this repo showed the
terminal computes command structure and then (a) doesn't retain it (#1, exp
001/002), (b) only produces it from an interactive prompt cycle (#3, exp 003/006),
and (c) doesn't expose the exit code even via its control API (#4, exp 007/008).

_(Interpretation.)_ So the central design move is: **an agent needs execution +
structured results, not a rendered cell grid.** Make VT emulation and the cell
grid a *display* concern (for humans), and give the agent a separate execution
layer. Don't make the agent reconstruct structure from the display the terminal
built for eyes.

## Design considerations

### 1. A structured command model — retained, prompt-independent, push+query
The repo's central gap (see `structured-terminal.md`, `terminal-protocol.md`):
- **Retain** a durable `command → input → output range → exit code → duration →
  cwd → timestamps` record — not the ≤2-bit grid tag every terminal keeps today
  (#1).
- **Produce it without a prompt.** `bash -c` has no prompt cycle, so shell
  integration emits nothing (#3 — exp 003 captured exactly `hello\r\n`). The
  terminal must mark boundaries itself (spawn the command → it knows the
  boundaries exactly) or track them at the PTY level, not depend on shell hooks.
- **Both push and query.** tmux `%output` proves push works (exp 008); Kitty RPC
  proves query works (exp 007). Agents need an awaitable `command.end{exit_code}`
  event *and* a "fetch command N's output" call. Kitty's machine-readable schema +
  per-command security is the template.

### 2. Split stdout/stderr on demand
A PTY merges stdout and stderr into one stream (visible as the single byte stream
in exp 004), so an agent can't ask "just the errors." _(Interpretation.)_ When an
agent needs structure, run the command with **separate pipes** (no PTY, or PTY +
side pipes); keep a merged view for the human.

### 3. Human + agent as dual users of one session
- Human: an ordinary terminal — inherit the VT/rendering stack from Part II of
  `../SYNTHESIS.md`.
- Agent: an execution + session-query API.
- The human sees **what the agent ran** as first-class UI objects (status,
  exit badge, foldable output) — a step past the OSC 133 prompt-navigation that
  Ghostty/Kitty/WezTerm already do (`../comparisons/agent-opportunities.md`).

### 4. Persistent server + concurrency
Agents run long tasks, survive disconnects, and fan out parallel commands. The
`../comparisons/multiplexing.md` finding: only a **server that owns the PTYs**
(tmux, WezTerm mux) gives persistence/detach/reattach; single-process GUIs
(Ghostty, Kitty) don't. So an AI-native terminal should be a persistent server —
sessions resumable, multiple clients (agents + humans) attachable, commands
runnable concurrently with structured results per lane.

### 5. Safety, permissions, provenance
An agent driving a terminal is dangerous.
- **Provenance tagging** — mark agent-initiated vs human-initiated actions.
  Bracketed paste (`?2004`, exp 009) exists for exactly this typed-vs-pasted
  boundary; AI needs the analog.
- **Capability scoping** — e.g. "read output but don't send input to a running
  process." Kitty's per-command password + AES-GCM (exp 007) is a primitive form.
- **Approval / dry-run / audit** for destructive commands.
- Carry **provenance + confidence** on values (the cwd lesson, #2) so the agent
  knows what a result actually is.

### 6. Input injection done right
`send-keys`-style keystroke simulation is fragile and timing-dependent (exp 008).
- **Batch execution** → a clean "run command, get structured result" primitive,
  not simulated typing.
- **Interactive programs** (vim, REPLs, `sudo` prompts) → a reliable keystroke
  channel using the Kitty keyboard protocol's unambiguous encoding
  (`../comparisons/input.md`). Distinguishing these two modes is a design axis.

## What to inherit vs. invent

**Inherit** (Part II of `../SYNTHESIS.md` — already de-facto standard, keeps
existing tools working):
- VT/ANSI grammar + the **Williams parser** (`../comparisons/parser.md`)
- **OSC 133 / OSC 7**, and the **Kitty keyboard & graphics** protocols
- the GPU rendering / glyph-atlas stack for the human display

**Invent** (the thin, high-value layer on top):
- the **semantic command record** (retain the join) + the **agent API** over a
  typed protocol. In today's tooling, exposing the terminal as an **MCP server**
  for agents is a natural framing (typed schema, local socket).

## Open design questions

1. **Does an AI-native "terminal" even need to be a terminal?** The PTY/VT exists
   to bridge programs that expect a tty. An agent running `bash -c` and reading
   structured output doesn't need cell-grid rendering — VT emulation could be a
   *display mode* that turns on only when a human is watching or a program demands
   a tty.
2. **The minimal intervention.** No API exposes the exit code (#4), yet OSC 133;D
   already carries it. The smallest useful change is a terminal that just
   **retains + pushes that one field**. tmux built durable OSC 133 records and
   **reverted** them (`6fd9987`, exp 002) — understanding *why* is the key
   design-risk signal.
3. **Depend on the shell, or bypass it?** #3 showed prompt hooks are a dead end
   for agents. If the terminal **spawns commands directly**, it knows the
   boundaries with 100% fidelity and needs no shell cooperation — at the cost of
   losing the shell's own notion of "a command."

## See also
- `structured-terminal.md` — retain the `command→output→exit-code` join.
- `terminal-protocol.md` — the typed, push, query API to expose it.
- `future.md` — the loose idea backlog (semantic scrollback, command graph,
  session replay, PTY snapshot, event bus).
- `../comparisons/agent-opportunities.md` — the four findings this builds on.
- `../SYNTHESIS.md` — the full study.
