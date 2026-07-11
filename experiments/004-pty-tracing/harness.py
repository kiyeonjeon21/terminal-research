#!/usr/bin/env python3
"""Experiment 004 — tracing PTY traffic.

Make the concepts in ../../notes/pty.md observable: allocate a real PTY, run
programs on the slave, and log the raw bytes crossing the master in BOTH
directions (input we write → child; output we read ← child). Demonstrates:

  A. cooked-mode echo — the kernel line discipline echoes input (not the program)
  B. ECHO off — `stty -echo` removes that echo
  C. escape sequences on the wire — a program's OSC/CSI bytes, raw
  D. termios flags — ICANON/ECHO/ISIG on a fresh PTY slave (cooked by default)
  E. resize — TIOCSWINSZ changes the child's view; on a running process the
     kernel raises SIGWINCH

Read-only w.r.t. the cloned projects (doesn't touch them at all). Scratch/raw
captures go under captures/ (gitignored except RESULTS.txt).
"""
import os, pty, select, time, termios, struct, fcntl, signal, pathlib

HERE = pathlib.Path(__file__).resolve().parent
CAP = HERE / "captures"
CAP.mkdir(exist_ok=True)
SH = "/bin/sh"

# ---- byte escaping for readable transcripts -------------------------------
def esc(b):
    out = []
    for c in b:
        if c == 0x1b: out.append("\\e")
        elif c == 0x07: out.append("\\a")
        elif c == 0x0d: out.append("\\r")
        elif c == 0x0a: out.append("\\n")
        elif c == 0x04: out.append("\\x04")
        elif 32 <= c < 127: out.append(chr(c))
        else: out.append("\\x%02x" % c)
    return "".join(out)

# ---- run a command in a PTY, capturing directional traffic ----------------
def trace(argv, script, winsize=(24, 80, 0, 0), timeout=4.0, on_ready=None):
    """script = list of (label, bytes_to_write). Returns a list of
    ('IN'|'OUT', bytes) events in wire order (best-effort)."""
    rows, cols, xp, yp = winsize
    pid, fd = pty.fork()
    if pid == 0:  # child: stdio is the slave
        os.execvp(argv[0], argv)
        os._exit(127)
    # parent holds the master fd
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, xp, yp))
    events = []
    queue = list(script)
    start = time.time()
    ready_fired = False
    while True:
        r, _, _ = select.select([fd], [], [], 0.15)
        if fd in r:
            try:
                data = os.read(fd, 4096)
            except OSError:
                break
            if not data:
                break
            events.append(("OUT", data))
            if on_ready and not ready_fired and on_ready[0].encode() in data:
                ready_fired = True
                on_ready[1](fd)
        elif queue:
            label, payload = queue.pop(0)
            os.write(fd, payload)
            events.append(("IN", payload))
        if time.time() - start > timeout:
            break
    try: os.close(fd)
    except OSError: pass
    try: os.waitpid(pid, 0)
    except OSError: pass
    return events

def render(name, title, events):
    lines = [title, "-" * 72]
    for direction, data in events:
        arrow = "IN  → child (we wrote)" if direction == "IN" else "OUT ← child (read from master)"
        lines.append(f"  [{arrow}] {esc(data)}")
    text = "\n".join(lines) + "\n"
    (CAP / f"{name}.txt").write_text(text)
    print(text)
    return events

# ---- D. termios inspection (no child needed) ------------------------------
def termios_report():
    master, slave = os.openpty()
    attrs = termios.tcgetattr(slave)
    iflag, oflag, cflag, lflag, ispeed, ospeed, cc = attrs
    def on(flag, bit): return "on " if flag & bit else "off"
    rep = [
        "D — termios flags on a fresh PTY slave (cooked/canonical by default)",
        "-" * 72,
        f"  ICANON (line buffering) : {on(lflag, termios.ICANON)}",
        f"  ECHO   (echo input)     : {on(lflag, termios.ECHO)}",
        f"  ISIG   (Ctrl-C→SIGINT)  : {on(lflag, termios.ISIG)}",
        f"  ICRNL  (CR→NL on input) : {on(iflag, termios.ICRNL)}",
        f"  OPOST  (output post-proc): {on(oflag, termios.OPOST)}",
        f"  IUTF8  (UTF-8 input)    : {on(iflag, getattr(termios,'IUTF8',0)) if hasattr(termios,'IUTF8') else 'n/a'}",
    ]
    os.close(master); os.close(slave)
    text = "\n".join(rep) + "\n"
    (CAP / "D_termios.txt").write_text(text)
    print(text)

def main():
    print("=" * 72)
    print("Experiment 004 — tracing PTY traffic")
    print("=" * 72)

    # A. cooked-mode echo: `cat` just re-emits its stdin; the DUPLICATE of our
    #    input in the output is the kernel line discipline echoing.
    render("A_cooked_echo",
           "A — cooked mode: line-discipline ECHO (run `cat`, send 'hello')",
           trace([SH, "-c", "cat"], [("type", b"hello\n"), ("eof", b"\x04")]))

    # B. ECHO off: same, but `stty -echo` first → no echoed copy.
    render("B_echo_off",
           "B — ECHO off: `stty -echo; cat` → the echoed copy disappears",
           trace([SH, "-c", "stty -echo; cat"],
                 [("type", b"hello\n"), ("eof", b"\x04")]))

    # C. escape sequences on the wire: a program emits OSC (title) + CSI (SGR).
    render("C_escape_seqs",
           "C — escape sequences on the wire (OSC title + CSI SGR color)",
           trace([SH, "-c", r"printf '\033]0;MyTitle\007\033[1;31mBOLD-RED\033[0m\n'"],
                 []))

    # D. termios flags on a fresh PTY.
    termios_report()

    # E. resize: run a process that traps SIGWINCH; mid-run we TIOCSWINSZ the
    #    master → kernel raises SIGWINCH → child re-reads size with `stty size`.
    def do_resize(fd):
        fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", 30, 100, 0, 0))
    # NOTE: the trap body MUST be single-quoted so `$(stty size)` is evaluated
    # when the trap FIRES, not when `trap` is parsed (double quotes would bake in
    # the pre-resize size).
    script_e = [SH, "-c",
                "trap 'echo WINCH now $(stty size)' WINCH; "
                "echo READY at $(stty size); sleep 2; echo DONE"]
    render("E_resize",
           "E — resize: TIOCSWINSZ 24x80 → 30x100 mid-run raises SIGWINCH",
           trace(script_e, [], winsize=(24, 80, 0, 0), timeout=5.0,
                 on_ready=("READY", do_resize)))

    print("=" * 72)
    print("captures written to captures/*.txt ; see RESULTS.txt for the bundle")

if __name__ == "__main__":
    main()
