# Result — 001-command-boundary

> Project: Ghostty (shallow clone, `projects/ghostty`). All line numbers as of the
> cloned HEAD. Facts cite `file:line`; interpretation marked _(interpretation)_.

## Answer

OSC 133 drives **two independent consumers** in Ghostty:

**(1) Grid annotation (persistent, the boundary itself).** No command struct,
list, or start/end range is stored. It records **semantic content** on the grid
— one tag per *cell*, one summary tag per *row*. A boundary is never stored as a
range; it is **reconstructed on demand** by walking the per-row markers. Stated
explicitly on `OSC 133;N`:

> "We don't currently do explicit command tracking in any way so there is no
> need to terminate prior commands. We just perform the `A` action."
> — `src/terminal/Terminal.zig:1791-1798`

**(2) Transient command events (`src/termio/stream_handler.zig:1096-1130`).** In
parallel, the stream handler emits ephemeral events: `133;C` →
`surfaceMessageWriter(.start_command)` starts a timer; `133;D` →
`.stop_command{exit_code}` reads `133;D;exit_code` (`:1109-1112`). In
`Surface.zig` this fires the `command_finished{exit_code, duration}` apprt action
(`src/Surface.zig:1128-1150`) — used for desktop notifications / "command done"
integration. **These events are fire-and-forget: a timer plus a one-shot action,
not a stored command history.**

## How OSC 133 maps to state

Parser action enum (`src/terminal/osc/parsers/semantic_prompt.zig:23-31`):

| OSC | Action | Effect |
| --- | ------ | ------ |
| `133;A` | `fresh_line_new_prompt` | fresh line, cursor semantic = prompt |
| `133;N` | `new_command` | same as `A` (no real command tracking) |
| `133;P` | `prompt_start` | cursor semantic = prompt (kind `k=`) |
| `133;B` | `end_prompt_start_input` | cursor semantic = input (`clear_explicit`) |
| `133;I` | `end_prompt_start_input_terminate_eol` | input, cleared at EOL |
| `133;C` | `end_input_start_output` | cursor semantic = output |
| `133;D` | `end_command` | cursor semantic = output |

Each writes the *cursor's* semantic content; subsequently written cells inherit
it (`Terminal.semanticPrompt` → `Screen.cursorSetSemanticContent`,
`src/terminal/Terminal.zig:1736-1854`, `src/terminal/Screen.zig:2590`).

## Where the state lives

- **Per cell:** `Cell.semantic_content: SemanticContent` (`input`/`output`/prompt),
  `src/terminal/page.zig:2072-2075` + enum `:2116`. Comment: *"used by the
  semantic prompt (OSC 133) set of sequences to understand boundary points for
  content."*
- **Per row:** `Row.semantic_prompt: enum(u2) { none, prompt, prompt_continuation }`,
  `src/terminal/page.zig:1972`, `:1997-2010`. A row-level summary — *"may contain
  false positives but never false negatives"* — used as a fast index of which
  rows begin a prompt.

## How a boundary is reconstructed (the consumers)

Because nothing is stored as a range, boundaries are computed by iterating the
row markers:

1. **Jump to prompt** (`Cmd+↑/↓`): `scroll(.{ .delta_prompt = n })` →
   `PageList.scrollPrompt` (`src/terminal/PageList.zig:3022`) walks the
   `promptIterator` over rows whose `semantic_prompt != .none`.
2. **Select command output:** `Screen.selectOutput`
   (`src/terminal/Screen.zig:3115-3166`) — from a cell tagged `.output`, walk the
   `promptIterator(.left_up)` to the nearest prompt above, then highlight the
   contiguous `.output` region. That prompt→next-prompt gap *is* the command
   boundary, computed lazily.

## Interpretation (for agent-native ideas)

_(interpretation)_ Ghostty is *closer* to an event model than a first read
suggests — it does emit `command_finished{exit_code, duration}`. But that event
is **consumed and dropped** (fires a notification, updates a timer); it is never
stored, indexed, or made queryable. Combined with consumer (1), the terminal
holds two half-structured views — a queryable grid of prompt/input/output cells,
and a transient per-command event — but **neither is a durable, queryable
command history with output attached**. An agent still has to reconstruct
"command → its output → its exit code" itself (grid walk à la `selectOutput` for
the output, plus catching the ephemeral event for the code). That reconstruction
burden is exactly what `../../ideas/structured-terminal.md` proposes to remove.

## Open questions
- ~~Does any code path read `133;D;exit_code`?~~ **Resolved:** yes —
  `stream_handler.zig:1109`, surfaced as `command_finished`, then dropped.
- Is `command_finished` ever persisted or exposed to an API/IPC surface, or only
  used for notifications? (Only notification path found so far.)
- How do WezTerm / Kitty differ — do they keep explicit command records? → next experiments.
