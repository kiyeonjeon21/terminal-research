# Result — 009-raw-mode-tui

> Empirical. Real vim/less runs captured in a PTY; regenerate with
> `python3 harness.py`. Interpretation marked _(interpretation)_.

## Answer

A full-screen TUI turns the PTY from cooked to **raw** and takes over the screen
via the **alternate buffer** — both observable directly:

- **Raw mode:** while vim/less run, `ICANON` and `ECHO` are **off** (exp 004's
  fresh PTY had them on). Keystrokes reach the app immediately, unbuffered and
  unechoed. **vim also clears `ISIG`** (Ctrl-C is a vim command); **less keeps
  `ISIG`** — "raw mode" is a chosen subset of termios flags, not a single switch.
- **Alternate screen:** `\e[?1049h` on entry, `\e[?1049l` on quit — a separate
  buffer, so shell scrollback is preserved.
- **Negotiated input modes:** vim enables bracketed paste (`?2004`), focus
  reporting (`?1004`), and app cursor keys (`?1`); less only the minimal set. Each
  is symmetrically disabled before exit. These are the exact DEC modes catalogued
  in `../../comparisons/input.md`, seen on the wire.

## Evidence
- `captures/RESULTS.txt` — per-TUI termios snapshot + DEC-mode inventory.
- `captures/*.raw` (gitignored) — full escape traffic.
- `harness.py` — the PTY TUI runner + termios/mode extractor.

## Why it matters (interpretation)

_(interpretation)_ This is the mirror of experiment 004. There we saw the *cooked*
default (line-discipline echo, line buffering); here we see a real program flip to
*raw* and drive the modes from `input.md` live. Together they bracket the two
worlds a terminal serves — the line-oriented shell and the full-screen app — over
the same PTY byte stream. It grounds the input/keyboard and PTY comparison docs in
observable behavior, closing the empirical side of the breadth study.

## Open questions / next
- Enable mouse in vim (`:set mouse=a`) and capture the `?1000`/`?1006` negotiation
  + an actual SGR mouse report.
- Capture the Kitty keyboard protocol handshake (`CSI > … u`) from a program that
  requests it (ties to `../../comparisons/input.md`).
