# PTY (Pseudo-terminal)

> Learning note. Facts cite source; assumptions are marked _(assumption)_.

## Question
What is a PTY and how does a terminal emulator use it?

## Key concepts
- Master / slave (control / subordinate) pair
- `forkpty()` / `openpty()`
- shell ↔ PTY ↔ terminal-emulator relationship
- line discipline, `termios`, raw vs cooked; controlling tty + `setsid`; SIGWINCH

## Findings

### The master/slave pair
A PTY is a bidirectional pipe with a terminal personality. `openpty()` returns
two fds: the **master** (kept by the emulator — reads child output, writes
keystrokes) and the **slave** (`/dev/pts/N`, becomes the child's stdin/out/err
via `dup2`). Write to master → appears as input on slave; child writes on slave
→ read from master. (Kitty makes the `dup2` explicit, `child.c:147-155`.)

### Line discipline / termios (raw vs cooked)
The slave sits behind the kernel line discipline. Default **cooked/canonical**
mode buffers a line, echoes, handles erase, and turns control chars into signals
(Ctrl-C→SIGINT, Ctrl-Z→SIGTSTP). Key `termios` flags: `ICANON` (line buffering),
`ECHO`, `ISIG`. Full-screen apps switch the tty to **raw** (flags cleared) so
every byte arrives immediately, no echo, no signals. `IUTF8` marks input UTF-8
for correct multibyte erase — Ghostty forces it on (`pty.zig:176`), tmux in the
child (`spawn.c:465`).

### openpty vs forkpty
`openpty()` only *allocates* the pair — Ghostty/WezTerm/Kitty use it so they can
fork separately and run custom pre-exec logic. `forkpty()` = `openpty()` +
`fork()` + child `setsid()` + make slave controlling tty + `dup2` — tmux uses it
(via `fdforkpty`). Splitting the steps buys control over signals, fd hygiene, and
env right before exec, which is why GUI terminals prefer `openpty`.

### Controlling tty + session (setsid) — the child ritual
All four run the same POSIX ritual in the child: reset signals to `SIG_DFL` →
`setsid()` (new session leader, no ctty) → `ioctl(slave, TIOCSCTTY, 0)` (acquire
controlling tty). Verified: Ghostty `pty.zig:251,254`, WezTerm `unix.rs:257,271`,
Kitty `child.c:114,120`; tmux via `forkpty`. This enables job control and lets
the kernel deliver terminal signals (SIGINT/SIGHUP/**SIGWINCH**) to the child's
process group.

### SIGWINCH (resize) propagation
The emulator never sends SIGWINCH directly. It calls
`ioctl(master, TIOCSWINSZ, &winsize)` with new rows/cols — Ghostty `pty.zig:221`,
WezTerm `unix.rs:189`, Kitty `child-monitor.c:618`, tmux `window.c:492`. The
**kernel** then raises SIGWINCH to the tty's foreground group; the app re-reads
size via `TIOCGWINSZ`. Skipping `TIOCSCTTY` breaks this (WezTerm notes it,
`unix.rs:266-270`).

### Exit detection
Master read returns EOF (or `EIO` on Linux, which WezTerm maps to EOF
`unix.rs:96`) when the slave closes, but the authoritative status comes from
`waitpid()`, driven by `SIGCHLD` (Kitty `child-monitor.c:1534/1584`, tmux
`server.c:463/469`) or a wait mechanism (Ghostty xev `p.wait`, WezTerm a
`process.wait()` thread). Killed-by-signal N → exit code `128+N` (tmux
`server-fn.c:343`).

### Why TERM / terminfo matters
`TERM` names a terminfo entry telling apps which sequences the terminal supports.
Each ships one matching its capabilities and must make it available:

| Terminal | default TERM | terminfo delivery |
| -------- | ------------ | ----------------- |
| Ghostty | `xterm-ghostty` (`Config.zig:3762`) | bundled `TERMINFO` dir; downgrades to `xterm-256color` |
| WezTerm | `xterm-256color` (`config.rs:1738`) | ships a `wezterm` entry, defaults to the universal one |
| Kitty | `xterm-kitty` (`definition.py:2591`) | bundled + base64-embedded (to push over SSH) |
| tmux | `screen` (`tmux.h:97`) | expects the multiplexer entry; users set `tmux-256color` |

All four set `COLORTERM=truecolor` (out-of-band 24-bit color signal) and
`TERM_PROGRAM`/`_VERSION` (emulator fingerprint).

## Process-model contrast (I/O loop)
| Terminal | I/O model |
| -------- | --------- |
| Ghostty | dedicated reader **thread** per pane, 4-buffer gather/parse pipeline (`Exec.zig:1279`) |
| WezTerm | per-pane reader **thread**, blocking read (`mux/src/lib.rs:279`) |
| Kitty | single C **`poll()` loop** thread for all children (`child-monitor.c:1675`) |
| tmux | libevent **`bufferevent` per pane** on one server event loop (`window.c:1338`) |

_(interpretation)_ tmux is unique: a long-lived **server** that allocates a PTY
per pane while itself sitting behind another terminal's PTY — hence the "terminal
inside a terminal" behavior seen in exp 002/005/007.

## Open questions
- Login-shell handling differs (Kitty may wrap in `login` on macOS; tmux uses
  `-shell`) — config-dependent.
- Empirical PTY byte tracing → `../experiments/004-pty-tracing/` (todo).

## Sources
- POSIX termios / `openpty(3)` / `forkpty(3)`; per-terminal files cited above
