# 003-osc133

## Question
Experiment 006 concluded (from reading the shell-integration scripts) that OSC
133 / OSC 7 markers are emitted **only** by an interactive shell driven through a
prompt cycle — so a non-interactive/agent command emits nothing. **This
experiment tests that empirically** by running real shells in a PTY and capturing
the raw byte stream.

## Method
`harness.py` uses Python's `pty.fork` to allocate a real pseudo-terminal, spawns
a shell, feeds it `echo hello` + `exit`, and captures every byte the shell writes
to the PTY master. It then extracts the OSC 133 (`\e]133;…`) and OSC 7
(`\e]7;…`) sequences.

Read-only w.r.t. the clones: the harness only **reads** the shipped scripts under
`../../projects/…/shell-integration/`; it never modifies them. Scratch files and
raw captures go under `captures/` (gitignored except `RESULTS.txt`).

## How to run
```sh
cd experiments/003-osc133
python3 harness.py          # prints per-scenario marker counts + a verdict
```
Requires bash ≥ 4.4 (here `/opt/homebrew/bin/bash` 5.3, for `PS0`), zsh, python3.

## Scenarios
| # | Shell | Mode | Integration | Expectation |
| - | ----- | ---- | ----------- | ----------- |
| A | bash 5.3 | interactive | faithful minimal (mirrors exp 006) | markers present |
| B | bash 5.3 | **non-interactive** (`bash -c`) | same, sourced | **no markers** |
| C | bash 5.3 | non-interactive | **real** kitty.bash / ghostty.bash | guard trips, hooks not installed |
| C2| bash 5.3 | interactive | **real** kitty.bash | real markers present |
| D | zsh 5.9 | interactive | faithful minimal | markers present (cross-shell) |

## Results
See `captures/RESULTS.txt` for the escaped byte transcripts, `notes.md` for the
observations, and `result.md` for the verdict.
