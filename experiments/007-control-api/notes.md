# Notes — 007-control-api

Traces of each terminal's programmatic control surface. Headline claims
spot-checked firsthand (`tmux/control.c:575`, `tmux/window.c:1314`,
`kitty/rc/get_text.py:87-95`, wezterm no-`SemanticZone`-PDU, ghostty
`src/apprt/ipc.zig:56-64`). Paths relative to each clone under `../../projects/`.

## Ghostty — essentially no control API

- IPC surface = **2 actions**: `new_window` (+args) and `toggle_quick_terminal`
  (`ghostty/src/apprt/ipc.zig:56-64`), over platform IPC (GTK D-Bus
  `src/apprt/gtk/ipc/`, macOS app).
- `ghostty +<action>` CLI (`src/cli/`) is config/introspection only:
  `show-config`, `list-actions`, `list-keybinds`, `validate-config`, `ssh`, etc.
- **No** input injection, output reading, state query, or events. The most
  shell-integration-polished terminal has the least remote-control surface.

## Kitty — `kitty @` RPC (request/response)

- **Transport:** JSON in a DCS frame `\x1bP@kitty-cmd{…}\x1b\\`
  (`kitty/remote_control.py:308`), sent in-band (from inside a kitty window) or
  to a unix/TCP socket (`--listen-on` / `--to` / `KITTY_LISTEN_ON`). Dispatch:
  `Boss._handle_remote_command` (`kitty/boss.py:720`) → `handle_cmd`
  (`remote_control.py:212`).
- **Security — most developed of the four:** `allow_remote_control`
  (`yes`/`no`/`socket-only`/`socket`/`password`); `remote_control_password` maps a
  password → allowed command globs / custom Python checker (**per-command
  scoping**); optional AES-256-GCM with ±5-min replay guard
  (`remote_control.py:58-75, 133-201`). Unknown password → interactive allow/deny.
- **Agent command set** (`kitty/rc/*.py`, 41 commands): `send-text`/`send-key`
  (input), `run` (exec a program off-screen and stream stdout/stderr back),
  `launch`/`new-window` (spawn), `ls` (window tree w/ cwd/pid/cmdline/env/title),
  `signal-child` (SIGINT/…), `set-user-vars`.
- **Reads command output:** `get-text --extent last_cmd_output`
  (`rc/get_text.py:87-95`) resolves the OSC-133 marks via `Window.cmd_output` →
  `screen.cmd_output` (the exp-002 `find_cmd_output` scan). So an agent can fetch
  "the last command's output" directly. **Exit code:** tracked internally
  (`last_cmd_exit_status`) but **not** in the `get-text` response.
- **Model:** strictly request/response. Async/streaming exist but only within one
  request's lifecycle — **no pub/sub; poll for changes.** Schema is
  machine-readable (auto-generates a Go client).

## WezTerm — three surfaces (hybrid)

- **(A) `wezterm cli`** (`wezterm/src/cli/`): external, request/response over unix
  socket (default `RUNTIME_DIR/sock`) or **TLS/SSH** domains for remote.
  `send-text` (input), `get-text` (+scrollback), `spawn`/`split-pane`, `list`
  (panes/tabs/clients w/ cwd+title), `list-clients`, activate/kill/zoom. One-shot.
- **(B) Lua** (`lua-api-crates/mux/src/pane.rs`, in-process only): richest —
  `send_text`, `inject_output` (write into the display), `get_current_working_dir`,
  **`get_semantic_zones` / `get_text_from_semantic_zone`** (OSC-133 command
  regions), `get_user_vars`, plus events via `wezterm.on(...)`. Only reachable by
  installing config, not by an out-of-process agent.
- **(C) codec/mux protocol** (`codec/src/lib.rs`, 60+ PDUs): a *persistent* client
  receives server-pushed `GetPaneRenderChangesResponse` deltas + `NotifyAlert`
  (incl. `SetUserVar`) — real event observation — but there is **no `subscribe`
  verb and no `SemanticZone` PDU** (confirmed). So the cli cannot read zones.
- **Reads command output:** semantic zones **Lua-only**; cli `get-text` is a
  line-range approximation. **Exit code:** discarded (exp 002,
  `performer.rs:900-902`).
- **Security:** local unix socket = filesystem perms only (no token,
  `SetClientId` is identification not auth); remote = mutual-TLS (per-start CA,
  per-client certs, `pki.rs`) or SSH.

## tmux — control mode `-CC` (push / event-stream)

- **Protocol:** client sends plain tmux commands (LF-delimited) on stdin; server
  replies with a line-based `%`-prefixed stream. Entry `control_start`
  (`control.c:739`); input parse `control.c:449-478`.
- **Command framing:** `%begin/%end/%error <time> <number>` around each submitted
  command's output (`cmd-queue.c:825-833`), correlatable by `<number>`.
- **`%output %<pane> <data>` = a PUSH firehose** of *every* pane's raw bytes to
  the controller (`control.c:575`, produced per-pane in `window.c:1314`), octal-
  escaped; backpressure via `%pause`/`%continue`. **This is the closest thing to
  an agent event bus that already ships.** Plus structural notifications:
  `%window-add`, `%session-changed`, `%pane-mode-changed`, … (`control-notify.c`).
- **Agent commands:** `send-keys` (input), `capture-pane` (read), `new-window`/
  `split-window`/`new-session` (spawn), `list-*` / `display-message -p` with
  formats (`#{pane_current_path}`, `#{pane_pid}`, `#{pane_current_command}`).
  `pipe-pane` streams one pane's output to an external command.
- **Command boundaries/exit codes:** command *response* framing yes; **shell**
  command boundaries/exit codes **no** — `input_osc_133` stores only A/C line
  flags, discards `D`+exit status (`input.c:3169-3189`, exp 002/005). Agent must
  re-parse OSC 133 out of the `%output` bytes. `#{pane_dead_status}` gives only a
  dead pane's *top-level* process exit, not per-command.
- **Security:** unix socket, **filesystem perms only, no auth** (`tmux.c:225`
  rejects group/other-accessible dir); same-uid = full control of every session.

## Cross-terminal matrix

| | Ghostty | Kitty | WezTerm | tmux |
| --- | --- | --- | --- | --- |
| Model | fire-and-forget | request/response (poll) | hybrid (cli 1-shot; codec push; Lua events) | **push / event-stream** |
| Input inject | ✗ | send-text/send-key | send-text; Lua inject_output | send-keys |
| Read output | ✗ | get-text (`last_cmd_output`), run | cli get-text; zones Lua-only | capture-pane; `%output` push |
| Spawn | new-window | launch/run | spawn/split | new-window/split/new-session |
| Query state | config only | ls (cwd/pid/cmdline/env) | list (panes/cwd/title) | list-*/formats |
| Events | ✗ | ✗ (poll) | codec deltas + Lua on() | `%output` + structural `%…` |
| Command output reachable | ✗ | ✓ (cleanest) | Lua-only | raw bytes (re-parse) |
| Exit code reachable | ✗ | ✗ | ✗ | ✗ |
| Security | OS session | password per-cmd + AES-GCM | filesystem / mTLS+SSH | filesystem only, no auth |

## Facts vs. assumptions
- _(fact)_ Matrix cells cite source; headline claims re-verified firsthand.
- _(assumption)_ WezTerm named-event emit sites (`user-var-changed`,
  `augment-command-line`) live in the `wezterm-gui` crate — the `wezterm.on`/emit
  mechanism is verified, those exact string sites were not located.
- _(assumption)_ Kitty's C-level OSC-133 mark scan behind `screen.cmd_output` was
  not re-read here; the Python selector plumbing (`rc/get_text.py`) is verified.
- _(assumption)_ Non-agent management commands (focus/close/resize/colors, etc.)
  characterized from their `short_desc`, not full reads.
