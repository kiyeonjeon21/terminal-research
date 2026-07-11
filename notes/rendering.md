# Terminal Rendering

> Learning note. Facts cite source; assumptions are marked _(assumption)_.

## Question
How is the terminal grid drawn to the screen?

## Key concepts
- cell grid model
- CPU vs GPU rendering
- glyph atlas / sprite sheet; text shaping
- damage / dirty tracking & redraw

## Findings

### The pipeline (GPU terminals)
`bytes → parser → cell grid → shaping → glyph rasterization (cached) → GPU draw`.
Detail per terminal in `../comparisons/rendering.md`.

### Glyph atlas / sprite sheet
One big GPU texture holding many rasterized glyphs packed as sub-rectangles.
Instead of a texture per character, a cell stores atlas coordinates (Ghostty
`CellText.glyph_pos`, Kitty `GPUCell.sprite_idx`), and the GPU draws the whole
screen sampling one bound texture. **Rasterize once, reuse forever** — a glyph is
rasterized (FreeType/CoreText) on first appearance and cached keyed by (font,
glyph id, size/opts): Ghostty `SharedGrid.zig:44`, WezTerm `glyphcache.rs:561`,
Kitty `glyph-cache.c:9`. Growth vs eviction differs: Ghostty grows/never evicts;
WezTerm rebuilds the whole cache on overflow; Kitty reallocs the sprite texture.

### Shaping ≠ rendering
**Shaping** (HarfBuzz / CoreText) turns a run of Unicode codepoints into
positioned glyph ids — handling ligatures and combining marks — on the CPU,
before rasterization. All three GPU terminals shape with HarfBuzz (Ghostty and
WezTerm can also use CoreText).

### CPU vs GPU
_(interpretation)_ GPU terminals offload compositing/blending to the GPU →
ligatures, gamma-correct blending, inline images, high-refresh redraw at low CPU
cost, at the price of an atlas/shader/driver stack. tmux's CPU-only
escape-sequence model is portable and network-transparent (works over SSH into a
dumb tty) but bounded by the outer terminal's capabilities and pipe throughput.

### Draw-call shape
- **Instanced quads** (Ghostty, Kitty): one unit quad, per-cell data uploaded
  once, a single instanced draw for the whole grid (`glDrawArraysInstanced`,
  Kitty `gl.c:136`).
- **Indexed vertex buffer** (WezTerm): 4 verts/cell in one buffer, one
  `draw_indexed` (`render/draw.rs:138`). Same "one draw per frame" goal.

### Damage / dirty tracking
Cache per-line/frame state; re-shape/re-upload only what changed — a blinking
cursor re-touches ~one line, not the grid. Kitty `has_dirty_text` bit
(`line.h:86`), WezTerm line `seqno` (`render/mod.rs:872`), Ghostty
`false/partial/full` enum (`render.zig:266`) + per-row dirt. tmux's damage
minimizes **bytes to the pipe** (`screen-redraw.c` cell_type diff), not GPU draws.

### Packed cells
Bit-packed to fit cache lines / minimize CPU→GPU upload: Ghostty 8 B terminal
cell + 32 B GPU cell; Kitty 12 B CPU + 20 B GPU (split representation); WezTerm's
`TeenyString(u64)` small-string optimization; tmux's ~5 B `grid_cell_entry`.
Styles deduplicated by id (Ghostty `style_id`) or offset (tmux), not inline.

## Open questions
- Cursor rendering, selection highlighting, and inline-image compositing paths.
- Subpixel/gamma-correct blending differences.

## Sources
- `../comparisons/rendering.md`; per-terminal renderer files cited there
