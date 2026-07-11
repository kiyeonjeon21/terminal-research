# Experiments

Each experiment answers **one** question with a small, reproducible probe.

## Convention
One folder per experiment, numbered `NNN-short-slug/`, containing:

- `README.md` — the question and how to reproduce
- `notes.md`  — running observations while tracing
- `patch.diff`— any local change made to a cloned project (kept out of upstream)
- `result.md` — the answer + citations (`file:line`)

## Index
| # | Question | Status |
| - | -------- | ------ |
| 001 | How does Ghostty find command boundaries? | done |
| 002 | Do other terminals keep durable command records? (WezTerm/Kitty/tmux) | done |
| 003 | How is OSC 133 emitted and consumed? | todo |
| 004 | How can PTY traffic be traced? | todo |
| 005 | How does each terminal track cwd? (OSC 7 vs process inspection) | done |
| 006 | How do shell-integration scripts *emit* the markers? (interactivity gap) | done |
