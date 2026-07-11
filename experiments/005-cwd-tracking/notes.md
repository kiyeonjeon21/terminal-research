# Notes — 005-cwd-tracking

Traces verified against the shallow clones. Punchlines spot-checked firsthand:
`tmux/input.c:2711`, `tmux/format.c:965`, `wezterm/.../performer.rs:936`,
`wezterm/.../localpane.rs:1061`, `kitty/window.py:166-176`,
`ghostty/src/terminal/osc.zig:799`.

## Ghostty — shell escape only (no process inspection)

```
OSC 7 parse    src/terminal/osc.zig:799  @"7" → parsers/report_pwd.zig:7  (raw string, no validation)
  (also OSC 1337 CurrentDir → same command:  osc/parsers/iterm2.zig:140-155)
  → handle     src/termio/stream_handler.zig:332 → reportPwd() :1132-1229
               empty URL → reset ("pwd unknown"); scheme must be file/kitty-shell-cwd;
               host must be LOCAL (internal_os.hostname.isLocal, :1193); percent-decode
  → store      src/terminal/Terminal.zig:68  pwd: std.ArrayList(u8)  (setPwd :3603, getPwd :3620)
  → seed       src/termio/Exec.zig:70  setPwd(cwd) at spawn (so first surface has a cwd pre-OSC7)
  → consume    window title fallback (stream_handler.zig:1224);
               new split/tab/window inherit (apprt/surface.zig:164-193, config toggles default true);
               relative-path resolution (Surface.zig:2065)
```
- **No `/proc`/process-cwd polling for cwd.** (The only `/proc` reads in the tree
  are kitty-graphics / systemd / cgroup — not cwd.) Ghostty trusts shell
  integration (OSC 7 / OSC 1337) entirely, plus the spawn-time seed.
- libghostty-vt path (`stream_terminal.zig:505`) stores the raw payload and
  defers decoding to the C embedder.

## WezTerm — OSC 7 primary, process fallback

```
OSC 7 parse    wezterm-escape-parser/src/osc.rs:466  "7" → SetCurrentWorkingDirectory
               → osc.rs:351 → CurrentWorkingDirectory(String)  (raw string)
  → handle     term/src/terminalstate/performer.rs:936-941
               self.current_dir = Url::parse(&url).ok()   (parse failure → None, silent)
               → Alert::CurrentWorkingDirectoryChanged
  → store      term/src/terminalstate/mod.rs:351  current_dir: Option<Url>   (get_current_dir :652)
  → consume    LocalPane::get_current_working_dir (mux/src/localpane.rs:512)
               spawn/split cwd inheritance (mux/src/lib.rs:1154/1218/1350, uses url.path())
               title refresh, Lua pane:get_current_working_dir
  → fallback   mux/src/localpane.rs:1061  divine_current_working_dir()
               reads the process leader's cwd when OSC 7 was never sent
```
- Host in the URL is not validated; consumers use only `url.path()` (host dropped).
- **OSC 1337 CurrentDir is parsed but IGNORED** — lands in the `_ =>` catch-all in
  the iTerm2 match (`performer.rs` ~856). Only OSC 7 updates `current_dir`.

## Kitty — process inspection default, OSC 7 override *only at the prompt*

```
OSC 7 dispatch kitty/vt-parser.c:527  case 7 → process_cwd_notification()
  → store      kitty/screen.c:3250  last_reported_cwd = raw bytes (NO parse, NO host check in C)
               (URL parsed later in Python: utils.py:967 path_from_osc7_url → unquote(urlparse.path);
                note: host is discarded, so no local-host check for OSC 7)
  → decide     kitty/window.py:166-176  CwdRequest.cwd_of_child:
               use OSC-7 value ONLY if  reported_cwd AND not child_is_remote
               AND (request == last_reported OR window.at_prompt)
               else → process inspection
  → process    kitty/child.py:508-543  cwd_of_process(pid):
               Linux realpath(/proc/<pid>/cwd); macOS macos_process_info.c:15;
               FreeBSD pwdx; foreground pgrp via os.tcgetpgrp
  → consume    new window/tab (--cwd current|last_reported|oldest|root, launch.py),
               session serialization, title matching
```
- Most defensive design: **distrusts OSC 7 mid-command** (only honors it when the
  cursor is at a shell prompt), and never trusts it across ssh (`child_is_remote`).
  Process inspection is the robust default.

## tmux — OSC 7 demoted to a cosmetic passthrough; real cwd = process inspection

```
OSC 7 dispatch input.c:2711  case 7 → screen_set_path(sctx->s, p, 1)  (input.c:2711-2716)
  → store      screen.c:264  s->path = clean_name(path)   (tmux.h:2034)  ← DISPLAY string only
  → surface    #{pane_path}  format.c:2334 (returns wp->base.path)
               forwarded UP to outer terminal: server-client.c:2382 tty_set_path()
REAL cwd (separate mechanism):
  #{pane_current_path}  format.c:957  format_cb_current_path → osdep_get_cwd(wp->fd)  (format.c:965)
    Linux   osdep-linux.c:63   tcgetpgrp + readlink(/proc/<pgrp>/cwd)
    macOS   osdep-darwin.c:71  tcgetpgrp + proc_pidinfo(PROC_PIDVNODEPATHINFO)
    *BSD    sysctl KERN_PROC_CWD
  new-window/pane cwd: server-client.c:2816 server_client_get_cwd (config→client→session→home)
```
- **OSC 7 never feeds cwd inheritance or `pane_current_path`.** Two entirely
  separate fields: `#{pane_path}` (OSC 7, display/passthrough) vs
  `#{pane_current_path}` (OS process inspection, authoritative).

## Facts vs. assumptions
- _(fact)_ All four parse OSC 7. Only Ghostty and WezTerm let it *set* the
  authoritative cwd; Kitty gates it behind at-prompt+not-remote; tmux ignores it
  for cwd entirely.
- _(fact)_ Process inspection: Kitty, WezTerm, tmux all read the OS process cwd;
  Ghostty does not.
- _(assumption)_ Ghostty "no cwd polling" is grep-based (no `/proc/<pid>/cwd`
  read found); shell-integration scripts under `src/shell-integration/` emit the
  OSC 7 it relies on (not read here).
- _(assumption)_ WezTerm OSC 1337-ignored confirmed by the missing match arm; not
  a full-tree grep for a second handler.
