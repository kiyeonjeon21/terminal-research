# Notes — 006-shell-emitters

Traces of the shipped scripts. Interactive guards and OSC 7 schemes spot-checked
firsthand. Paths relative to each clone under `../../projects/`.

## Hook mechanism (how code runs at prompt- and command-time)

| Shell | precmd (prompt) | preexec (before command) | Notes |
| ----- | --------------- | ------------------------ | ----- |
| bash  | `PROMPT_COMMAND` | `PS0` (bash ≥ 4.4) | else bundled `bash-preexec.sh` (DEBUG trap) |
| zsh   | `precmd_functions` | `preexec_functions` | deferred init so it runs after prompt frameworks |
| fish  | `fish_prompt` event | `fish_preexec` event | `fish_postexec` fires D |

- **bash-preexec divergence:** Ghostty bundles it only for bash < 4.4
  (`ghostty/src/shell-integration/bash/ghostty.bash:218,266`); **WezTerm bundles
  it verbatim** and always uses it (`wezterm/assets/shell-integration/wezterm.sh:41-424`);
  **Kitty ships none** — PS0-based (`kitty/shell-integration/bash/kitty.bash:230`).
- zsh init is deferred and re-forced to the end of `precmd_functions` each cycle
  so plugin prompt rewrites don't drop the marks
  (`ghostty/.../zsh/ghostty-integration:376-384`,
  `kitty/shell-integration/zsh/kitty-integration:359-367`).

## OSC 133 markers — literal sequences

- **A** (prompt start), **C** (`preexec`, output start), **D** (`;$?`, end):
  - Ghostty bash: A `\e]133;A;redraw=last;cl=line;aid=$BASHPID` (`ghostty.bash:188`) +
    `133;P`/`133;B` in PS1 (`:145`); C `\e]133;C;` (`:214`);
    D `\e]133;D;$ret;aid=$BASHPID` (`:177`).
  - Kitty bash: **D and A combined in PS1** `\e]133;D;$?\a\e]133;A\a` (`kitty.bash:258`);
    C via PS0 → `\e]133;C;cmdline=%q` (`:227`).
  - WezTerm: P;k=i + B in PS1 (`wezterm.sh:472`); A `\e]133;A;cl=m;aid=$$` (`:491`);
    C `\e]133;C;` (`:504`); D `\e]133;D;$ret;aid=$$` (`:482`).
- **B divergence:** emitted (in PS1) by Ghostty bash/zsh (`ghostty.bash:145`) and
  WezTerm (`wezterm.sh:472`); **NOT** by Ghostty fish (no B) or **Kitty zsh**
  (explicitly disabled, ZLE hooking too fragile —
  `kitty/shell-integration/zsh/kitty-integration:231-235`).
- **Command text on C:** Kitty `cmdline=%q` (`kitty.bash:227`), fish
  `cmdline_url=` URL-escaped (`kitty-…fish:106`). The terminal thus *receives*
  the command line — but only interactively.
- **WezTerm extra:** OSC 1337 `SetUserVar=WEZTERM_PROG=<cmd>` in preexec
  (`wezterm.sh:539`) — a side channel naming the running program.

## Exit-code capture
Captured *before anything else* to avoid clobbering `$?`:
- bash/zsh: `local ret="$?"` / `local -i cmd_status=$?` as the first line of
  precmd (`ghostty.bash:137`, `ghostty-integration:98`, `wezterm.sh:465`), or
  embedded literally in PS1 so it expands at render time (`kitty.bash:258`).
- fish: `$status` read in the `fish_postexec` handler (`ghostty-…fish:155`).
- zsh implementations run a small state machine (0/1/2) so D is only emitted when
  a C is open, and suppress D when precmd is invoked from ZLE (cd-triggered
  refresh) — `ghostty-integration:98-120`, `kitty-integration:136-158`.

## OSC 7 cwd — scheme divergence (spot-checked firsthand)

| Scheme | Encoding | Who |
| ------ | -------- | --- |
| `kitty-shell-cwd://` | raw (none) | Ghostty bash/zsh/elvish (`ghostty.bash:196`); all Kitty (`kitty.bash:207`, `kitty-integration:240`, `kitty-…fish:135`) |
| `file://` | raw | WezTerm (`wezterm.sh:457`), or delegates to `wezterm set-working-directory` CLI |
| `file://` | percent-encoded (`string escape --style=url`) | **only** Ghostty fish (`ghostty-…fish:164`) |

- Note the de-facto standardization: Ghostty adopts kitty's `kitty-shell-cwd://`
  for bash/zsh (its parser accepts it — see exp 005). Because bash/zsh emit the
  path **raw**, cwds with spaces/specials rely on lenient parsing (ties to 005).
- bash emits OSC 7 only at precmd (no cwd-change hook), so `cd x && cat` doesn't
  report the new cwd until the next prompt (`ghostty.bash:191-193`); zsh also
  wires `chpwd_functions` to catch `cd` (`ghostty-integration:236`).

## The thesis — everything is gated on an interactive human prompt
Every script hard-guards on an interactive shell, and *every* marker is bound to
precmd/preexec/postexec:

| Terminal | bash | zsh | fish |
| -------- | ---- | --- | ---- |
| Ghostty | `ghostty.bash:19` `[[ "$-" != *i* ]]` | `ghostty-integration:43` `[[ -o interactive ]]` | `ghostty-…fish:44` `status --is-interactive` |
| Kitty | `kitty.bash:3` | `kitty-integration:26` | `kitty-…fish:20` |
| WezTerm | `wezterm.sh:27` `[[ $- != *i* ]]; return 0` | (same file) | not handled |

→ A non-interactive command (`bash -c`, an agent spawning a shell with no prompt)
fires **zero** OSC 133 / OSC 7 markers.

## Facts vs. assumptions
- _(fact)_ All escape literals, guards, hooks, and OSC 7 schemes above are quoted
  from source; guards + schemes re-verified firsthand.
- _(assumption)_ The "non-interactive → no markers" conclusion is inferred from
  the interactive guard + prompt-bound emission; no script states it explicitly
  (but it is a direct structural consequence, consistent across all three).
- _(assumption)_ bash-preexec's exact DEBUG-trap mechanics were not re-read
  line-by-line; role inferred from the registration sites + the known upstream.
