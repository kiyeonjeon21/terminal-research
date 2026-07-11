# Result — 004-pty-tracing

> Empirical (like exp 003). Numbers/bytes from a real PTY-capture run; regenerate
> with `python3 harness.py`. Interpretation marked _(interpretation)_.

## Answer

You can observe everything a terminal and its shell say to each other by holding
the **PTY master** and logging both directions. Doing so makes the
`../../notes/pty.md` concepts concrete:

- **The echo you see when typing is the kernel's, not the program's.** Running
  `cat` and sending `hello` yields `hello` **twice** on the master — line-
  discipline echo + the program's output (scenario A). Clearing `ECHO`
  (`stty -echo`) removes the first copy (B). Newlines we send (`\n`) come back as
  `\r\n` via output post-processing.
- **A fresh PTY is cooked/canonical** — `ICANON/ECHO/ISIG/ICRNL/OPOST` all on (D).
  Raw-mode apps clear these.
- **Escape sequences are just bytes in the same stream.** A `printf` put a real
  OSC title (`\e]0;MyTitle\a`) and CSI SGR colors (`\e[1;31m…\e[0m`) on the wire
  (C) — the exact grammar the parsers in `../../comparisons/parser.md` consume.
- **Resize is `TIOCSWINSZ` on the master → the kernel raises `SIGWINCH`.** Setting
  24×80 → 30×100 mid-run made the child's trap re-read `stty size` as `30 100`
  (E), exactly the path all four terminals use (e.g. Ghostty `pty.zig:221`).

## Evidence
- `captures/RESULTS.txt` — escaped byte transcripts of scenarios A–E.
- `harness.py` — the reproducible bidirectional PTY tracer + termios dump.

## Why it matters (interpretation)

_(interpretation)_ This closes the loop across the whole repo: the abstract PTY /
termios / escape-sequence facts (notes) and the four terminals' cited
`openpty`/`TIOCSWINSZ`/parser code (comparisons) all show up as concrete bytes in
one small harness. The "terminal ↔ shell" boundary that every experiment here
depends on — command markers (001–003, 006), cwd (005), control APIs (007) — is
just this bidirectional byte stream over a PTY, with a line discipline in the
middle. Seeing it directly demystifies the rest.

## Open questions / next
- Raw-mode capture of a real TUI (vim/htop) to see the full-screen escape traffic
  and mouse/kitty-keyboard sequences (ties to `../../comparisons/input.md`).
- Trace a shell with real integration sourced to see OSC 133 markers alongside
  the echo (bridges exp 003 and this).
