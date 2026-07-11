# Shell Integration — Comparison

> Fill the table as findings are verified. Cite `file:line` per project.

## Question
What shell-integration protocols does each support, and how deeply?

### OSC 133 command model
Verified in `../experiments/001-command-boundary/` (Ghostty) and
`../experiments/002-command-model/` (WezTerm/Kitty/tmux). **Unanimous finding:
the durable artifact is a ≤2-bit semantic tag on the grid; no terminal keeps a
queryable command record.**

| Project | OSC 133 handled | Durable artifact | Exit code (133;D) |
| ------- | --------------- | ---------------- | ----------------- |
| Ghostty | A/N/P/B/I/C/D + Kitty ext (`redraw`, `click_events`) | per-cell + per-row tag (`page.zig:2072`, `:1972`) | surfaced then dropped (`stream_handler.zig:1109`, notification only) |
| WezTerm | A/P/N/B/I/C/D parsed | per-cell 2-bit `SemanticType` (`wezterm-cell/src/lib.rs:211`); lazy zone cache | **discarded** — empty arm `performer.rs:900-902` |
| Kitty   | A/C set line tag; D → Python | 2-bit per-line `prompt_kind` (`line.h:84`) | transient scalar `last_cmd_exit_status` (`window.py:260`) |
| tmux    | **A/C only** (no B/D) | 2 line-flag bits (`tmux.h:805-806`) | **not handled**; richer version reverted (`6fd9987`) |

### cwd tracking (OSC 7 vs OS process inspection)
Verified in `../experiments/005-cwd-tracking/`. **The terminals diverge on
whether to trust the shell's OSC 7 escape or read the OS process cwd.**

| Project | Parses OSC 7 | Authoritative cwd source | Process-cwd fallback |
| ------- | ------------ | ------------------------ | -------------------- |
| Ghostty | yes → `setPwd` (`osc.zig:799`) | **shell escape only** (OSC 7 / iTerm2 1337 + spawn seed) | **no** |
| WezTerm | yes → `current_dir: Url` (`performer.rs:936`) | OSC 7 primary, else process | yes (`localpane.rs:1061`) |
| Kitty   | yes → `last_reported_cwd` (`screen.c:3250`) | **process default**; OSC 7 only *at prompt* & not remote (`window.py:166`) | yes (`/proc`, macOS, `pwdx`) |
| tmux    | yes → display-only `#{pane_path}` (`input.c:2711`) | **process only** (`osdep_get_cwd`, `format.c:965`) | yes (authoritative) |

Spectrum, most→least trusting of the shell: **Ghostty → WezTerm → Kitty → tmux.**

### Other shell-integration surface (TBD)
| Project | Provided shell scripts |
| ------- | ---------------------- |
| Ghostty | _TBD_ |
| WezTerm | _TBD_ |
| Kitty   | _TBD_ |
| tmux    | _TBD_ |
