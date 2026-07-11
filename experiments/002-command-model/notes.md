# Notes — 002-command-model

Running observations. Citations verified against the shallow clones (punchlines
spot-checked firsthand: `performer.rs:900-902`, `input.c:3183-3186`,
`line.h:84`, `window.py:260`, `screen.c:4522`).

## WezTerm — same class as Ghostty, keeps *less*

```
OSC 133 parse   wezterm-escape-parser/src/osc.rs:704  FinalTermSemanticPrompt
  (D carries exit code: CommandStatus{ status, aid }  osc.rs:737-744)
  → handle      term/src/terminalstate/performer.rs:863-902
                A/P/N → set_semantic_type(Prompt); B/I → Input; C → Output
                CommandStatus{..} => {}          ← performer.rs:900-902 (exit code DISCARDED)
  → store       wezterm-cell/src/lib.rs:211      2-bit SemanticType per cell
  → derive      wezterm-surface/src/line/line.rs:426-482  Line.zones (lazy cache,
                invalidated on any edit: line.rs:786/819/925/...)
  → query       term/src/terminalstate/mod.rs:2711  get_semantic_zones()
                recomputes the whole Vec<SemanticZone> every call
```
- `SemanticZone` (`term/src/lib.rs:117-123`) has `start/end` coords + type only —
  **no exit_code, no command text, no aid**.
- Lua exposes `pane:get_semantic_zones` / `get_text_from_semantic_zone`
  (`lua-api-crates/mux/src/pane.rs:305-378`) — geometric regions, recomputed,
  no command identity.
- Net: authoritative state = per-cell tag (like Ghostty); WezTerm adds a lazy
  per-line zone cache + Lua helpers, but retains **no exit code at all** —
  strictly less durable command state than Ghostty (which at least surfaces it
  transiently).

## Kitty — 2-bit per-line tag, reconstruct by mark-scan

```
OSC 133 dispatch  kitty/vt-parser.c:580  → shell_prompt_marking()
  → handle        kitty/screen.c:3179
                  A → line_attrs[y].prompt_kind = PROMPT_START / SECONDARY_PROMPT
                  C → line_attrs[y].prompt_kind = OUTPUT_START
                  D → forwards exit_status string to Python, writes NOTHING to grid
  → store         kitty/line.h:84-93  LineAttrs.prompt_kind (2 bits/line)
                  enum kitty/data-types.h:208
  → reconstruct   kitty/screen.c:4522  find_cmd_output()  (walks prompt_kind marks)
                  kitty/screen.c:4658  cmd_output()       (renders line range to text)
  → exit code     kitty/window.py:260  Window.last_cmd_exit_status  (single scalar,
                  set window.py:1774, overwritten each command)
```
- `@last_cmd_output` etc. (`boss.py:276-283`) all route through the mark-scan.
- Deep-scrollback fallback (`history.c:505-518`) re-finds boundaries by searching
  the raw bytes `\x1b]133;C\x1b\\` — reconstruction, not a stored index.
- No command object anywhere; exit code is a last-value scalar consumed for
  notifications.

## tmux — thinnest; only A/C; a richer version was reverted

```
OSC dispatch   input.c:2747  case 133 → input_osc_133()
  → handle     input.c:3171-3189
               'A' → gl->flags |= GRID_LINE_START_PROMPT   (input.c:3183)
               'C' → gl->flags |= GRID_LINE_START_OUTPUT   (input.c:3186)
               NO 'B', NO 'D' case → exit code never parsed/stored
  → store      tmux.h:805-806  two grid-line flag bits (that is the whole footprint)
  → consume    window-copy.c:6516  copy-mode next-prompt/previous-prompt
               cmd-capture-pane.c:368  capture-pane emits O/P markers
               screen-write.c:1620  flags preserved on scroll
```
- `struct grid_cell` / `struct grid_line` otherwise hold only visual state
  (glyph, attrs, colors, hyperlink) — no semantic field.
- tmux is a **multiplexer inside an outer terminal**; rich shell-integration UX
  is delegated outward. Unknown OSCs are dropped (logged), not forwarded; raw
  forwarding is a separate `DCS tmux;` passthrough gated by `allow-passthrough`
  (`input.c:2595-2657`).
- **HEAD `6fd9987` is a revert** of `f3c6b4f` "Add formats and events for OSC 133
  commands, as well as a -T flag" — i.e. a durable-records version existed and
  was backed out.

## Facts vs. assumptions (carried from the traces)
- _(assumption)_ tmux richer-version contents inferred from the revert message +
  absence of any command-record struct / format vars, not a line-by-line diff of
  `f3c6b4f` (the shallow clone lacks the parent object).
- _(assumption)_ WezTerm "no IPC command-history channel" is grep-based
  (no such struct exists to ship) rather than an exhaustive read of every mux
  serialization file.
- _(assumption, Kitty)_ not every kitten audited, but all named output/scroll
  paths route through the `find_cmd_output` mark-scan; no per-command record
  struct found repo-wide.
- _(fact)_ In all four terminals the exit code is either discarded (WezTerm,
  tmux) or kept only transiently and detached from any stored output (Ghostty
  event, Kitty scalar).
