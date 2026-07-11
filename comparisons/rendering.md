# Rendering — Comparison

> Breadth/learning study. How the cell grid becomes pixels. Cite `file:line`.
> Background facts in `../notes/rendering.md`.

## Question
Cell grid, glyph atlas, GPU pipeline, damage tracking — how does each do it?

Three are GPU rasterizers (Ghostty, WezTerm, Kitty); **tmux is the contrast** —
it never touches a GPU, it re-emits terminfo escape sequences to an *outer*
terminal and lets that do the rasterizing.

| Terminal | CPU/GPU + API | Glyph cache (`file:line`) | Shaping | Damage tracking | Cell size |
| -------- | ------------- | ------------------------- | ------- | --------------- | --------- |
| **Ghostty** | GPU — Metal / OpenGL / WebGL, backend-abstracted (`renderer/generic.zig`); **instanced** quads | rect-pack atlas `font/Atlas.zig` + `font/SharedGrid.zig:44` (GlyphKey→Render) | HarfBuzz **or** CoreText, compile-time (`font/shape.zig:20`) | 3-state `false/partial/full` (`terminal/render.zig:266`) + per-row `dirty` + per-cell `Dirty` | terminal cell **8 B** (`page.zig:2037`); GPU cell **32 B** (`metal/shaders.zig:265`) |
| **WezTerm** | GPU — WebGPU (wgpu) **or** OpenGL (glium), runtime; single `draw_indexed` (4 verts/cell, not instanced) | `glyphcache.rs:561` (HashMap + `Atlas`) | HarfBuzz (`shaper/harfbuzz.rs`) | **line seqno** compare (`termwindow/render/mod.rs:872`) | `Cell` = `TeenyString(u64)` + attrs (`wezterm-cell/src/lib.rs:715`) |
| **Kitty** | GPU — OpenGL, **instanced** `glDrawArraysInstanced` (`gl.c:136`) | sprite map `glyph-cache.c:9` (SpritePosKey→SpritePosition) | HarfBuzz in C (`fonts.c:1347`) | per-line `has_dirty_text` bit (`line.h:86`) | CPUCell **12 B** + GPUCell **20 B** (`line.h:42,82`) |
| **tmux** | **No GPU** — writes terminfo escapes to the outer tty (`tty.c`, `tty-draw.c`) | none | none (forwards UTF-8) | per-cell `cell_type` diff (`screen-redraw.c:857`) + `GRID_LINE_*` flags | logical `grid_cell` + packed `grid_cell_entry` **~5 B** (`tmux.h:863`) |

## Notes
- **Draw call shape:** Ghostty and Kitty upload a packed per-cell array and issue
  **one instanced draw** (one unit quad × N cells). WezTerm builds a big vertex
  buffer (4 verts/cell) and issues **one `draw_indexed`** — same "one draw per
  frame" goal, different mechanism.
- **Glyph atlas = rasterize once, reuse forever.** All three GPU terminals cache
  rasterized glyphs keyed by (font, glyph id, size/opts) in a hash map + pack them
  into one GPU texture; a cell just stores atlas coords / `sprite_idx`. Growth vs
  eviction differs: Ghostty grows and never evicts; WezTerm rebuilds the whole
  cache on overflow; Kitty reallocs its sprite texture.
- **Damage tracking = do less.** For a blinking cursor on an idle screen each
  re-touches ~one line: Kitty `has_dirty_text` bit, WezTerm line `seqno`, Ghostty
  `false/partial/full` + per-row dirt. tmux's "damage" instead minimizes **bytes
  written to the pipe**, not GPU draws.
- **Packed cells save bandwidth.** Bit-packed to fit cache lines / minimize
  CPU→GPU upload; styles deduplicated by id (Ghostty `style_id`) or offset (tmux)
  rather than stored inline.
- **tmux is the counter-example** worth keeping in mind: it maintains an in-memory
  grid but its "render target" is a real terminal on the other end of an fd. It
  diffs grids and emits minimal terminfo sequences (`tty_draw_line`
  `tty-draw.c:118`), tracking the outer cursor to avoid redundant moves. Portable
  and network-transparent; bounded by the outer terminal.

## Sources
Per-terminal renderer files cited above; `../notes/rendering.md`.
