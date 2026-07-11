# Notes — 009-raw-mode-tui

Real TUIs run in a PTY; termios snapshot + DEC-mode extraction. Full inventory in
`captures/RESULTS.txt`; regenerate with `python3 harness.py`.

## Observed

### vim (`-u NONE -N -n`)
```
raw mode while running:  ICANON off | ECHO off | ISIG off
DEC private modes on the wire (enter → leave):
  \e[?1049h  alternate screen        ... \e[?1049l
  \e[?1h     app cursor keys (DECCKM)... \e[?1l
  \e[?2004h  bracketed paste         ... \e[?2004l
  \e[?1004h  focus reporting         ... \e[?1004l
  \e[?12h/l  cursor blink   \e[?25l/h cursor visibility
alternate screen used: True
```

### less (pager)
```
raw mode while running:  ICANON off | ECHO off | ISIG on
DEC private modes:
  \e[?1049h  alternate screen ... \e[?1049l
  \e[?1h     app cursor keys  ... \e[?1l
alternate screen used: True
```

## Key observations
- **Cooked → raw is real and observable.** exp 004 showed a fresh PTY with
  `ICANON/ECHO/ISIG` all on; here, *while the TUI runs*, `ICANON`/`ECHO` are off —
  every keystroke reaches the app immediately, unbuffered and unechoed, so the app
  controls the screen fully.
- **ISIG is the interesting difference.** **vim clears `ISIG`** (Ctrl-C is a vim
  command, not SIGINT); **less keeps `ISIG` on** (Ctrl-C still interrupts). A
  concrete example that "raw mode" is not one setting but a chosen subset of
  termios flags.
- **The alternate screen** (`?1049h`/`?1049l`) is why a TUI doesn't clobber your
  shell scrollback: it swaps to a separate buffer on entry and restores on exit —
  symmetric enter/leave in both captures.
- **TUIs negotiate input modes up front.** vim enables **bracketed paste**
  (`?2004`, exp 004/`input.md`: distinguish typed vs pasted) and **focus
  reporting** (`?1004`) and **app cursor keys** (`?1`, changes arrow encoding to
  `SS3`) — the exact modes catalogued in `../../comparisons/input.md`, here on the
  wire. less negotiates only the minimal set.
- **Everything is cleaned up on quit** — each enabled mode has a matching disable
  before exit, so the shell returns to a sane state.

## Facts vs. assumptions
- _(fact)_ All values from real captures (vim 9.1, less, macOS, `TERM=
  xterm-256color`).
- _(note)_ The exact mode set depends on `TERM`/terminfo and program config; with
  a richer config vim would also enable mouse (`?1000`/`?1006`). `-u NONE` keeps
  it minimal and deterministic.
- _(scope)_ Full screen-draw traffic (cursor moves, SGR, clears) is in the `.raw`
  captures but summarized here as the mode inventory to stay readable.
