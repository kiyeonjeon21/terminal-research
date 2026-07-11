# 004-pty-tracing

## Question
How can we observe the raw bytes flowing across the PTY master/slave, and see the
`../../notes/pty.md` concepts (line discipline, raw/cooked, escape sequences,
resize) happen for real?

## Method
`harness.py` allocates a real PTY (`pty.fork`), runs small programs on the slave,
and logs every byte crossing the master in **both directions** — input we write
(→ child) and output we read (← child) — with control chars escaped. Plus a
`termios` dump of a fresh PTY slave.

Read-only w.r.t. the clones (doesn't touch them). Scratch captures go under
`captures/` (gitignored except `RESULTS.txt`).

## How to run
```sh
cd experiments/004-pty-tracing
python3 harness.py          # prints all scenarios; writes captures/*.txt
```
Requires python3 (uses `pty`, `termios`, `fcntl`, `struct`). macOS/Linux.

## Scenarios
| # | Shows | How |
| - | ----- | --- |
| A | cooked-mode **echo** comes from the kernel line discipline, not the program | run `cat`, send `hello` → output has `hello` **twice** (echo + cat) |
| B | `ECHO` off removes that echo | `stty -echo; cat` → `hello` once |
| C | **escape sequences on the wire** | a program emits OSC title + CSI SGR; capture the raw `\e]…\a` / `\e[…m` bytes |
| D | a fresh PTY is **cooked/canonical** by default | dump `ICANON/ECHO/ISIG/…` termios flags |
| E | **resize**: `TIOCSWINSZ` mid-run raises `SIGWINCH`; child re-reads size | trap SIGWINCH, resize 24×80→30×100, child prints new `stty size` |

## Results
See `captures/RESULTS.txt` for the byte transcripts, `notes.md` for observations,
`result.md` for the takeaways.
