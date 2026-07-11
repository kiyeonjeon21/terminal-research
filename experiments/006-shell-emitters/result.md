# Result — 006-shell-emitters

> Emitter side of OSC 133 / OSC 7: the shell-integration scripts Ghostty, Kitty,
> and WezTerm ship. Facts cite `file:line` (under `../../projects/`);
> interpretation marked _(interpretation)_.

## Answer

The shipped scripts hook the shell's prompt lifecycle and `printf` the escape
sequences at fixed points:

- **prompt drawn** (bash `PROMPT_COMMAND`, zsh `precmd`, fish `fish_prompt`) →
  emit **D** (previous command's `;$?`) then **A** (new prompt start); **B** rides
  inside `PS1`.
- **command about to run** (bash `PS0`, zsh/fish `preexec`) → emit **C** (output
  start), often with the command text (`cmdline=`).
- **cwd** → emit **OSC 7** at precmd / on `cd`.

The three converge on the same de-facto protocol (FinalTerm OSC 133 + OSC 7) —
they even share kitty's `kitty-shell-cwd://` scheme and the same bundled
`bash-preexec.sh`. The interesting differences are small (see tables in
`notes.md`): Kitty combines `D;$?` + `A` in one PS1 string and ships no bash
preexec; WezTerm bundles bash-preexec always and adds an OSC 1337
`SetUserVar=WEZTERM_PROG` channel; only Ghostty's fish percent-encodes the OSC 7
path while every bash/zsh emits it raw.

## The thesis — the machinery is fed only by an interactive human prompt

Every script begins with an interactive-shell guard (`ghostty.bash:19`,
`kitty.bash:3`, `wezterm.sh:27`, and the zsh/fish equivalents), and **every**
marker is bound to a precmd/preexec/postexec hook — i.e. to the existence of a
prompt cycle.

**Consequence (verified structurally):** a command run non-interactively —
`bash -c "…"`, `zsh -c`, `fish -c`, or an agent that spawns a shell without an
interactive prompt — produces **zero** OSC 133 / OSC 7 markers. There is no
prompt, so nothing fires.

## Why this is the sharpest finding of the arc

_(interpretation)_ Experiments 001/002 showed the terminal doesn't *retain* a
command record; 005 showed cwd is a lossy single value. This experiment shows the
more fundamental thing: for **agent-run commands, the structured signals are
never even produced.**

- The whole command-boundary + cwd apparatus (exp 001/002/005) is downstream of
  an interactive human typing at a prompt. Take away the prompt and the terminal
  sees an undifferentiated byte stream — exactly what a coding agent gets today.
- So an agent can't rely on OSC 133 at all unless it deliberately drives an
  interactive shell *and* that shell has integration installed. The "structure"
  is a property of interactive human use, not of the shell or the terminal.

This reframes the opportunity (recorded as Finding #3 in
`../../comparisons/agent-opportunities.md`): the gap isn't only *retention*
(Findings #1/#2), it's *production*. An agent-native design would either (a) emit
command structure for non-interactive/programmatic execution, or (b) let the
agent drive terminal state directly rather than depending on shell prompt hooks —
see `../../ideas/structured-terminal.md` and `../../ideas/terminal-protocol.md`.

## Open questions / next
- What exactly does `bash-preexec.sh`'s DEBUG-trap emulation do (edge cases:
  subshells, `PROMPT_COMMAND` sharing)? Not re-read line-by-line here.
- Empirical check (exp 003): actually run each shell + emit sequences and observe
  the byte stream — confirm the "no markers when non-interactive" claim live.
- Do any of these ship a way to mark a *programmatic* command boundary (a manual
  `print '\e]133;C'`), and is that documented for scripting/agent use?
