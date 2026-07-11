# Input / Keyboard / Mouse

> Learning note. Facts cite source; assumptions are marked _(assumption)_.

## Question
How do key presses, modifiers, mouse, paste, and focus become bytes sent to the
child — and why is the legacy scheme being replaced?

## Key concepts
- legacy (xterm) key encoding and its ambiguity
- the Kitty keyboard protocol (CSI u) + modifyOtherKeys
- mouse tracking modes & SGR encoding
- bracketed paste, focus reporting

## Findings

### Why legacy key encoding is ambiguous
Control chars collide with named keys — same byte:
- `Ctrl-I` = `0x09` = **Tab**; `Ctrl-M` = `0x0D` = **Enter**; `Ctrl-[` = `0x1B`
  = **Esc**. The receiver can't tell which physical key was pressed.
- Most keys can't report modifiers at all (an unmodified letter and its Ctrl form
  map to one C0 byte); tmux's legacy path explicitly discards modifiers on Unicode
  keys (`input-keys.c:498`).
- Alt/Meta = an ESC prefix (`\x1b` + key) — ambiguous with a real Esc then a key
  (timing-dependent).
- Arrows/function keys use `CSI` (`\x1b[`) normally, `SS3` (`\x1bO`) in
  application-cursor mode (DECCKM) — same key, different bytes by mode.

### What the Kitty keyboard protocol fixes
Kitty (kovidgoyal) invented it to replace the above. Every key is reported
unambiguously as `CSI unicode-key ; modifiers [; text] u` (functional keys use a
`~`/letter trailer), so `Ctrl-I`/`Tab`, `Ctrl-M`/`Enter`, `Esc`/`Ctrl-[` are all
distinguishable and modifiers attach to *any* key.

Opt-in via a **progressive-enhancement handshake** — a per-screen 5-bit flag
stack: `disambiguate`, `report_events` (press/repeat/release),
`report_alternates`, `report_all`, `report_associated` (text). Sequences:
- `CSI > flags u` — push a flag set
- `CSI < number u` — pop
- `CSI = flags ; mode u` — set (mode 1 all / 2 set-specified / 3 clear-specified)
- `CSI ? u` — query → terminal replies `CSI ? flags u`

Reference router: Kitty `vt-parser.c:1312-1333`. Ghostty and WezTerm implement it
fully; tmux only does the `extended-keys` CSI-u/xterm *encoding*, not the stack.

### modifyOtherKeys (xterm's earlier partial fix)
`CSI > 4 ; 1|2 m` makes xterm emit `CSI 27 ; mods ; key ~` for keys that
otherwise couldn't carry modifiers. Less complete than CSI u (no release events,
no text, no stack). Ghostty/WezTerm/tmux support it; **Kitty rejects it**
(`screen.c:1782`) telling apps to use its protocol.

### Mouse tracking
- *What* to track (DEC modes): `?1000` press/release, `?1002` + drag (button
  held), `?1003` any motion.
- *How* to encode: default X10 (`\x1b[M`+3 bytes biased by 32; breaks past col
  223), `?1005` UTF-8, **`?1006` SGR** (modern default), `?1015` urxvt, `?1016`
  SGR-pixels.
- **SGR** = `CSI < button ; x ; y M` (press/drag) / `… m` (release): decimal
  coords (no 223 limit), explicit press-vs-release. All four support it.

### Bracketed paste `?2004` — a security feature
Pasted text is wrapped in `\x1b[200~ … \x1b[201~` so the app distinguishes
*typed* from *pasted* input and won't auto-execute pasted control chars (e.g. a
shell won't run a pasted newline). Ghostty scans paste for a stray `201~` as
unsafe (`paste.zig:133`). _(Relevant to agent input injection: an agent pasting
into a shell should respect bracketed-paste framing.)_

### Focus reporting `?1004`
When enabled the terminal sends `CSI I` on focus-in, `CSI O` on focus-out (Kitty
`screen.c:5962`) — lets apps pause animations/refresh.

## Open questions
- The full modifier-encoding numeric scheme (shift=1, alt=2, ctrl=4, super=8 …).
- Key release events + how TUIs use them (games, modal editors).

## Sources
- `../comparisons/input.md`; Kitty `docs/keyboard-protocol.rst`; per-terminal
  input files cited there
