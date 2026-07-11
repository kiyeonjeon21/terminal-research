# 009-raw-mode-tui

## Question
Experiment 004 showed a fresh PTY is **cooked/canonical**. A full-screen TUI flips
it to **raw** and drives the **alternate screen**. What does that look like on the
wire, and which DEC private modes does a real TUI enable?

## Method
`harness.py` runs real TUIs (`vim`, `less`) in a PTY. While each runs it snapshots
the tty termios (to catch the raw-mode flip), extracts the DEC private modes the
program enables (`\e[?…h`) / disables (`\e[?…l`), then sends a quit key and
captures the alt-screen leave.

Read-only w.r.t. the clones. Scratch captures under `captures/` (gitignored except
`RESULTS.txt`).

## How to run
```sh
cd experiments/009-raw-mode-tui
python3 harness.py          # writes captures/RESULTS.txt
```
Requires `/usr/bin/vim`, `/usr/bin/less`, python3.

## What it shows
- **Raw mode** — `ICANON/ECHO` cleared while the TUI runs (vs exp 004's cooked
  defaults). vim also clears `ISIG` (handles Ctrl-C itself); less keeps `ISIG`.
- **Alternate screen** — `\e[?1049h` on entry, `\e[?1049l` on quit (so your shell
  scrollback is preserved).
- **The modes a TUI negotiates** — app cursor keys (`?1`), bracketed paste
  (`?2004`), focus reporting (`?1004`), cursor visibility (`?25`) — the byte
  grammar catalogued in `../../comparisons/input.md`, seen live.

## Results
See `captures/RESULTS.txt` (the mode inventory + termios per TUI), `notes.md`,
`result.md`.
