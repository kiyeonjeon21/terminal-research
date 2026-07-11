# 007-control-api

## Question
A **new axis** after the shell-integration arc (001–006). Those showed terminals
leave command structure to a human's interactive prompt cycle — a dead end for
agents. So: **is there an API an external program (a coding agent) can drive?**
Send input, read output, spawn, query state, watch events — does a *build-on*
surface already exist, and does it expose the command→output→exit-code structure
that 001/002/006 found missing?

Covered across all four: Ghostty, Kitty, WezTerm, tmux.

## Setup / how to reproduce
Static source trace — no build. Read-only against the clones. Entry points:

**Ghostty** (`projects/ghostty`) — minimal IPC
```sh
sed -n '56,64p' src/apprt/ipc.zig      # the entire IPC Action union
ls src/cli/                            # `ghostty +<action>` = config introspection
```

**Kitty** (`projects/kitty`) — `kitty @` remote control
```sh
ls kitty/rc/                           # 41 command classes
grep -n "encode_send\|@kitty-cmd" kitty/remote_control.py
grep -n "extent\|CommandOutput" kitty/rc/get_text.py
grep -n "allow_remote_control" kitty/boss.py
```

**WezTerm** (`projects/wezterm`) — three surfaces
```sh
ls wezterm/src/cli/                    # `wezterm cli` subcommands
grep -n "get_semantic_zones" lua-api-crates/mux/src/pane.rs   # Lua-only
grep -c "=>" codec/src/lib.rs          # 60+ PDUs; no SemanticZone PDU
```

**tmux** (`projects/tmux`) — control mode (`-CC`)
```sh
grep -n "%%output\|control_start" control.c
grep -n "control_write_output" window.c
grep -n "unsafe permissions" tmux.c    # filesystem-only security
```

## Steps
See `notes.md` for the four traces + capability matrix, `result.md` for the
synthesis (pull-vs-push models; the exit-code gap that persists from the API side).
