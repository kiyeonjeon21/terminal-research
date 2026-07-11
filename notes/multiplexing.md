# Terminal Multiplexing

> Learning note. Facts cite source; assumptions are marked _(assumption)_.

## Question
What is a terminal multiplexer, why does it exist, and how does it differ from a
GUI terminal with tabs/splits?

## Key concepts
- server/client split; sessions/windows/panes
- persistence across disconnect
- why detach/reattach requires a server holding the PTYs

## Findings

### What a multiplexer is
A **server process that owns the PTYs and child (shell) processes**, decoupled
from the UI ("client") that draws them. Because the long-lived server holds each
pane's PTY master, the UI can disconnect and the programs keep running. In tmux
each `window_pane` stores the PTY `fd`/`pid` in the server (`tmux.h:1266`), so
detaching (`server-client.c:563`) tears down only the client.

### Why it exists
1. **Sessions survive disconnects** — detach, drop the SSH connection, the build
   keeps running; attach later from anywhere.
2. **One set of processes, many viewers** — multiple clients attach to the same
   session and mirror it (pair programming).
3. **Windows/panes** — split one terminal into many logical terminals.

### Why detach/reattach *requires* a server
A Unix process's controlling terminal is a PTY. If the process owning the PTY
master exits, the child receives SIGHUP and dies (see `pty.md`). To let the UI
come and go, *something else* must keep holding the PTY master + child — that
"something else" is the multiplexer server. A GUI terminal that is itself the
PTY owner **cannot** offer detach/reattach.

### Multiplexer vs GUI-terminal-with-tabs
- **True multiplexers:** tmux, and WezTerm via `wezterm-mux-server` — separate
  server/mux process owns panes+PTYs; detach/attach + multiple clients. WezTerm
  is notable for being *both* a GUI terminal and a multiplexer.
- **GUI terminals with tabs/splits:** Kitty (Boss→TabManager→Tab→Window) and
  Ghostty (Surface + apprt tabs/splits) keep the window tree *inside the single
  UI process*; children are owned by that process and die on exit. No detach/
  attach, no multi-client.
- Kitty's `--session` is **declarative layout restore** (reopen these tabs/dirs/
  commands as new processes), not live-process persistence. Ghostty has none.

Details + citations in `../comparisons/multiplexing.md`.

## Open questions
- tmux control mode as a *machine* client of the same server (covered in
  `../experiments/007-control-api/`).
- WezTerm's tmux control-mode bridge (`mux/src/tmux.rs`) — surfacing an inner
  tmux as native panes.

## Sources
- `../comparisons/multiplexing.md`; `pty.md`; per-terminal files cited there
