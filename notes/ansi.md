# ANSI Escape Sequences

> Learning note. Facts cite source; assumptions are marked _(assumption)_.

## Question
How does text control color, cursor, and style via escape codes?

## Key concepts
- C0 / C1 control bytes
- CSI (Control Sequence Introducer) structure
- SGR (colors, styles), cursor movement, erase / scroll

## Findings

### C0 vs C1 controls
- **C0** = `0x00–0x1F` (+ DEL `0x7F`): BEL, BS, HT, LF, CR, ESC (`0x1B`), etc.
  These are `execute`d immediately from almost any parser state without aborting
  an in-progress sequence. Exceptions: **CAN (`0x18`)** and **SUB (`0x1A`)**
  cancel a sequence; **ESC (`0x1B`)** restarts one ("anywhere" transitions).
- **C1** = `0x80–0x9F`: the 8-bit forms of `ESC @`…`ESC _`. Key ones: **CSI =
  `0x9B`**, **OSC = `0x9D`**, **ST = `0x9C`**, **DCS = `0x90`**. (WezTerm maps
  these in its `anywhere_or` table, `vtparse/src/transitions.rs:31-40`.)

### CSI sequence structure
`CSI = ESC [` (or C1 `0x9B`) → **parameters** (digits, `;` separators, and `:`
sub-parameters) → **intermediates** (`0x20–0x2F`) → one **final** byte
(`0x40–0x7E`) that is dispatched. Example: `ESC [ 1 ; 31 m`.

Common finals:
- **SGR** (`m`) — colors/styles. `0` reset, `1` bold, `3` italic, `4` underline,
  `7` reverse; `30–37`/`40–47` 8-color fg/bg; `38;5;N`/`48;5;N` 256-color;
  `38;2;R;G;B` truecolor. Colon sub-params (`38:2:…`) are the ISO form —
  Ghostty patches its Williams table to accept `:` in params for this
  (`parse_table.zig:6-8`).
- **Cursor** — `A/B/C/D` up/down/right/left, `H` position (`row;colH`), `s`/`u`
  save/restore.
- **Erase** — `J` erase display, `K` erase line (with `0/1/2` variants).
- **Scroll** — `S`/`T` scroll up/down; `r` set scroll region.
- **DEC private modes** — `CSI ? Ph/l` set/reset (see `vt100.md`).

_(These are the ECMA-48 / DEC finals; the four terminals dispatch them from the
`csi_dispatch` action — `comparisons/parser.md`.)_

## Open questions
- Full SGR attribute inventory (blink, strikethrough, overline, underline styles).
- Mouse-tracking CSI modes and the SGR mouse encoding (ties to an input axis).

## Sources
- ECMA-48; vt100.net
- `../comparisons/parser.md`, `osc.md`, `vt100.md`
