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

### Other shell-integration surface (TBD)
| Project | OSC 7 (cwd) | Provided shell scripts |
| ------- | ----------- | ---------------------- |
| Ghostty | _TBD_ | _TBD_ |
| WezTerm | _TBD_ | _TBD_ |
| Kitty   | _TBD_ | _TBD_ |
| tmux    | _TBD_ | _TBD_ |
