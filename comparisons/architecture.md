# Architecture — Comparison

> Fill the table as findings are verified. Cite `file:line` per project.

## Question
How is each terminal structured, and what does it choose to be?

| Project | Language | Rendering | Multiplexer | Reusable library |
| ------- | -------- | --------- | ----------- | ---------------- |
| Ghostty | Zig      | GPU       | No          | libghostty       |
| WezTerm | Rust     | GPU       | Yes         | No               |
| tmux    | C        | N/A       | Yes         | No               |
| Kitty   | C/Python | GPU       | No          | No               |
| VS Code | TS       | GPU (xterm.js) | No     | xterm.js         |

## Notes
_TBD_
