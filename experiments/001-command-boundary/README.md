# 001-command-boundary

## Question
How does Ghostty detect where one command's output ends and the next begins?

## Setup / how to reproduce
Static source trace — no build required. Against `projects/ghostty` (shallow
clone), follow the OSC 133 path from parser to grid state to consumer:

```sh
cd projects/ghostty
grep -rni "semantic_prompt\|OSC 133" src/terminal/ | less
```

Entry points to read, in order:
1. `src/terminal/osc/parsers/semantic_prompt.zig` — parses `133;A..D`
2. `src/terminal/stream_terminal.zig:276` — dispatches to the terminal
3. `src/terminal/Terminal.zig:1736` `semanticPrompt()` — applies each action
4. `src/terminal/Screen.zig:2590` `cursorSetSemanticContent()` — writes state
5. `src/terminal/page.zig:1972` (row) & `:2072` (cell) — where it's stored
6. `src/terminal/Screen.zig:3115` `selectOutput()` — a consumer that
   reconstructs a boundary

## Steps
See `notes.md` for the running trace and `result.md` for the answer.
