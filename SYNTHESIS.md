# Synthesis — Four modern terminals, end to end

> The comprehensive conclusion of this study: both **(I) the agent-native thesis**
> — what terminals do with command structure and where a coding agent falls out —
> and **(II) how terminals actually work** — the parsing, rendering, PTY,
> multiplexing, input, and graphics mechanics learned across the four. Every claim
> traces to a cited experiment or comparison; those cite source `file:line` in the
> four studied terminals (Ghostty, WezTerm, Kitty, tmux). Facts and interpretation
> are kept separate throughout (per [AGENTS.md](AGENTS.md)).

Nine experiments + nine cross-terminal comparisons, all against unmodified source
clones. Index: [experiments/](experiments/), [comparisons/](comparisons/).

---

# Part I — The agent axis

## Thesis

**Modern terminals compute command structure but never keep it, and they get it
only from an interactive human's prompt cycle — so for a coding agent, running
commands non-interactively, that structure does not exist.** Even the terminals'
own control APIs, which do let a program drive them, expose reconstructed output
but no command exit code. The agent-native opportunity is therefore narrow and
specific: a *uniform, structured, event-driven* surface that retains and pushes
`command → output → exit code`, which no terminal offers today.

This held across four independently-built terminals (Zig / Rust / C / C),
approached from three directions that all landed on the same gap.

## The research arc (agent axis)

**Shell-integration axis — how terminals handle OSC 133 / OSC 7:**
- [001](experiments/001-command-boundary/) — Ghostty: no durable command record; grid tags + lazy reconstruction.
- [002](experiments/002-command-model/) — WezTerm/Kitty/tmux: same design; exit codes dropped or a transient scalar; tmux even *reverted* a richer version (`6fd9987`).
- [005](experiments/005-cwd-tracking/) — cwd: shell-escape (OSC 7) vs OS process inspection; four different policies.
- [006](experiments/006-shell-emitters/) — the emitter scripts: every marker is gated behind an interactive shell + a prompt hook.
- [003](experiments/003-osc133/) — empirical: PTY capture proving the interactive-only claim on the wire.

**Control-API axis — what a program can drive:**
- [007](experiments/007-control-api/) — Ghostty ≈ none; Kitty RPC (pull); WezTerm cli/Lua/codec (hybrid); tmux control mode (push).
- [008](experiments/008-control-api-live/) — empirical: driving tmux control mode live confirms the `%output` push model — and the missing exit code — on the wire.

## The four findings

Full write-ups in [comparisons/agent-opportunities.md](comparisons/agent-opportunities.md).

**#1 — No terminal keeps a durable command record.** The only durable
command-boundary artifact is a **≤2-bit semantic tag on the grid** (Ghostty
`page.zig:2072`, WezTerm `wezterm-cell/src/lib.rs:211`, Kitty `line.h:84`, tmux
`tmux.h:805-806`). Identity, output ranges, and exit codes are reconstructed on
demand or discarded. _(Exp 001, 002.)_

**#2 — "cwd" is not one fact; each terminal collapses its provenance.** All four
parse OSC 7 but disagree on trusting it vs. reading the OS process cwd — a
spectrum **Ghostty (shell-only) → WezTerm → Kitty → tmux (process-only)**. cwd has
provenance and confidence that every terminal flattens to one string. _(Exp 005.)_

**#3 — The markers require an interactive human prompt.** OSC 133 / OSC 7 come
from the shell's integration scripts, which all hard-guard on an interactive shell
(`ghostty.bash:19`, `kitty.bash:3`, `wezterm.sh:27`) and bind every marker to a
prompt hook. A non-interactive `bash -c` emits **nothing** — confirmed on the
wire: same `echo hello` → full `D→A…B…C` interactively, exactly `hello\r\n`
non-interactively. So for agent commands the structure is not merely unretained —
it is **never produced**. _(Exp 006, 003.)_

**#4 — A control surface exists, but it's a patchwork that withholds the exit
code.** Three of four expose a drivable API in two interaction models — Kitty
**pulls** (RPC, poll), tmux **pushes** (`%output` firehose), WezTerm hybrid,
Ghostty ~none. Output is reachable everywhere; **no API exposes a command's exit
code**. Confirmed live in exp 008. _(Exp 007, 008.)_

## The design brief that falls out

_(Interpretation — the payoff.)_ An agent-native terminal does **not** start from
zero. The pieces exist, uncombined:

1. **Retain the join** — a durable `command → input → output range → exit code →
   duration` record instead of computing boundaries and throwing them away.
   (#1/#2 → [ideas/structured-terminal.md](ideas/structured-terminal.md).)
2. **Produce it without a prompt** — mark command boundaries for non-interactive
   execution so an agent's commands are visible. (#3.)
3. **Expose it on a push channel** — a typed, gated, event-driven API
   (`command.start / output / end{exit_code}`) modeled on **tmux's push** +
   **Kitty's schema and security**. (#4 →
   [ideas/terminal-protocol.md](ideas/terminal-protocol.md).)

The whole value-add is putting the structure every terminal already computes onto
a channel an agent can use. Experiment 008 shows the transport half (tmux
`%output`) already ships; the missing piece is the semantic layer.

---

# Part II — How terminals work (the mechanics)

The breadth study, synthesized. Each axis has a `comparisons/` doc; the recurring
theme is that **three of four converge on shared designs and Kitty tends to be the
outlier or the inventor.**

## Parsing the byte stream — [comparisons/parser.md](comparisons/parser.md)
Three of four implement **Paul Williams' vt500 state machine**
(`GROUND→ESCAPE→CSI…`, `OSC_STRING`, `DCS_*`), differing only in codegen: Ghostty
a **comptime**-generated table (`Parser.zig:15-30`), WezTerm **const-fn** packed
`u16` tables (`vtparse/src/enums.rs:36-60`), tmux **function-pointer** range tables
(`input.c:360`). **Kitty** hand-rolls a coarse 8-state switch (`vt-parser.c:178`)
and doesn't cite the spec. SIMD (Ghostty, Kitty — Kitty heaviest with
AVX2/SSE4.2/NEON) accelerates only the *print/scan* phase; control-sequence
parsing stays sequential. String sequences end with **BEL or ST** — the split seen
in exp 005/007 (`kitty-shell-cwd://`, `DCS @kitty-cmd`).

## Rendering the grid — [comparisons/rendering.md](comparisons/rendering.md)
Three are **GPU rasterizers** — Ghostty (Metal/GL, instanced quads), WezTerm
(WebGPU/GL, one `draw_indexed`), Kitty (GL, `glDrawArraysInstanced`) — each with a
**glyph atlas** (rasterize once, cache by font+glyph+size: `SharedGrid.zig:44`,
`glyphcache.rs:561`, `glyph-cache.c:9`), HarfBuzz shaping, and damage tracking
(Ghostty `false/partial/full`, WezTerm line **seqno**, Kitty `has_dirty_text`
bit). **tmux is the counter-example**: no GPU — it diffs grids and emits terminfo
escapes to an *outer* tty (`tty-draw.c`), so its "damage" saves **pipe bytes**, not
GPU draws. Cells are bit-packed (Ghostty 8B, Kitty 12B+20B split, tmux ~5B).

## The PTY & process model — [notes/pty.md](notes/pty.md), exp [004](experiments/004-pty-tracing/)
All four run the same POSIX ritual in the child: `openpty` (Ghostty/WezTerm/Kitty)
or `forkpty` (tmux) → reset signals → `setsid()` → `TIOCSCTTY` to acquire the
controlling tty → resize via `ioctl(master, TIOCSWINSZ)` which makes the **kernel**
raise SIGWINCH. Exp 004 makes this observable: a fresh PTY is **cooked** (ICANON/
ECHO on, echo is the *kernel's*), `\n`→`\r\n` via OPOST, and TIOCSWINSZ→SIGWINCH
delivers a live resize. They differ in I/O model — reader **thread** per pane
(Ghostty, WezTerm) vs one **`poll()`** loop (Kitty) vs **libevent** on a server
(tmux) — and in `TERM` (`xterm-ghostty` / `xterm-256color` / `xterm-kitty` /
`screen`). Exp [009](experiments/009-raw-mode-tui/) shows the flip side: a TUI puts
the tty in **raw** mode and drives the alternate screen.

## Multiplexing & sessions — [comparisons/multiplexing.md](comparisons/multiplexing.md)
The master variable. **tmux and WezTerm's mux are true multiplexers** — a separate
**server owns the PTYs**, so the UI can detach/reattach and multiple clients mirror
one session (tmux `window_pane` holds the PTY `fd`/`pid`, `tmux.h:1266`; WezTerm
`Mux`, `mux/src/lib.rs:102`). **Kitty and Ghostty are single GUI processes** with
tabs/splits but no server, so no persistence (Kitty `--session` is layout restore
only). Detach/reattach *requires* a server holding the PTY master — a GUI terminal
that is itself the PTY owner cannot offer it.

## Input, keys & modes — [comparisons/input.md](comparisons/input.md), exp [009](experiments/009-raw-mode-tui/)
Legacy key encoding is ambiguous (`Ctrl-I`==Tab, most keys can't carry modifiers).
**Kitty invented the keyboard protocol** (CSI u + a progressive-enhancement flag
stack, `vt-parser.c:1312`) to fix it; Ghostty and WezTerm implement it fully, tmux
does only the `extended-keys` encoding. Kitty **rejects** xterm's `modifyOtherKeys`
in favor of its own. Mouse SGR (`?1006`), bracketed paste (`?2004`, a *security*
feature), and focus (`?1004`) are universal. Exp 009 captured a real vim/less
negotiating exactly these modes on the wire (vim clears `ISIG`, less keeps it).

## Inline graphics — [comparisons/graphics.md](comparisons/graphics.md)
The base grid has no pixels, so images need an out-of-band protocol pinned to
cells. **Kitty invented the Kitty graphics protocol** (APC, shared-mem transport,
z-index) — Ghostty and WezTerm support it too; **WezTerm is the generalist**
(the only one doing all of Kitty graphics + **Sixel** + **iTerm2 OSC 1337**);
**tmux** natively decodes only Sixel and passes the rest through `allow-passthrough`.

---

# Cross-cutting patterns (both parts)

- **The multiplexer split is the master variable.** Whether a terminal has a
  server/session model (tmux, WezTerm) vs is a single GUI process (Ghostty, Kitty)
  predicts the rest: persistence, the richest control surfaces (exp 007), and even
  tmux's "terminal inside a terminal" rendering.
- **Reconstruct, don't retain — everywhere.** The same philosophy that leaves
  command records unstored (#1) shows up in rendering (lazy zone caches, damage
  tracking) and cwd (recompute from tags/process). Terminals compute richly and
  keep little.
- **De-facto standardization by copying.** No formal body, yet the four converge:
  the FinalTerm **OSC 133** + **OSC 7** protocol, Kitty's **`kitty-shell-cwd://`**
  scheme, the same bundled **`bash-preexec.sh`**, the **Williams** parser, and
  Kitty's **keyboard** and **graphics** protocols adopted by others.
- **Kitty is the protocol inventor / outlier.** It hand-rolls its parser, invented
  the keyboard and graphics protocols and the `kitty @` RPC with a machine-readable
  schema, and rejects `modifyOtherKeys` — repeatedly setting conventions the others
  adopt.
- **Hot-path engineering, three dialects.** Systems languages for the core, with
  **comptime tables** (Ghostty), **const-fn tables** (WezTerm), or **hand-tuned
  SIMD** (Kitty) for parsing/decoding, plus bit-packed cells to cut CPU→GPU upload.
- **Pull vs push is already in the wild.** Kitty's RPC polls; tmux control mode
  pushes a `%output` firehose. The design tension the agent protocol must resolve
  is not hypothetical — both models ship today (exp 007/008).

# The four terminals, characterized

_(Interpretation, drawing on every axis.)_

- **Ghostty (Zig)** — the purist single-process GPU terminal with a **library
  heart** (`libghostty`/`libghostty-vt`, the only one factored for reuse). Comptime
  Williams parser + SIMD; the most shell-integration polish (five shells incl.
  elvish; fish alone percent-encodes OSC 7); yet it **trusts the shell entirely**
  for cwd (no process fallback) and offers the **least** control surface (2 IPC
  actions).
- **WezTerm (Rust)** — the **batteries-included generalist**: a GPU terminal *and*
  a built-in multiplexer with remote mux over TLS/SSH, three control surfaces
  (cli/Lua/codec), and the only support for all three image protocols. Its one
  gap is discarding the OSC 133 exit code outright (`performer.rs:900-902`).
- **Kitty (C + Python)** — the **protocol-defining power tool**: a C hot core with
  a Python control/extension layer, inventor of the keyboard protocol, the graphics
  protocol, and the richest remote-control RPC (schema + per-command password +
  AES-GCM). Defaults to reading the OS process cwd (distrusts OSC 7 mid-command);
  no Sixel in this checkout.
- **tmux (C)** — **not an emulator at all**: a multiplexer that renders into
  another terminal and is the only one with a true **server/session** model and
  live persistence. Its control mode is the closest thing to an agent event bus
  that ships. It stores the least (two prompt-flag bits, no exit codes) — and once
  built durable OSC 133 records, then **reverted** them.

---

## Scope & what's left

The study covers the agent axis and the technical-core breadth. Genuinely
untouched (nice-to-haves, not gaps): a live SGR **mouse** report and the **Kitty
keyboard protocol** handshake capture; driving kitty `@` / wezterm `cli` on a
machine that has them running (kitty needs a GUI; wezterm isn't installed here —
both source-verified in exp 007).

## Method & reproducibility

Source reading over docs; execution paths traced, not files summarized; exact
`file:line` citations; facts separated from assumptions (per
[AGENTS.md](AGENTS.md)). Cloned projects under `projects/` are kept unmodified
(gitignored). Four experiments — [003](experiments/003-osc133/),
[004](experiments/004-pty-tracing/), [008](experiments/008-control-api-live/),
[009](experiments/009-raw-mode-tui/) — are empirical and ship a `harness.py`
(`python3 harness.py`).
