# Notes — 004-pty-tracing

Empirical run via `harness.py` (PTY byte capture). Escaped transcripts in
`captures/RESULTS.txt`. Regenerate with `python3 harness.py`.

## Observed

### A — cooked-mode echo (the line discipline, not the program)
```
IN  → child:  hello\n
OUT ← child:  hello\r\nhello\r\n
```
We ran `cat`, which re-emits its stdin **once**. The output contains `hello`
**twice** — the first copy is the **kernel line discipline echoing** our typed
input back (because `ECHO` is on), the second is `cat`'s own output. Also note
`\n` (what we sent) becomes `\r\n` on the way out (`OPOST`/`ONLCR` output
processing). The `\x04` (Ctrl-D) shows as `^D\x08\x08` — the tty's visual echo of
the EOF control char.

### B — ECHO off
```
stty -echo; cat  →  OUT: hello\r\n   (once)
```
With `ECHO` cleared, the echoed copy is gone; only `cat`'s output remains. Proves
the duplicate in A was the line discipline, not the program.

### C — escape sequences on the wire
```
OUT ← child:  \e]0;MyTitle\a\e[1;31mBOLD-RED\e[0m\r\n
```
A single `printf` produced: an **OSC** window-title sequence `\e]0;MyTitle\a`
(BEL-terminated) and **CSI SGR** sequences `\e[1;31m` (bold red) … `\e[0m`
(reset). This is exactly the byte grammar the parsers in `../../comparisons/parser.md`
consume, and the OSC/CSI structure from `../../notes/osc.md` / `ansi.md`, seen raw
on the wire.

### D — a fresh PTY is cooked by default
```
ICANON on · ECHO on · ISIG on · ICRNL on · OPOST on
```
Confirms the default line discipline: line-buffered, echoing, signal-generating,
CR→NL input + output post-processing. Full-screen apps clear these for raw mode
(`../../notes/pty.md`).

### E — resize (TIOCSWINSZ → SIGWINCH)
```
OUT: READY at 24 80       (initial winsize)
     [master ioctl TIOCSWINSZ 30x100]
OUT: WINCH now 30 100      (trap fired; child re-read the new size)
```
Setting the winsize on the **master** raised **SIGWINCH** to the child, whose
trap re-read `stty size` and saw the new `30 100`. Directly demonstrates the
resize path from `../../notes/pty.md` and the four terminals' `TIOCSWINSZ` calls
(e.g. Ghostty `pty.zig:221`).

## Facts vs. assumptions
- _(fact)_ Every transcript is from a real capture in this environment (macOS,
  `/bin/sh`, python3 `pty`).
- _(fact)_ Winsize propagation master→slave verified in isolation (both ends read
  30×100 after one `TIOCSWINSZ`).
- _(gotcha, not a PTY fact)_ Scenario E first mis-reported the old size because a
  double-quoted `trap "… $(stty size)"` expands `$(…)` at trap-*set* time; the
  fix was single-quoting so it evaluates when the trap *fires*. A shell-quoting
  bug, not kernel behavior — noted so the harness stays trustworthy.
- _(scope)_ IUTF8 showed `n/a` — Python's `termios` on this build doesn't expose
  the constant; the flag exists at the OS level (Ghostty forces it, `pty.zig:176`).
