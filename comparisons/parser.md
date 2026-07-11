# Escape-sequence Parser — Comparison

> Breadth/learning study (not the agent axis). How each terminal parses the
> VT/ANSI byte stream — the state machine, not the higher-level handlers. Cite
> `file:line`. Background facts in `../notes/vt100.md`, `../notes/ansi.md`,
> `../notes/osc.md`.

## Question
How does each terminal parse VT/ANSI/CSI/OSC/DCS input?

## The reference model
Three of four implement **Paul Williams' "DEC ANSI-compatible parser"**
(vt100.net/emu/dec_ansi_parser): states `GROUND → ESCAPE → CSI_ENTRY/PARAM/
INTERMEDIATE → …`, `OSC_STRING`, `DCS_*`, with exit-action → transition-action →
entry-action ordering. See `../notes/vt100.md`.

| Terminal | Parser style | State enum | SIMD / fast path | Williams cited |
| -------- | ------------ | ---------- | ---------------- | -------------- |
| **Ghostty** | table-driven Williams, **comptime-generated** table | `src/terminal/Parser.zig:15-30`; table `parse_table.zig` | **yes** — bulk UTF-8 decode of printable runs until `0x1B` (`src/simd/vt.zig`, `stream.zig:562`); scalar fallback | yes (`Parser.zig:3-4`) |
| **WezTerm** (`vtparse`) | table-driven Williams, **const-fn** packed-`u16` tables | `vtparse/src/enums.rs:36-60` (State), `:5-25` (Action) | no SIMD; `utf8parse` crate + dedicated `Utf8`/`Utf8Sequence` states; `get_unchecked`/`transmute` hot path | yes (`lib.rs:1-2`, ECMA-48) |
| **Kitty** | **hand-rolled switch** + CSI sub-states | `kitty/vt-parser.c:178-179` (`VTEState`), `:199` (CSI) | **yes, heaviest** — runtime AVX2/SSE4.2/NEON `utf8_decode_to_esc`, `find_either_of_two_bytes` (`simd-string.c`) | **no** (only "ECMA-48" in `control-codes.h:108`) |
| **tmux** | table-driven Williams, **fn-pointer range tables** | `input.c:360-365` (`input_state` objs), `:374-390` | no SIMD; last-transition cache + deferred `screen_write_collect` batching | yes (`input.c:32-34`) |

## Notes
- **Table materialization differs but converges:** Ghostty builds the 256×states
  table at *compile time*; WezTerm builds packed-`u16` tables via `const fn`;
  tmux walks sparse byte-range transition lists linearly (with a
  last-match cache). All three are the same Williams machine, different codegen.
- **Kitty is the outlier** — a coarse 8-state `switch`
  (`NORMAL/ESC/CSI/OSC/DCS/APC/PM/SOS`) with hand-written per-state consumers and
  a separate CSI sub-state machine. Correct, but not a 1:1 Williams mapping, and
  it doesn't cite the spec.
- **SIMD accelerates only the print/scan phase**, never control-sequence parsing
  (which is inherently sequential everywhere). Ghostty and Kitty bulk-decode
  printable UTF-8 runs until the next control byte; WezTerm and tmux stay scalar
  but batch prints into the grid collector.
- **Dispatch:** Ghostty `Parser.next()` (`Parser.zig:251`) returns a
  `[3]?Action` triple (exit/transition/entry); WezTerm unpacks `(action,state)`
  from a `u16` (`lib.rs:31-38`); tmux runs a function-pointer handler per
  transition (`input.c:955`); Kitty `switch (vte_state)` → per-state consumer
  (`vt-parser.c:1460`).
- **Documented spec deviation:** Ghostty allows `:` in `csi_param` for SGR
  sub-parameters (`parse_table.zig:6-8`) — the standard real-world patch to the
  Williams table for colon-separated SGR colors.

## Sources
Per-terminal parser files above; Williams reference at vt100.net/emu/dec_ansi_parser.
