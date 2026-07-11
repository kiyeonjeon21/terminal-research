# Architecture — Comparison

> Fill the table as findings are verified. Cite `file:line` per project.

## Question
How is each terminal structured, and what does it choose to be?

| Project | Language | Rendering | Multiplexer | Reusable library |
| ------- | -------- | --------- | ----------- | ---------------- |
| Ghostty | Zig      | GPU       | No          | libghostty       |
| WezTerm | Rust     | GPU       | Yes         | No               |
| tmux    | C        | N/A       | Yes         | No               |
| Kitty   | C/Python | GPU       | No          | No               |
| VS Code | TS       | GPU (xterm.js) | No     | xterm.js         |

## Structural overview (from the subsystem studies)
Synthesized from `parser.md`, `rendering.md`, and `../notes/pty.md`.

| | Parser | Renderer | PTY I/O model | Process shape |
| --- | --- | --- | --- | --- |
| **Ghostty** | Williams, comptime table + SIMD | GPU, Metal/GL, instanced | reader **thread** / pane | single GUI process |
| **WezTerm** | Williams, const-fn tables | GPU, WebGPU/GL, indexed | reader **thread** / pane | GUI + **mux server** (local/SSH/TLS) |
| **Kitty** | hand-rolled switch + heavy SIMD | GPU, GL, instanced | single **`poll()`** loop | C core + Python driver |
| **tmux** | Williams, fn-pointer tables | **none** — escapes to outer tty | libevent **bufferevent**/pane | long-lived **server**, PTY/pane, itself behind a tty |

## Notes
- **What each chooses to be.** Ghostty — a fast standalone GPU terminal with a
  reusable `libghostty`/`libghostty-vt` core (the only one factored as a library).
  WezTerm — a GPU terminal **with** a built-in multiplexer (own mux server,
  remote domains). Kitty — a GPU terminal with a C performance core and a Python
  control/extension layer. tmux — **not** a terminal emulator at all: a
  multiplexer that renders into another terminal (see `rendering.md`).
- **Two languages-of-choice patterns:** systems languages for the hot path
  (Zig/Rust/C) with either compile-time metaprogramming (Ghostty comptime tables,
  WezTerm const-fn) or hand-tuned SIMD (Kitty) for parsing/decoding; Kitty
  additionally uses Python for everything non-hot (remote control, config,
  kittens — see `../experiments/007-control-api/`).
- **The multiplexer split drives everything else:** tmux and WezTerm have a
  server/session model (detach/attach, one process serving many clients); Ghostty
  and Kitty are single GUI processes. This is also why tmux/WezTerm expose the
  richest control surfaces (exp 007) and why tmux uniquely runs "a terminal inside
  a terminal."

## Sources
`parser.md`, `rendering.md`, `../notes/pty.md`, `../experiments/007-control-api/`.
