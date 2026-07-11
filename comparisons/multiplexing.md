# Multiplexing / Session Model — Comparison

> Breadth/learning study. The object model (session/window/tab/pane) and, the key
> axis, **what survives disconnect**. Cite `file:line`. Background in
> `../notes/multiplexing.md`.

## Question
How does each structure sessions/windows/panes, and what persists when the UI
disconnects?

| Terminal | Object model | Server / persistent? | Detach–attach | Multi-client | Built-in session save |
| -------- | ------------ | -------------------- | ------------- | ------------ | --------------------- |
| **tmux** | session→winlink→window→window_pane(+PTY); server owns global `sessions/windows/clients` (`tmux.h:1557/1384/1266`, `server.c:212`) | **YES** — standalone server holds PTYs; survives client disconnect (`server-client.c:563`) | **YES** — `detach-client`/`attach-session` (`cmd-detach-client.c:33`, `CLIENT_EXIT_DETACH` `tmux.h:2275`) | **YES** — mirrored; `attached` count (`tmux.h:1582`) | no full disk save (external `tmux-resurrect`) |
| **WezTerm** | Mux→Domain→Window→Tab→Pane + workspaces (`mux/src/lib.rs:102`, `domain.rs:50`) | **YES with mux-server** (`wezterm-mux-server*/`); local-only GUI is not | **YES** — `wezterm connect` (`wezterm-gui/src/main.rs:126`), `Domain::detach/attach` (`domain.rs:192`) | **YES** — `clients` map (`lib.rs:111`) | workspaces built-in; resurrect external |
| **Kitty** | Boss→(os_window)→TabManager→Tab→WindowList→Window(+child) (`boss.py:414`, `tabs.py:1182/177`, `window.py:684`) | **NO** — single process; children die on exit | **NO** | **NO** (`kitty @` = remote command, not attach) | **layout only** — `kitty --session` (`session.py:223/318`) |
| **Ghostty** | Surface owns its PTY; tabs/splits are apprt actions, no persistent tree (`Surface.zig:1-7`, `apprt/action.zig:84-146`) | **NO** — single process | **NO** | **NO** | none |

## Notes
- **The split is multiplexer vs GUI-terminal-with-tabs.** tmux and WezTerm's mux
  are true multiplexers — a **separate server process owns the panes + PTYs**, so
  the UI ("client") can come and go. Kitty and Ghostty are single GUI processes
  whose window tree and child processes live *in* the process; on exit, children
  die.
- **WezTerm is both** — a GUI terminal *and*, via `wezterm-mux-server`, a
  multiplexer. The plain local GUI (no mux-server) is not persistent; the
  unix/SSH/TLS mux domains are.
- **Why detach/reattach needs a server** (`../notes/multiplexing.md`): a Unix
  process's controlling terminal is a PTY; if the process owning the PTY master
  exits, the child gets SIGHUP and dies. To let the UI disconnect, *something
  else* must keep holding the PTY master — that's the multiplexer server. tmux
  stores the PTY `fd`/`pid` on each `window_pane` in the server (`tmux.h:1266`),
  so detach (`server-client.c:563`) tears down only the client.
- **Kitty `--session` is layout restore, not persistence** — it re-opens tabs/
  splits/cwds/commands as *new* processes (`session.py`), not live processes or
  scrollback. Ghostty has not even that.
- **Nesting:** tmux is socket-per-server, so tmux-in-tmux is independent servers;
  WezTerm has first-class tmux control-mode integration (`mux/src/tmux.rs`),
  surfacing an inner tmux as native WezTerm panes. Kitty/Ghostty are outermost
  PTY hosts.
- Ties to the control-API axis: tmux/WezTerm's server model is *why* they expose
  the richest control surfaces (`../experiments/007-control-api/`).

## Sources
Per-terminal files above; `../notes/multiplexing.md`.
