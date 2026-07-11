# 006-shell-emitters

## Question
Experiments 001/002/005 traced how terminals **consume** OSC 133 / OSC 7. This
flips to the **emitter side**: the shell-integration scripts each terminal ships
so the shell *produces* those markers. **How do bash/zsh/fish inject the markers,
and what does that assume?** (Closes the open question logged in 002 and 005.)

tmux ships no emitter (consumer only, exp 002) — this round covers **Ghostty,
Kitty, WezTerm** across bash / zsh / fish (Ghostty also ships elvish).

## Setup / how to reproduce
Static source read — no build. Read-only against the shipped scripts:

**Ghostty** (`projects/ghostty/src/shell-integration/`)
- `bash/ghostty.bash`, `zsh/ghostty-integration`,
  `fish/vendor_conf.d/ghostty-shell-integration.fish`, `elvish/lib/…`

**Kitty** (`projects/kitty/shell-integration/`)
- `bash/kitty.bash`, `zsh/kitty-integration`,
  `fish/vendor_conf.d/kitty-shell-integration.fish`

**WezTerm** (`projects/wezterm/assets/shell-integration/wezterm.sh`) — one script
for bash + zsh; docs at `projects/wezterm/docs/shell-integration.md`.

Quick greps:
```sh
grep -rn "133;A\|133;B\|133;C\|133;D\|]7;" projects/*/…/shell-integration/
grep -rn 'interactive\|\$- != \*i\*' projects/*/…/shell-integration/   # the guards
```

## Steps
See `notes.md` for the per-shell traces and tables, `result.md` for the unified
answer + the interactivity-gap thesis.
