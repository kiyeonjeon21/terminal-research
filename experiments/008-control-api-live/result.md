# Result — 008-control-api-live

> Empirical. Live `tmux -C` capture; regenerate with `python3 harness.py`.
> Interpretation marked _(interpretation)_.

## Answer

**Yes — tmux control mode is a real, drivable agent surface, and it behaves
exactly as experiment 007 predicted from source.** We attached a control client
over a PTY, injected input with `send-keys`, and watched the terminal **push** the
results back:

- `send-keys 'echo hello-from-agent' Enter` → the shell's echo and output streamed
  back **unsolicited** as `%output %0 …` (even chunked across messages). We polled
  nothing.
- `capture-pane -p`, `list-windows` → replies **framed** by `%begin <t> <n>` …
  `%end <t> <n>`, correlatable by number.
- `new-window` → `%window-add @1`; session lifecycle pushed as `%sessions-changed`
  / `%session-changed` / `%window-renamed` / `%exit`.

And the gap from the rest of the repo is visible on the wire: **no
`command.end{exit_code}`** — the stream carries raw `%output`, so to know when a
command finished or how it exited, a consumer must parse the pane bytes itself.

## Not run here (honest scope)
- **kitty `@`** — installed, but a GUI app; driving it would pop a window on the
  user's screen. Source-verified in `../007-control-api/` instead.
- **wezterm `cli`** — not installed. Source-verified in `../007-control-api/`.

## Why it matters (interpretation)

_(interpretation)_ This is the empirical counterpart to exp 007's reading. The
"closest thing to an agent event bus that already ships" is not hypothetical — it
runs, headless, over a pipe, and an agent can drive it today: inject input, watch
a push stream, spawn/query with framed replies. What it lacks is the semantic
layer (`command.start/output/end{exit_code}`) that the whole repo argues for — you
get the transport and the raw bytes, and must reconstruct the structure yourself.
tmux control mode is the transport half of `../../ideas/terminal-protocol.md`
already in the wild.

## Evidence
- `captures/RESULTS.txt` — the raw `%`-protocol transcript.
- `harness.py` — the PTY control-client driver (private socket, self-cleaning).

## Open questions / next
- Turn on `pause-after` / flow control and observe `%pause`/`%continue`.
- Drive kitty `@` on a machine with a GUI session (or a headless kitty build) to
  capture the request/response side empirically.
