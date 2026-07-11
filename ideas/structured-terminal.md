# Structured Terminal API

> Raw idea. No need to be right — capture it before it evaporates.

## The idea
A terminal that exposes commands, outputs, and state as structured events instead of a byte stream.

## Why it might matter for coding agents
An agent driving a terminal today has to *screen-scrape*: it gets a byte stream
and must guess where a command started, ended, and what its exit code was. If
the terminal already knows the boundaries (it does — see below), exposing them
as events (`command.start`, `command.output`, `command.end{exit_code}`) would
let an agent read command results reliably instead of parsing scrollback.

## Prior art / closest existing thing
**OSC 133 semantic prompts** are the closest existing mechanism. Verified in
Ghostty (`../experiments/001-command-boundary/`), the terminal actually gets
*most of the way there* and then throws the structure away:
- it tags every cell/row prompt/input/output (a queryable grid), **and**
- it does emit a `command_finished{exit_code, duration}` event on `133;D`.

But it keeps **no durable command record** — the event fires a notification and
is dropped, and the grid tags are never joined to it. So "command → output →
exit code" exists momentarily across two subsystems and is never assembled. The
gap is a small one: an event bus + query API that *retains and joins* what the
terminal already computes. See `terminal-protocol.md`.

**This is not Ghostty-specific.** `../experiments/002-command-model/` verified
the same design in WezTerm, Kitty, and tmux — four independent codebases, all
storing only a ≤2-bit grid tag and reconstructing (or discarding) the rest.
WezTerm discards the exit code outright (`performer.rs:900-902`); Kitty keeps it
as an overwritten scalar; tmux never parses it. Most tellingly, **tmux built a
durable OSC-133 records feature and reverted it** (`6fd9987`) — so the gap is a
deliberately-un-landed capability, not an accident. A from-scratch agent-native
terminal can own that structure by design instead of retrofitting it.

## Open questions
- What is the right retention window / eviction policy for a command store
  (unbounded history vs. ring buffer vs. tied to scrollback)?
- Does the join belong in the terminal core or in a sidecar that consumes the
  existing OSC 133 markers + PTY exit status?
- What killed tmux's version — config surface, or something structural? (Would
  inform whether the retrofit-vs-greenfield distinction actually matters.)
