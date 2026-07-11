#!/usr/bin/env python3
"""Experiment 009 — raw-mode TUI capture.

Experiment 004 showed a fresh PTY is cooked/canonical. A full-screen TUI flips it
to RAW and drives the alternate screen. This runs real TUIs (vim, less) in a PTY
and captures:

  - the termios flip to raw (ICANON/ECHO/ISIG cleared) WHILE the TUI runs,
    contrasting exp 004's cooked defaults
  - the DEC private modes the TUI enables (alt screen ?1049, bracketed paste
    ?2004, app-cursor ?1, mouse ?1000/?1006, …) — the byte grammar of
    ../../comparisons/input.md, seen on the wire
  - alt-screen enter (?1049h) on start and leave (?1049l) on quit

Read-only w.r.t. the clones. Scratch captures under captures/ (gitignored except
RESULTS.txt).
"""
import os, pty, select, time, termios, re, tempfile, pathlib

HERE = pathlib.Path(__file__).resolve().parent
CAP = HERE / "captures"; CAP.mkdir(exist_ok=True)

MODE_RE = re.compile(rb'\x1b\[\?([0-9;]+)([hl])')   # DEC private set(h)/reset(l)
KNOWN = {
    "1": "app cursor keys (DECCKM)",
    "12": "cursor blink",
    "25": "cursor visible (DECTCEM)",
    "1000": "mouse: button tracking",
    "1002": "mouse: button+drag",
    "1006": "mouse: SGR encoding",
    "1049": "alternate screen buffer",
    "2004": "bracketed paste",
    "1004": "focus reporting",
    "47": "alt screen (legacy)",
    "1047": "alt screen (legacy)",
}

def run_tui(argv, quit_keys, settle=1.2, timeout=5.0):
    """Run argv in a PTY. After `settle`s snapshot the tty termios, then send
    `quit_keys`. Return (raw_output_bytes, termios_snapshot_or_None)."""
    pid, fd = pty.fork()
    if pid == 0:
        os.environ["TERM"] = "xterm-256color"
        os.execvp(argv[0], argv); os._exit(127)
    import fcntl, struct
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))
    out = bytearray(); start = time.time()
    snap = None; quit_sent = False
    while True:
        r, _, _ = select.select([fd], [], [], 0.1)
        now = time.time()
        if fd in r:
            try: d = os.read(fd, 4096)
            except OSError: break
            if not d: break
            out.extend(d)
        if snap is None and now - start > settle:
            try: snap = termios.tcgetattr(fd)   # the tty is shared master/slave
            except termios.error: snap = None
        if not quit_sent and now - start > settle + 0.2:
            try: os.write(fd, quit_keys)
            except OSError: pass
            quit_sent = True
        if now - start > timeout: break
    try: os.close(fd)
    except OSError: pass
    try: os.waitpid(pid, 0)
    except OSError: pass
    return bytes(out), snap

def termios_line(snap):
    if not snap: return "  (termios snapshot unavailable)"
    lflag = snap[3]
    def st(bit): return "off" if not (lflag & bit) else "on "
    return (f"  raw mode while running:  ICANON {st(termios.ICANON)} | "
            f"ECHO {st(termios.ECHO)} | ISIG {st(termios.ISIG)}   "
            f"(exp 004 cooked default: all on)")

def modes(raw):
    seen = []
    for m in MODE_RE.finditer(raw):
        for code in m.group(1).decode().split(";"):
            act = "enable" if m.group(2) == b"h" else "disable"
            seen.append((code, act))
    # de-dup preserving order
    uniq = []
    for x in seen:
        if x not in uniq: uniq.append(x)
    return uniq

def report(name, title, argv, quit_keys):
    raw, snap = run_tui(argv, quit_keys)
    (CAP / f"{name}.raw").write_bytes(raw)
    lines = [title, "-" * 72, f"  bytes captured: {len(raw)}", termios_line(snap),
             "  DEC private modes on the wire:"]
    ms = modes(raw)
    if not ms:
        lines.append("    (none seen)")
    for code, act in ms:
        lines.append(f"    \\e[?{code}{'h' if act=='enable' else 'l'}   "
                     f"{act:7} {KNOWN.get(code,'?')}")
    alt = any(c == "1049" for c, _ in ms)
    lines.append(f"  alternate screen used (?1049): {alt}")
    text = "\n".join(lines) + "\n"
    print(text)
    return text

def main():
    print("=" * 72); print("Experiment 009 — raw-mode TUI capture"); print("=" * 72)
    out = ["Experiment 009 — raw-mode TUI capture",
           "Regenerate with: python3 harness.py", "=" * 72, ""]

    # vim: the canonical raw-mode / alt-screen TUI. -u NONE -N -n = no config,
    # nocompatible, no swapfile. Quit: ESC then :q! Enter.
    tf = tempfile.NamedTemporaryFile(suffix=".txt", delete=False)
    tf.write(b"hello from a captured vim session\n"); tf.close()
    out.append(report("A_vim", "A — vim (raw mode + alternate screen)",
                      ["/usr/bin/vim", "-u", "NONE", "-N", "-n", tf.name],
                      b"\x1b:q!\r"))
    out.append("=" * 72 + "\n")
    os.unlink(tf.name)

    # less: pager, also raw + alt screen. Quit: q.
    tf2 = tempfile.NamedTemporaryFile(suffix=".txt", delete=False)
    tf2.write(b"\n".join(b"line %d" % i for i in range(1, 40))); tf2.close()
    out.append(report("B_less", "B — less (pager: raw mode + alternate screen)",
                      ["/usr/bin/less", tf2.name], b"q"))
    os.unlink(tf2.name)

    (CAP / "RESULTS.txt").write_text("\n".join(out))
    print("wrote captures/RESULTS.txt")

if __name__ == "__main__":
    main()
