# 008-control-api-live

## Question
Experiment 007 mapped the control surfaces by *reading* source. Can we drive one
**for real** and see the protocol live? Specifically tmux control mode — the
`%output` push stream that exp 007 called "the closest thing to an agent event
bus that already ships."

## Scope (what's runnable here)
- **tmux `-C` control mode** — driven live (headless, no GUI). ✅
- **kitty `@`** — kitty is installed but is a **GUI app**; driving it would pop a
  window on the user's screen, so it is **not** run here. (Source-verified in
  exp 007.)
- **wezterm cli** — wezterm **not installed**. (Source-verified in exp 007.)

## Method
`harness.py` attaches a tmux **control client** (`tmux -C new-session …`) over a
PTY, writes plain tmux commands to its stdin, and captures the `%`-prefixed
protocol on stdout. Uses a **private socket** (`-L research-live-008`) and
`kill-server`s it at the end — the user's own tmux is never touched.

## How to run
```sh
cd experiments/008-control-api-live
python3 harness.py          # writes captures/RESULTS.txt; leaves no tmux server
```
Requires `/opt/homebrew/bin/tmux` (tested with 3.6a) + python3.

## What it exercises (→ exp 007 findings, live)
| Command sent | Demonstrates | Protocol seen |
| ------------ | ------------ | ------------- |
| `send-keys 'echo …' Enter` | input injection | `%output %0 …` (the echo streams back) |
| `capture-pane -p` | read pane content | `%begin … <text> … %end` |
| `new-window -n second` | spawn | `%window-add @1` |
| `list-windows -F …` | query state | framed `%begin/%end` output |
| (startup) | structural notifications | `%sessions-changed`, `%session-changed`, `%window-renamed` |

## Results
See `captures/RESULTS.txt` for the raw protocol transcript, `notes.md`,
`result.md`.
