# 005-cwd-tracking

## Question
How does each terminal know a pane's **current working directory**? Specifically:
does it trust the shell's **OSC 7** escape (`ESC ] 7 ; file://host/path ST`), read
the **OS process cwd** directly, or both? This fills the `OSC 7 (cwd)` columns
left TBD in `../../comparisons/shell-integration.md`.

## Setup / how to reproduce
Static source trace — no build. Read-only against the shallow clones under
`../../projects/`. Entry points:

**Ghostty** (`projects/ghostty`)
```sh
grep -n 'report_pwd\|@"7"' src/terminal/osc.zig
grep -n "fn reportPwd\|setPwd" src/termio/stream_handler.zig src/terminal/Terminal.zig
```

**WezTerm** (`projects/wezterm`)
```sh
grep -rn "CurrentWorkingDirectory\|current_dir\|divine_current_working_dir" \
  wezterm-escape-parser/src/osc.rs term/src/terminalstate/ mux/src/localpane.rs
```

**Kitty** (`projects/kitty`)
```sh
grep -n "process_cwd_notification\|last_reported_cwd" kitty/screen.c kitty/vt-parser.c
grep -n "cwd_of_child\|cwd_of_process\|get_foreground_cwd" kitty/window.py kitty/child.py
```

**tmux** (`projects/tmux`)
```sh
grep -n "case 7:\|screen_set_path" input.c
grep -n "format_cb_current_path\|osdep_get_cwd\|pane_current_path\|pane_path" format.c
```

## Steps
See `notes.md` for the four traces and `result.md` for the unified answer + the
"shell-escape vs. OS-process" axis.
