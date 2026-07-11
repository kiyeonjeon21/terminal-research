# Notes — 003-osc133

Empirical run via `harness.py` (PTY capture). Numbers below are from an actual
run; regenerate with `python3 harness.py`. Raw bytes in `captures/*.bin`, escaped
transcript in `captures/RESULTS.txt`.

## Observed results

| Scenario | Bytes | OSC markers captured |
| -------- | ----- | -------------------- |
| A — bash interactive + mini | 389 | `A:2 B:2 C:2 D:2 OSC7:2` |
| B — bash **non-interactive** + mini | 7 | **(none)** — bytes are exactly `hello\r\n` |
| C — real kitty.bash / ghostty.bash, non-interactive | — | `NO_HOOKS_INSTALLED` (guard trips) |
| C2 — **real kitty.bash**, interactive | 878 | `A:2 C:2 D:2 OSC7:1 k:16` |
| D — zsh interactive + mini | 637 | `A:2 B:2 C:2 D:2 OSC7:2` |

Two prompts fire in the interactive runs (initial prompt + the one after `echo
hello`), hence the `:2` counts; `C` fires per command line entered.

## Key observations

- **A vs B is the whole thesis.** Identical integration script, identical command
  (`echo hello`). Interactive → full `D → OSC7 → A … B … C` cycle on the wire.
  Non-interactive `bash -c` → the capture is literally `hello\r\n`, nothing else.
  The markers are a property of the *prompt cycle*, not of the command.

- **The real scripts confirm it too.** `C` sources the shipped `kitty.bash` /
  `ghostty.bash` in a non-interactive shell: their top-of-file interactive guard
  (`kitty.bash:3`, `ghostty.bash:19`) returns before any hook is installed →
  `NO_HOOKS_INSTALLED`. `C2` sources the *same* `kitty.bash` interactively and the
  real markers appear.

- **C2 empirically validates exp 006's specific claims** — captured verbatim from
  the real kitty.bash:
  - OSC 7 uses the `kitty-shell-cwd://` scheme (not `file://`) — matches
    `../006-shell-emitters/` and `../005-cwd-tracking/`.
  - `\e]133;C;cmdline=echo\ hello` — the `cmdline=%q` on the C marker
    (`kitty.bash:227`), carrying the command text.
  - Order `\e]133;D;0` then `\e]133;A` at the prompt — the combined `D;$?`+`A`
    PS1 emission (`kitty.bash:258`).
  - `\e]133;k;start_kitty` / `end_kitty` delimiters — kitty's internal
    `133;k;<name>_kitty` prompt-wrapping marks (`kitty.bash:145`), not semantic
    A/B/C/D.

- **Cross-shell (D):** zsh 5.9 with a minimal `add-zsh-hook precmd/preexec`
  integration emits the same A/B/C/D + OSC7 — the mechanism isn't bash-specific.

## Facts vs. assumptions
- _(fact)_ Every number and byte sequence above is from a real capture in this
  environment (bash `/opt/homebrew/bin/bash` 5.3.9, zsh 5.9, macOS).
- _(fact)_ The non-interactive-emits-nothing result now rests on direct
  observation, not just the guard-reading inference of exp 006.
- _(assumption / scope)_ The "mini" bash/zsh integrations are faithful
  reconstructions of the exp-006 mechanism, not the shipped scripts; scenarios C
  and C2 use the real scripts to close that gap for bash+kitty. ghostty/zsh real
  scripts were only checked for the guard (C), not fully driven interactively.
- _(note)_ `PS0`-based `C` needs bash ≥ 4.4; macOS system bash is 3.2, so the
  harness pins Homebrew bash 5.3. On bash 3.2 the real scripts fall back to a
  bundled `bash-preexec.sh` (exp 006) — not exercised here.
