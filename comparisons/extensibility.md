# Extensibility — Comparison

> Cite `file:line` per project. Control-API rows verified in
> `../experiments/007-control-api/`.

## Question
How can users/programs extend behavior — config, scripting, plugins, APIs?

## Config & scripting
| Project | Config format | Scripting |
| ------- | ------------- | --------- |
| Ghostty | key=value config file | none (config only) |
| Kitty   | `kitty.conf` | Python "kittens" + custom Python remote-control checkers |
| WezTerm | **Lua** config (`wezterm.lua`) | full Lua API + `wezterm.on(...)` event handlers |
| tmux    | `.tmux.conf` (tmux commands) | tmux commands / hooks; no embedded language |

## Programmatic control API (can an external program drive it?)
The core of `../experiments/007-control-api/`. **A build-on surface exists for
three of four, split across two interaction models; none exposes a command's
exit code.**

| | Ghostty | Kitty | WezTerm | tmux |
| --- | --- | --- | --- | --- |
| Surface | 2 IPC actions (`apprt/ipc.zig:56`) | `kitty @` RPC | `cli` / Lua / codec | control mode `-CC` |
| Transport | platform IPC (D-Bus/app) | DCS escape or unix/TCP socket | unix / TLS / SSH | unix socket |
| Model | fire-and-forget | request/response (poll) | hybrid | **push / event-stream** |
| Input inject | ✗ | send-text/send-key | send-text; Lua inject_output | send-keys |
| Read output | ✗ | get-text `last_cmd_output`; run | cli get-text; zones Lua-only | capture-pane; **`%output` push** |
| Spawn | new-window | launch/run | spawn/split | new-window/split/new-session |
| Query state | config only | ls (cwd/pid/cmdline/env) | list (panes/cwd/title) | list-\* / formats |
| Events to a client | ✗ | ✗ (poll) | codec deltas + Lua on() | `%output` + structural `%…` |
| Command output reachable | ✗ | ✓ cleanest | Lua-only | raw bytes (re-parse) |
| Exit code reachable | ✗ | ✗ | ✗ | ✗ |
| Security | OS session | password per-cmd + AES-GCM | filesystem / mTLS+SSH | filesystem only, no auth |

Spectrum of capability: **Ghostty (≈none) → WezTerm/Kitty/tmux (rich, different
models).** Interaction model is the sharpest split — Kitty pulls, tmux pushes.
See `agent-opportunities.md` Finding #4.
