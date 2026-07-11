# Terminal Research

A personal research repository for studying modern terminal emulators and exploring what terminals could look like in the age of coding agents.

## Goals

- Understand how modern terminals are built.
- Compare architectural decisions across projects.
- Learn by reading source code and running experiments.
- Explore ideas for agent-native developer tooling.

## Findings

**→ [SYNTHESIS.md](SYNTHESIS.md) — the full synthesis** (Part I: the agent
thesis + four findings; Part II: how terminals work — parser, rendering, PTY,
multiplexing, input, graphics; plus a portrait of each terminal).

Nine experiments across two axes converge on one thesis: *terminals compute
command structure but never keep it, and get it only from an interactive human's
prompt cycle — so for a coding agent it does not exist.* The four findings
(detailed in [comparisons/agent-opportunities.md](comparisons/agent-opportunities.md)):

1. No terminal keeps a durable command record — just a ≤2-bit grid tag. _(exp [001](experiments/001-command-boundary/), [002](experiments/002-command-model/))_
2. "cwd" is lossy — shell-escape vs OS-process, four different policies. _(exp [005](experiments/005-cwd-tracking/))_
3. Markers require an interactive prompt — agent commands emit nothing (proven on the wire). _(exp [006](experiments/006-shell-emitters/), [003](experiments/003-osc133/))_
4. A control API exists (Kitty RPC / tmux push / WezTerm cli+Lua) but none exposes a command's exit code. _(exp [007](experiments/007-control-api/))_

## Comparison studies (breadth)

Cross-terminal technical comparisons, beyond the agent axis — general terminal
understanding:

- [parser](comparisons/parser.md) · [rendering](comparisons/rendering.md) · [architecture](comparisons/architecture.md)
- [multiplexing](comparisons/multiplexing.md) · [input/keyboard](comparisons/input.md) · [graphics](comparisons/graphics.md)
- [shell-integration](comparisons/shell-integration.md) · [extensibility](comparisons/extensibility.md) · [agent-opportunities](comparisons/agent-opportunities.md)

Background reference in [notes/](notes/) (pty, ansi, vt100, osc, rendering,
shell-integration, input, multiplexing, graphics).

## Experiments

Small, reproducible probes ([full index](experiments/)):

| # | Question |
| - | -------- |
| [001](experiments/001-command-boundary/) | Command boundaries in Ghostty |
| [002](experiments/002-command-model/) | Command model across WezTerm/Kitty/tmux |
| [003](experiments/003-osc133/) | OSC 133 hands-on — markers are interactive-only *(PTY capture)* |
| [004](experiments/004-pty-tracing/) | Tracing PTY traffic — echo/escapes/resize *(PTY capture)* |
| [005](experiments/005-cwd-tracking/) | cwd tracking — OSC 7 vs process inspection |
| [006](experiments/006-shell-emitters/) | Shell-integration emitters (the interactivity gap) |
| [007](experiments/007-control-api/) | Control-API surface across the four *(source)* |
| [008](experiments/008-control-api-live/) | Driving a control API live — tmux control mode *(live capture)* |
| [009](experiments/009-raw-mode-tui/) | Raw-mode TUI capture — vim/less *(live capture)* |

Empirical probes (003, 004, 008, 009) ship a `harness.py` — run `python3 harness.py`.

## Projects

Local clones under `projects/` (gitignored, kept unmodified):

- Ghostty · WezTerm · Kitty · tmux

## Research Areas

- PTY
- ANSI / VT escape sequences
- Shell integration
- Rendering
- Command boundaries
- Terminal state
- Developer experience

## Method

For each project:

1. Read the source code.
2. Trace important execution paths.
3. Compare design decisions.
4. Validate findings with small experiments.
5. Record insights and open questions.

The goal is not to build another terminal emulator, but to understand the design space well enough to discover new ideas for coding-agent-first developer environments.