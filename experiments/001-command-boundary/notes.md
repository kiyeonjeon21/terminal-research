# Notes — 001-command-boundary

Running observations while tracing. Cite `file:line`.

## Execution path

```
PTY bytes
  → OSC parser              src/terminal/osc/parsers/semantic_prompt.zig
  → stream dispatch         src/terminal/stream_terminal.zig:276
                              .semantic_prompt => terminal.semanticPrompt(value)
  → apply action            src/terminal/Terminal.zig:1736  semanticPrompt()
  → write cursor semantics  src/terminal/Screen.zig:2590    cursorSetSemanticContent()
  → store on grid           src/terminal/page.zig
                              Row.semantic_prompt  :1972  (none/prompt/prompt_continuation)
                              Cell.semantic_content :2072 (input/output/prompt)
  ← consume (lazy)          src/terminal/Screen.zig:3115   selectOutput()
                            src/terminal/PageList.zig:3022  scrollPrompt()  (jump-to-prompt)
```

## Observations
- No `Command` type exists. Grep for command tracking turns up only *semantic
  content* on cells/rows. Confirmed by the source comment at
  `Terminal.zig:1791-1798` — `133;N` deliberately does no command bookkeeping.
- The row marker is an **index/optimization**: "may contain false positives but
  never false negatives" (`page.zig:1969-1972`). Cell-level tags are the source
  of truth.
- `133;C` has a fish-specific heuristic: if the cursor row is a prompt and we're
  at column 0, the row is un-marked as prompt (fish has no PS2 / `k=s`)
  (`Terminal.zig:1829-1843`).
- `selectOutput` shows the reconstruction pattern: from an `.output` cell, walk
  `promptIterator(.left_up)` to the nearest prompt, else fall back to
  screen-top → next-prompt (`Screen.zig:3119-3149`).

## Second consumer (found on verification — corrected an earlier assumption)
- OSC 133 is dispatched to **two** handlers, not one:
  - `Terminal.semanticPrompt` — grid annotation (above).
  - `StreamHandler.semanticPrompt` (`src/termio/stream_handler.zig:1096`) — emits
    events: `133;C` → `.start_command` (starts timer), `133;D` →
    `.stop_command{exit_code}` reading `133;D;exit_code` (`:1109-1112`).
- `Surface.zig:1128-1150`: `.stop_command` computes duration and fires the
  `command_finished{exit_code, duration}` apprt action. Fire-and-forget — not
  stored.
- **Correction:** earlier assumption that `exit_code` is discarded was WRONG. It
  is read and surfaced (then dropped). Verified by
  `grep -rn "exit_code" src/` → only reader outside parser/tests is
  `stream_handler.zig:1110`.
