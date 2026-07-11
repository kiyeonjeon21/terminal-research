# Shell Integration

> Learning note. Facts cite source; assumptions are marked _(assumption)_.

## Question
How do terminals learn about prompts, commands, and exit codes?

## Key concepts
- prompt marking (OSC 133)
- cwd reporting (OSC 7)
- shell hooks (bash/zsh/fish)
- what data the terminal gains

## Findings

### OSC 133 semantic prompt actions
The shell emits these markers (spec:
`per-bothner/.../semantic-prompts.md`); the terminal maps each to state.
Naming below follows Ghostty's action enum
(`projects/ghostty/src/terminal/osc/parsers/semantic_prompt.zig:23-31`):

| Seq | Meaning | Marks the region that follows as |
| --- | ------- | -------------------------------- |
| `133;A` | fresh line + new prompt | prompt |
| `133;N` | new command (implicit end of prev) | prompt (same as A) |
| `133;P` | explicit prompt start (`k=` kind) | prompt |
| `133;B` | end prompt, start input | input |
| `133;I` | end prompt, start input (until EOL) | input |
| `133;C` | end input, start output | output |
| `133;D` | end command (`exit_code` optional) | — (output ends) |

Kitty extensions ride on `A`/`P`: `redraw`, `special_key`, `click_events`,
`k=` prompt kind. The `aid` (command id) option is parsed by every terminal
studied and **used by none**.

### What the terminal actually gains (verified)
Across Ghostty / WezTerm / Kitty / tmux, OSC 133 buys the terminal a **≤2-bit
semantic tag per grid cell/line** — enough for prompt navigation and
"select command output", all reconstructed on demand. It does **not** buy a
durable command record: exit codes are dropped or kept as a transient scalar,
never joined to output. Full trace + citations:
`../experiments/001-command-boundary/`, `../experiments/002-command-model/`,
synthesis in `../comparisons/agent-opportunities.md`.

### OSC 7 (cwd reporting)
Traced in `../experiments/005-cwd-tracking/`. All four terminals parse OSC 7 but
diverge on trusting it vs. reading the OS process cwd — spectrum
**Ghostty (shell-only) → WezTerm → Kitty → tmux (process-only)**. iTerm2 OSC 1337
`CurrentDir` is an alternate carrier (Ghostty honors it; WezTerm ignores it).

## Open questions
- Shell hook mechanics: how bash/zsh/fish inject the OSC 133 markers
  (PROMPT_COMMAND, preexec, fish events) — and fish's missing-PS2 quirk that
  Ghostty special-cases (`Terminal.zig:1829-1843`).

## Sources
- `projects/ghostty/src/terminal/osc/parsers/semantic_prompt.zig`
- semantic-prompts spec (linked at top of that file)
- Experiments 001 & 002 in this repo
