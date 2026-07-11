# Result — 002-command-model

> Projects: WezTerm, Kitty, tmux (shallow clones under `../../projects/`).
> Ghostty from `../001-command-boundary/`. Facts cite `file:line`; interpretation
> marked _(interpretation)_.

## Answer

**No — none of WezTerm, Kitty, or tmux keeps a durable, queryable command
record.** All four terminals studied converge on the *same* minimal model:

> The only durable command-boundary artifact is a **≤2-bit semantic tag on the
> grid**. Command identity, output ranges, and exit codes are either
> reconstructed on demand from those tags, or discarded.

| Terminal | Durable artifact | Boundary reconstruction | Exit code (OSC 133;D) |
| --- | --- | --- | --- |
| Ghostty | per-cell `semantic_content` + per-row `semantic_prompt` (`page.zig:2072`, `:1972`) | lazy — `Screen.zig:3115 selectOutput`, `PageList.zig:3022 scrollPrompt` | surfaced then dropped — `stream_handler.zig:1109` → `Surface.zig:1128 command_finished` (notification only) |
| WezTerm | per-cell `SemanticType` 2-bit tag (`wezterm-cell/src/lib.rs:211`) | lazy `Line.zones` cache (`line/line.rs:426-482`) + recomputed `get_semantic_zones` (`terminalstate/mod.rs:2711`) | **discarded** — empty arm `performer.rs:900-902` |
| Kitty | 2-bit per-line `prompt_kind` (`line.h:84`; enum `data-types.h:208`) | mark-scan `find_cmd_output` (`screen.c:4522`), `cmd_output` (`screen.c:4658`) | transient scalar `last_cmd_exit_status` (`window.py:260`), overwritten each command |
| tmux | 2 per-line flag bits `GRID_LINE_START_PROMPT/OUTPUT` (`tmux.h:805-806`); only `A`/`C` handled | copy-mode scan `window-copy.c:6516`, `capture-pane.c:368` | **not handled** — no `B`/`D` case in `input_osc_133` (`input.c:3171-3189`) |

## Notable specifics

- **WezTerm retains the least.** Despite the richest surface API (`SemanticZone`,
  Lua `get_semantic_zones` / `get_text_from_semantic_zone`), the OSC 133;D exit
  code is dropped in an empty match arm (`performer.rs:900-902`), verified
  firsthand. Its zones are a lazy cache rebuilt from the per-cell tag.
- **Kitty keeps a scalar, not a record.** `last_cmd_exit_status` is a single
  value on the Python `Window`, overwritten by the next command and never joined
  to the output region that `find_cmd_output` reconstructs.
- **tmux is the thinnest and the most telling.** It handles only `A`/`C` (two
  line-flag bits) and never parses `B`/`D`. Its HEAD commit `6fd9987` is a
  **revert** of `f3c6b4f` "Add formats and events for OSC 133 commands … and a
  -T flag" — a durable-records version was implemented and then removed.

## Interpretation (the thesis)

_(interpretation)_ Four terminals, four independent codebases (Zig / Rust / C /
C), all landed on the same design: **tag the grid, throw away the structure.**
Every one of them *computes* command boundaries — enough to jump between prompts
and select a command's output — yet none *retains* the join of `command →
output → exit code` as queryable data. Exit codes in particular are treated as
UI ephemera (a notification, a scalar) or dropped entirely.

The tmux revert makes the point sharply: durable command records are not merely
an unnoticed gap — at least one project built them and chose to back them out.
Whatever the reason (scope, config surface, maintenance), the *result* is that
today an external consumer — including a coding agent — cannot ask the terminal
"what did command N output and how did it exit?" and must screen-scrape the grid
the way `selectOutput` / `find_cmd_output` do internally.

That absence is the concrete opening for an agent-native terminal. See
`../../ideas/structured-terminal.md` and `../../comparisons/agent-opportunities.md`.

## Open questions / next
- Was `f3c6b4f`'s reverted design storing per-command records or just formats?
  (Would need the full-history clone to diff.)
- OSC 7 (cwd) support per terminal — separate follow-up (TBD in the comparison).
- Does any terminal expose command state over IPC (WezTerm mux, Kitty remote
  control)? Kitty's `@ get-text` selectors are the closest, but they still
  mark-scan rather than read records.
