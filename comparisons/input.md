# Input / Keyboard / Mouse — Comparison

> Breadth/learning study. How key/mouse/paste/focus events become bytes sent to
> the child. Cite `file:line`. Background in `../notes/input.md`.

## Question
How does each encode keyboard, mouse, paste, and focus — and which support the
modern Kitty keyboard protocol?

Note the roles: Ghostty/WezTerm/Kitty are emulators (encode GUI events → bytes).
**tmux is a multiplexer** — it *decodes* bytes from the outer terminal
(`tty-keys.c`) and *re-encodes* per child pane (`input-keys.c`), tracking each
pane's requested modes.

| Terminal | Kitty kbd protocol | modifyOtherKeys | mouse SGR (?1006) | bracketed paste (?2004) | focus (?1004) |
| -------- | ------------------ | --------------- | ----------------- | ----------------------- | ------------- |
| **Ghostty** | **full** — encode `key_encode.zig:100`; flags `terminal/kitty/key.zig:79`; push/pop/set/query `stream_terminal.zig:254-258,553` | yes (`Terminal.zig:98`, used `key_encode.zig:413`) | yes (`modes.zig:284`, `mouse_encode.zig`) | yes (`paste.zig:96`) | yes (`stream_terminal.zig:615`) |
| **WezTerm** | **full** — `KeyboardEncoding::Kitty` (`termwiz/src/input.rs:28`); parse `csi.rs:161,1875-1908` | yes (`input.rs:293`; `XtermKeyMode` `csi.rs:805`) | yes (`SGRMouse=1006` `csi.rs:931`; no urxvt) | yes (`csi.rs:945`) | yes (`csi.rs:926`) |
| **Kitty** | **reference impl** — encode `key_encoding.c:66`; router `vt-parser.c:1312-1333`; stack `screen.c:1787-1831` | **parsed but rejected** — logs "use the kitty protocol" (`screen.c:1782`) | yes (`MOUSE_SGR_MODE` `modes.h:67`, `mouse.c:103`) | yes (`modes.h:81`) | yes (`CSI I/O` `screen.c:5962`) |
| **tmux** | **no** — `extended-keys` emits CSI u *or* xterm form, but no push/pop/report stack (`input-keys.c:426,467`; `options-table.c:395`) | yes (`input_key_mode1` `input-keys.c:545`) | yes — decode `tty-keys.c:1187`, re-encode `input-keys.c:757` | yes (`MODE_BRACKETPASTE` `input.c:1682`) | yes (`MODE_FOCUSON` `input.c:1673`) |

## Notes
- **Legacy encoding is ambiguous** (`../notes/input.md`): `Ctrl-I`==`Tab`(0x09),
  `Ctrl-M`==`Enter`(0x0D), `Ctrl-[`==`Esc`(0x1B); most keys can't carry
  modifiers; Alt is an ESC-prefix (collides with real Esc); arrows differ by
  DECCKM app-cursor mode (`CSI` vs `SS3`). tmux's code literally comments on
  losing modifiers on Unicode keys (`input-keys.c:498`).
- **Kitty keyboard protocol** (Kitty invented it, kovidgoyal) fixes this: every
  key as `CSI unicode ; mods [; text] u`, opt-in via a **progressive-enhancement
  flag stack** (5 bits: disambiguate / report_events / report_alternates /
  report_all / report_associated). Handshake: `CSI > flags u` push, `CSI < u`
  pop, `CSI = flags ; mode u` set, `CSI ? u` query → `CSI ? flags u`. Ghostty and
  WezTerm implement it fully; **tmux only does the `extended-keys` CSI-u/xterm
  encoding, not the stack**.
- **modifyOtherKeys** (xterm's earlier partial fix, `CSI > 4 ; n m` → `CSI 27 ;
  mods ; key ~`): supported by Ghostty/WezTerm/tmux; **Kitty deliberately rejects
  it** in favor of its own protocol.
- **Mouse:** `?1000/1002/1003` select *what* (press / drag / any-motion);
  `?1006` SGR is the modern *encoding* (`CSI < b;x;y M/m`, decimal coords, explicit
  press/release) — all four support it. tmux notes why release needs SGR: legacy
  release doesn't say which button (`input-keys.c:744`).
- **Bracketed paste** `?2004` — a **security** feature: wraps paste in
  `\e[200~…\e[201~` so apps distinguish typed vs pasted and won't auto-run pasted
  newlines. Ghostty scans pasted data for a stray `201~` as unsafe (`paste.zig:133`).

## Sources
Per-terminal input files above; `../notes/input.md`.
