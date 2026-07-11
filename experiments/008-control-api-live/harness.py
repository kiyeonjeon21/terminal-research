#!/usr/bin/env python3
"""Experiment 008 — driving a control API for real (tmux control mode).

Experiment 007 mapped the control surfaces by reading source. This drives the one
runnable headless: tmux control mode (`tmux -C`). We attach a control client over
a PTY, send plain tmux commands on its stdin, and capture the `%`-prefixed
protocol stream — proving live the exp-007 findings:

  - input injection via `send-keys`
  - the `%output %<pane>` PUSH stream (unsolicited pane bytes)
  - `%begin`/`%end` command framing (correlatable by number)
  - structural notifications (`%window-add`, `%session-changed`, …)

kitty @ / wezterm cli are NOT driven here: kitty needs a GUI window (would pop one
on the user's screen) and wezterm isn't installed. See result.md.

Uses a PRIVATE tmux socket (`-L <label>`) and kills that server at the end, so the
user's own tmux is never touched. Cloned projects are not touched at all.
"""
import os, pty, select, time, subprocess, pathlib

HERE = pathlib.Path(__file__).resolve().parent
CAP = HERE / "captures"; CAP.mkdir(exist_ok=True)
TMUX = "/opt/homebrew/bin/tmux"
SOCK = "research-live-008"   # private socket label

def esc(b):
    out=[]
    for c in b:
        if c==0x1b: out.append("\\e")
        elif c==0x0d: out.append("\\r")
        elif c==0x0a: out.append("\\n\n")   # real newline for readability
        elif c==0x07: out.append("\\a")
        elif 32<=c<127: out.append(chr(c))
        else: out.append("\\x%02x"%c)
    return "".join(out)

def drive(argv, script, settle=0.6, timeout=8.0):
    """Spawn argv in a PTY; run `script` = list of (delay, bytes). Capture all
    master output. Returns raw bytes."""
    pid, fd = pty.fork()
    if pid==0:
        os.environ["PATH"]="/opt/homebrew/bin:/usr/bin:/bin"
        os.execvp(argv[0], argv); os._exit(127)
    out=bytearray(); start=time.time(); step=0; last=start
    # write initial delay
    queue=list(script)
    next_at=start+ (queue[0][0] if queue else 0)
    while True:
        r,_,_=select.select([fd],[],[],0.1)
        now=time.time()
        if fd in r:
            try:d=os.read(fd,4096)
            except OSError:break
            if not d:break
            out.extend(d)
        if queue and now>=next_at:
            _,payload=queue.pop(0)
            try:os.write(fd,payload)
            except OSError:break
            next_at=now+(queue[0][0] if queue else 0)
        if now-start>timeout: break
    try:os.close(fd)
    except OSError:pass
    try:os.waitpid(pid,0)
    except OSError:pass
    return bytes(out)

def main():
    print("="*72); print("Experiment 008 — tmux control mode, driven live"); print("="*72)
    # make sure no stale server on our private socket
    subprocess.run([TMUX,"-L",SOCK,"kill-server"], stderr=subprocess.DEVNULL)
    try:
        # tmux -C new-session: attach a CONTROL client to a fresh session running
        # a shell. Then feed commands on stdin; read the % protocol on stdout.
        argv=[TMUX,"-L",SOCK,"-C","new-session","-x","80","-y","24","/bin/sh"]
        script=[
            (1.2, b"send-keys 'echo hello-from-agent' Enter\n"),   # input injection
            (1.0, b"capture-pane -p\n"),                            # read pane (framed)
            (0.8, b"new-window -n second\n"),                       # -> %window-add
            (0.6, b"list-windows -F '#{window_id} #{window_name}'\n"),
            (0.6, b"kill-server\n"),                                # clean shutdown
        ]
        raw=drive(argv, script, timeout=8.0)
    finally:
        subprocess.run([TMUX,"-L",SOCK,"kill-server"], stderr=subprocess.DEVNULL)

    (CAP/"tmux_control_mode.raw").write_bytes(raw)
    text=esc(raw)
    # transcript
    header=("Experiment 008 — tmux control mode (`tmux -C`) live protocol capture\n"
            "Regenerate with: python3 harness.py   (uses private socket, kills it after)\n"
            + "="*72 + "\n\n")
    (CAP/"RESULTS.txt").write_text(header+text+"\n")

    # quick analysis
    msgs=[l for l in text.splitlines() if l.startswith("%")]
    kinds={}
    for m in msgs:
        k=m.split(" ",1)[0]
        kinds[k]=kinds.get(k,0)+1
    print(text[:1500])
    print("..." if len(text)>1500 else "")
    print("-"*72)
    print("%-message types seen:", ", ".join(f"{k}×{v}" for k,v in sorted(kinds.items())))
    got_output = any("hello-from-agent" in l for l in msgs) or "hello-from-agent" in text
    print("send-keys injected + echoed back via %output:", got_output)
    print("wrote captures/RESULTS.txt")

if __name__=="__main__":
    main()
