# Result — 003-osc133

> First **empirical** experiment in this repo (001/002/005/006 were source
> reading). Numbers from a real PTY-capture run; regenerate with
> `python3 harness.py`. Interpretation marked _(interpretation)_.

## Answer

**Confirmed, on the wire:** OSC 133 / OSC 7 markers are emitted only by an
interactive shell driven through a prompt cycle. The exp-006 thesis is no longer
an inference from reading guards — it is observed.

The decisive pair (same script, same `echo hello`):

- **Interactive** (scenario A) — captured 389 bytes containing the full cycle
  `\e]133;D;0` → `\e]7;file://…` → `\e]133;A` … `\e]133;B` … `\e]133;C`
  (`A:2 B:2 C:2 D:2 OSC7:2`).
- **Non-interactive** `bash -c` (scenario B) — captured **7 bytes: `hello\r\n`**.
  Zero markers.

And with the **real shipped scripts**:
- Sourcing `kitty.bash` / `ghostty.bash` non-interactively → their interactive
  guard returns before installing any hook (`NO_HOOKS_INSTALLED`).
- Sourcing the *same* `kitty.bash` interactively → real markers appear, including
  `\e]7;kitty-shell-cwd://…`, `\e]133;C;cmdline=echo\ hello`, and `D;0`→`A` —
  verbatim confirmation of the specific claims in `../006-shell-emitters/`.

## Evidence
- `captures/RESULTS.txt` — escaped byte transcripts of scenarios A/B/C/C2/D.
- `captures/*.bin` — raw captures (gitignored; regenerate via `harness.py`).
- `harness.py` — the reproducible PTY capture harness.

## Why it matters (interpretation)

_(interpretation)_ This nails down the arc's central claim with a live artifact:
the byte stream a coding agent gets from a non-interactive command
(`hello\r\n`) is **structurally identical to a dumb terminal's** — no command
boundary, no cwd, no exit code, nothing. All the machinery from 001/002/005/006
sits behind a prompt cycle the agent doesn't have. An agent-native terminal has
to *produce* structure for programmatic execution (or expose an API the agent
drives), because the shell-integration path is, empirically, a no-op for it. See
`../../comparisons/agent-opportunities.md` (Finding #3).

## Open questions / next
- Drive the real ghostty.bash and a real zsh script interactively too (only
  kitty.bash was fully driven; others only guard-checked).
- Exercise the bash 3.2 → bundled `bash-preexec.sh` fallback path.
- Can a wrapper emit `\e]133;C`/`D` around a *non-interactive* command to make it
  visible to the terminal? (A concrete probe toward the Finding #3 opportunity.)
