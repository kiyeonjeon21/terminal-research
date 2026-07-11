# Notes — 008-control-api-live

Live `tmux -C` protocol capture. Full transcript in `captures/RESULTS.txt`;
regenerate with `python3 harness.py`.

## Observed protocol (abridged from a real run)
```
%begin … 286 0            ← command framing (correlatable by the number)
%end … 286 0
%window-add @0            ← structural notifications on session create
%sessions-changed
%session-changed $0 0
%window-renamed @0 zsh
%output %0 sh-3.2$        ← PUSH: the pane's prompt bytes, unsolicited
--- we send: send-keys 'echo hello-from-agent' Enter ---
%output %0 ech
%output %0 o hel
%output %0 lo-from-agent\015\012   ← our injected command, echoed + run,
%output %0 hello-from-agent\015\012    streamed back as %output (chunked!)
%output %0 sh-3.2$
--- we send: capture-pane -p ---
%begin … 295 1
sh-3.2$ echo hello-from-agent
hello-from-agent
sh-3.2$ …                 ← pane content, framed between %begin/%end
%end … 295 1
--- we send: new-window -n second ---
%window-add @1            ← spawn -> structural push
--- we send: list-windows -F '#{window_id} #{window_name}' ---
%begin … 299 1
@0 bash
@1 second                 ← query result, framed
%end … 299 1
--- we send: kill-server ---
%exit
```

## Key observations (exp 007, confirmed live)
- **`%output` is a genuine push stream.** We never asked for the pane's bytes —
  `send-keys` injected `echo hello-from-agent`, and the shell's echo + output came
  back unsolicited as `%output %0 …`, even **chunked** across several messages
  (`ech` / `o hel` / `lo-from-agent`). This is the firehose exp 007 described.
- **Input injection works** via `send-keys` — the agent "typed" into the pane and
  saw the result on the same stream.
- **Command results are framed** by `%begin <t> <n>` … `%end <t> <n>`, the `<n>`
  correlating a reply to its submission (`capture-pane`, `list-windows`).
- **Structural events push** without polling: `%window-add`, `%sessions-changed`,
  `%session-changed`, `%window-renamed`, `%session-window-changed`, `%exit`.
- **No shell-command boundary / exit code** appears anywhere in the stream — to
  detect when `echo` finished or its status, a consumer must parse the pane bytes
  itself (exactly the exp 002/005/007 gap, now visible: the protocol carries raw
  `%output`, not `command.end{code}`).

## Facts vs. assumptions
- _(fact)_ Every line above is from a real capture (tmux 3.6a, macOS, private
  socket, server killed after — verified no leftover server).
- _(scope)_ kitty `@` and wezterm `cli` were not driven (GUI / not installed);
  their capabilities are source-verified in `../007-control-api/`.
- _(note)_ `%output` chunk boundaries are timing-dependent (PTY read sizes), so
  exact splits vary run to run; the message *types* and framing are stable.
