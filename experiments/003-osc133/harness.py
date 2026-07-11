#!/usr/bin/env python3
"""Experiment 003 — OSC 133 hands-on.

Empirically confirm the experiment-006 thesis: shell-integration markers
(OSC 133 A/B/C/D, OSC 7) are emitted ONLY by an interactive shell driven through
a prompt cycle. Non-interactive / agent-style command execution emits nothing.

Method: allocate a real PTY (pty.fork), spawn a shell, feed it commands, capture
every byte the shell writes to the PTY master, and extract the OSC sequences.

Read-only w.r.t. the cloned projects: we only READ the shipped scripts under
../../projects/, never modify them. All scratch files go under captures/.
"""
import os, pty, select, time, re, sys, pathlib

HERE = pathlib.Path(__file__).resolve().parent
CAP = HERE / "captures"
CAP.mkdir(exist_ok=True)
PROJECTS = HERE.parent.parent / "projects"

BASH = "/opt/homebrew/bin/bash"   # bash 5.3 (PS0 support)
ZSH = "/bin/zsh"

# A faithful *minimal* integration mirroring the mechanism documented in exp 006.
# NOT a real terminal's script — just the essential hooks, with the same
# interactive guard the real scripts use.
MINI_BASH = r"""
[[ "$-" != *i* ]] && return                       # interactive guard (as real scripts do)
_mini_precmd() {
  local ret="$?"                                  # capture exit code first
  printf '\e]133;D;%s\a' "$ret"                   # D: end of previous command
  printf '\e]7;file://%s%s\a' "$HOSTNAME" "$PWD"  # OSC 7: cwd report
  printf '\e]133;A\a'                             # A: prompt start
}
PROMPT_COMMAND=_mini_precmd
PS0='\e]133;C\a'                                  # C: output start (bash>=4.4)
PS1='$ \e]133;B\a'                                # B: end of prompt / start of input
"""

MINI_ZSH = r"""
[[ -o interactive ]] || return
autoload -Uz add-zsh-hook
_mini_precmd() {
  local ret=$?
  print -n $'\e]133;D;'"$ret"$'\a'
  print -n $'\e]7;file://'"$HOST$PWD"$'\a'
  print -n $'\e]133;A\a'
}
_mini_preexec() { print -n $'\e]133;C\a'; }
add-zsh-hook precmd _mini_precmd
add-zsh-hook preexec _mini_preexec
PS1=$'$ %{\e]133;B\a%}'
"""

OSC_RE = re.compile(rb'\x1b\](133;[^\x07\x1b]*|7;[^\x07\x1b]*)(?:\x07|\x1b\\)')

def run(argv, feed, env=None, timeout=6.0):
    """Spawn argv in a PTY, write `feed`, capture master bytes until child exits."""
    pid, fd = pty.fork()
    if pid == 0:  # child
        if env:
            os.environ.update(env)
        try:
            os.execvp(argv[0], argv)
        finally:
            os._exit(127)
    out = bytearray()
    to_write = feed.encode() if isinstance(feed, str) else feed
    start = time.time()
    while True:
        r, w, _ = select.select([fd], [fd] if to_write else [], [], 0.2)
        if fd in r:
            try:
                data = os.read(fd, 4096)
            except OSError:
                break
            if not data:
                break
            out.extend(data)
        if to_write and fd in w:
            n = os.write(fd, to_write[:128])
            to_write = to_write[n:]
        if time.time() - start > timeout:
            break
    try: os.close(fd)
    except OSError: pass
    try: os.waitpid(pid, 0)
    except OSError: pass
    return bytes(out)

def markers(raw):
    """Return the list of OSC 133/7 payloads found in the captured bytes."""
    return [m.group(1).decode('latin1') for m in OSC_RE.finditer(raw)]

def summarize(name, raw):
    ms = markers(raw)
    kinds = {}
    for m in ms:
        if m.startswith('133;'):
            kinds.setdefault(m.split(';')[1][:1] or '?', 0)
            kinds[m.split(';')[1][:1] or '?'] += 1
        elif m.startswith('7;'):
            kinds['OSC7'] = kinds.get('OSC7', 0) + 1
    (CAP / f"{name}.bin").write_bytes(raw)
    tag = ' '.join(f"{k}:{v}" for k, v in sorted(kinds.items())) or "(none)"
    print(f"[{name}] {len(raw):5d} bytes captured | OSC markers: {tag}")
    for m in ms[:12]:
        print(f"     └─ ESC]{m}")
    return kinds

def rcfile(body, tmpname):
    p = CAP / tmpname
    p.write_text(body)
    return str(p)

def main():
    print("=" * 70)
    print("Experiment 003 — OSC 133 hands-on (PTY capture)")
    print("=" * 70)

    # --- A: interactive bash + minimal integration → expect A/B/C/D + OSC7 ---
    #     NOTE: --norc would make bash IGNORE --rcfile, so we omit it here.
    rc = rcfile(MINI_BASH, "mini.bash")
    rawA = run([BASH, "--noprofile", "--rcfile", rc, "-i"],
               "echo hello\nexit\n")
    kA = summarize("A_bash_interactive_mini", rawA)

    # --- B: NON-interactive bash sourcing the same integration → expect none ---
    rawB = run([BASH, "--norc", "--noprofile", "-c",
                f"source {rc}; echo hello"], "")
    kB = summarize("B_bash_noninteractive_mini", rawB)

    # --- C: real shipped scripts, sourced non-interactively → guard must trip ---
    #     We check that the integration's hook function is NOT defined afterwards.
    real = {
        "kitty": PROJECTS / "kitty/shell-integration/bash/kitty.bash",
        "ghostty": PROJECTS / "ghostty/src/shell-integration/bash/ghostty.bash",
    }
    print("-" * 70)
    for term, path in real.items():
        if not path.exists():
            print(f"[C_{term}] MISSING {path}"); continue
        probe = (f'export KITTY_SHELL_INTEGRATION=enabled GHOSTTY_SHELL_FEATURES=1; '
                 f'source "{path}" 2>/dev/null; '
                 f'echo "HOOKS=[${{PROMPT_COMMAND:-}}]"; '
                 f'declare -F _ksi_prompt_command _ghostty_hook __ghostty_precmd 2>/dev/null '
                 f'|| echo "NO_HOOKS_INSTALLED"')
        rawC = run([BASH, "--norc", "--noprofile", "-c", probe], "", timeout=4.0)
        (CAP / f"C_{term}_noninteractive.txt").write_bytes(rawC)
        text = rawC.decode('latin1')
        installed = "NO_HOOKS_INSTALLED" not in text
        print(f"[C_{term}] non-interactive source → hooks installed: {installed}")
        for line in text.splitlines():
            if 'HOOKS=' in line or 'NO_HOOKS' in line or '_precmd' in line or '_ksi' in line:
                print(f"     └─ {line.strip()}")

    # --- C2: the SAME real kitty.bash, but INTERACTIVE → real markers appear ---
    krc = rcfile('export KITTY_SHELL_INTEGRATION=enabled\n'
                 f'source "{real["kitty"]}"\n', "real_kitty.bash")
    rawC2 = run([BASH, "--noprofile", "--rcfile", krc, "-i"], "echo hello\nexit\n")
    kC2 = summarize("C2_real_kitty_interactive", rawC2)

    # --- D: interactive zsh + minimal integration → cross-shell confirm ---
    print("-" * 70)
    rcz = rcfile(MINI_ZSH, "mini.zsh")
    # zsh: ZDOTDIR trick to load our rc as .zshrc
    zdir = CAP / "zdot"; zdir.mkdir(exist_ok=True)
    (zdir / ".zshrc").write_text(MINI_ZSH)
    rawD = run([ZSH, "-i"], "echo hello\nexit\n",
               env={"ZDOTDIR": str(zdir)})
    kD = summarize("D_zsh_interactive_mini", rawD)

    # --- verdict ---
    print("=" * 70)
    ok_A = all(k in kA for k in ("A", "C", "D")) and "OSC7" in kA
    ok_B = not kB
    print(f"A interactive bash emits A/C/D + OSC7 : {ok_A}  ({kA})")
    print(f"B non-interactive bash emits nothing  : {ok_B}  ({kB or '{}'})")
    print(f"D interactive zsh emits markers       : {bool(kD)}  ({kD})")
    print("THESIS (markers require interactive prompt) CONFIRMED:",
          ok_A and ok_B)

if __name__ == "__main__":
    main()
