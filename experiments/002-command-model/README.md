# 002-command-model

## Question
Experiment 001 found that **Ghostty** keeps no durable command records — it tags
the grid and reconstructs command boundaries on demand. Do the other terminals
differ? Specifically: **does any of WezTerm, Kitty, or tmux keep a durable,
queryable command record (command → output range → exit code)?**

## Setup / how to reproduce
Static source trace — no build required. Against the shallow clones under
`../../projects/`. Read-only (per `AGENTS.md`, cloned source is not modified).

Entry points per project:

**WezTerm** (`projects/wezterm`)
```sh
grep -rn "FinalTermSemanticPrompt\|SemanticType\|get_semantic_zones" term/ wezterm-cell/ wezterm-surface/
```
- Parse: `wezterm-escape-parser/src/osc.rs:704` (`FinalTermSemanticPrompt`)
- Handle: `term/src/terminalstate/performer.rs:863-902`
- Store: `wezterm-cell/src/lib.rs:181-211` (`SemanticType`, 2-bit tag)
- Query: `term/src/terminalstate/mod.rs:2711` (`get_semantic_zones`)

**Kitty** (`projects/kitty`)
```sh
grep -n "shell_prompt_marking\|find_cmd_output\|prompt_kind" kitty/screen.c kitty/line.h
```
- Parse/handle: `kitty/screen.c:3179` (`shell_prompt_marking`), dispatch `vt-parser.c:580`
- Store: `kitty/line.h:84-93` (`LineAttrs.prompt_kind`), enum `kitty/data-types.h:208`
- Reconstruct: `kitty/screen.c:4522` (`find_cmd_output`), `:4658` (`cmd_output`)
- Exit code: `kitty/window.py:260` (`last_cmd_exit_status`, scalar)

**tmux** (`projects/tmux`)
```sh
grep -n "input_osc_133\|GRID_LINE_START_PROMPT\|GRID_LINE_START_OUTPUT" input.c tmux.h
```
- Parse/handle: `input.c:2747` (dispatch), `input.c:3171-3189` (`input_osc_133`, `A`/`C` only)
- Store: `tmux.h:805-806` (two grid-line flag bits)
- Consume: `window-copy.c:6516` (copy-mode prompt nav), `cmd-capture-pane.c:368`
- Note: HEAD `6fd9987` reverts a richer "formats and events for OSC 133" version.

**Ghostty**: see `../001-command-boundary/` (not re-traced here).

## Steps
See `notes.md` for the per-terminal traces and `result.md` for the unified answer.
