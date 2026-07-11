# Result — 005-cwd-tracking

> Projects: the four shallow clones under `../../projects/`. Facts cite
> `file:line`; interpretation marked _(interpretation)_.

## Answer

All four terminals **parse OSC 7**, but they disagree sharply on *whether to
trust it*. The real axis is **shell-escape vs. OS-process** as the source of
truth for cwd:

| Terminal | Parses OSC 7 | Authoritative cwd source | Process-cwd inspection | OSC 1337 `CurrentDir` |
| --- | --- | --- | --- | --- |
| **Ghostty** | yes → `setPwd` (`osc.zig:799`, `Terminal.zig:3603`) | **shell escape only** (+ spawn-time seed `Exec.zig:70`) | **no** | **yes** — shares the OSC 7 handler (`iterm2.zig:140`) |
| **WezTerm** | yes → `current_dir: Option<Url>` (`performer.rs:936`, `mod.rs:351`) | OSC 7 primary; process fallback when absent | yes — `divine_current_working_dir` (`localpane.rs:1061`) | parsed but **ignored** (catch-all) |
| **Kitty** | yes → raw `last_reported_cwd` (`screen.c:3250`) | **process inspection default**; OSC 7 only *at the prompt* & not remote (`window.py:166-176`) | yes — `/proc/<pid>/cwd`, macOS syscall, `pwdx` (`child.py:508-543`) | n/a (uses `kitty-shell-cwd://` scheme) |
| **tmux** | yes → `s->path` (`input.c:2711`) | **process inspection only** (`osdep_get_cwd`, `format.c:965`) | yes — authoritative | n/a |

## The spectrum (most-trusting → least-trusting of the shell)

1. **Ghostty — trusts the shell completely.** OSC 7 (or iTerm2 OSC 1337) is the
   *only* way cwd updates after spawn; there is no process-cwd fallback. Cleanest
   model, but cwd is only as good as shell integration — no OSC 7 emitted → cwd
   goes stale (mitigated by validating the URL is a local `file://` host and
   resetting on an empty `7;`).
2. **WezTerm — prefers the shell, falls back to the OS.** OSC 7 sets
   `current_dir`; if it was never sent, `divine_current_working_dir` reads the
   process leader's cwd. No at-prompt gating — a mid-command OSC 7 is trusted.
3. **Kitty — trusts the OS, lets the shell override only when safe.** Process
   inspection is the default; the OSC-7 value is used *only* when the cursor is
   at a shell prompt and the child isn't a remote ssh session. The most defensive
   design — it explicitly distrusts a stale/mid-command OSC 7.
4. **tmux — ignores the shell for cwd.** OSC 7 is demoted to a cosmetic
   `#{pane_path}` (even forwarded up to the outer terminal via `tty_set_path`),
   while the authoritative `#{pane_current_path}` and new-pane cwd come purely
   from `osdep_get_cwd` (foreground pgrp → `/proc` / `proc_pidinfo`).

## Interpretation (agent angle)

_(interpretation)_ Unlike the command-record finding (experiment 002), here the
terminals genuinely **diverge** — and each choice has a different failure mode an
agent must know about:

- **OSC 7** is accurate for the *shell's* logical cwd and works across ssh (the
  shell re-emits it), but requires shell integration and is only trustworthy at a
  prompt (Kitty's insight). A terminal with no fallback (Ghostty) reports nothing
  useful if integration is missing.
- **Process inspection** always works locally without shell cooperation, but has
  a race (which foreground process?), can't see through ssh, and reports the OS
  cwd of a *process*, not the shell's logical cwd.

So "the pane's cwd" is not one fact — it has **provenance** (shell-reported vs
OS-observed) and **confidence** (at-prompt vs mid-command; local vs remote), and
today that metadata is collapsed to a single string with each terminal picking a
different policy. This is a smaller, concrete agent opportunity: expose cwd
*with* its provenance/confidence rather than a lossy single value. Recorded as
Finding #2 in `../../comparisons/agent-opportunities.md`.

## Open questions / next
- The shell-integration scripts (`src/shell-integration/` etc.) that actually
  emit OSC 7 — how do bash/zsh/fish hook it, and do they gate on prompt?
- Does any terminal reconcile a conflict between OSC-7 and process cwd, or is it
  strictly one-or-the-other?
- OSC 133 `aid` + cwd: could a command record (exp 002) carry the cwd it ran in?
