# OSC (Operating System Command)

> Learning note. Facts cite source; assumptions are marked _(assumption)_.

## Question
How do apps talk to the terminal beyond drawing text?

## Key concepts
- OSC / DCS / APC string sequences and their structure
- BEL vs ST terminators
- OSC 8 hyperlinks, OSC 52 clipboard, OSC 133 command boundaries, OSC 7 cwd, title

## Findings

### OSC vs DCS vs APC (the "string" sequences)
Unlike CSI (which has a fixed grammar and a final byte), these carry an
arbitrary string payload terminated by a string terminator:
- **OSC** = `ESC ]` (or C1 `0x9D`) → `code ; text` → terminator. App↔terminal
  side-channel: titles (`0`/`2`), colors (`4`/`10`/`11`), **hyperlinks (8)**,
  **clipboard (52)**, **cwd (7)**, **command marks (133)**.
- **DCS** = `ESC P` (or `0x90`) → params/intermediates → final (`hook`) →
  passthrough data (`put`) → terminator (`unhook`). Used for e.g. Sixel,
  terminfo queries, tmux passthrough (`DCS tmux; … ST`).
- **APC/PM/SOS** = `ESC _` / `ESC ^` / `ESC X` → opaque string → terminator.
  Application-private — **Kitty's graphics protocol uses APC**; Kitty remote
  control uses `DCS @kitty-cmd … ST` (see `../experiments/007-control-api/`).

### BEL vs ST terminators
A string sequence ends with either:
- **ST** = `ESC \` (`0x1B 0x5C`; canonical C1 form `0x9C`), or
- a bare **BEL** (`0x07`) — accepted for OSC by widespread convention.

Real terminals accept both for OSC. Verified handling: Kitty scans for either in
one SIMD pass (`find_st_terminator`, `vt-parser.c:369-393`); tmux records which
fired via `INPUT_END_ST` / `INPUT_END_BEL` (`input.c:55-57`), and downstream
handlers (OSC-8, OSC-52) branch on it. Ghostty's OSC has a dedicated parser
(`osc.zig`) handling BEL-vs-ST on exit.

### The OSC codes studied in this repo
| OSC | Purpose | Where studied |
| --- | ------- | ------------- |
| 7 | cwd reporting (`file://…` / `kitty-shell-cwd://…`) | `../experiments/005-cwd-tracking/` |
| 8 | hyperlinks | (touched) |
| 52 | clipboard read/write | (touched) |
| 133 | semantic prompt / command marks (A/B/C/D) | `../experiments/001…003,006` |
| 1337 | iTerm2 proprietary (CurrentDir, SetUserVar) | exp 005, 007 |

## Open questions
- OSC 52 clipboard: how each terminal gates read vs write (security).
- OSC 8 hyperlink id/uri handling and the local-host check (Kitty).

## Sources
- ECMA-48; xterm ctlseqs; the semantic-prompts spec
- `../comparisons/parser.md`; experiments 001–007
