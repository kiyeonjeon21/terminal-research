# Inline Graphics / Images

> Learning note. Facts cite source; assumptions are marked _(assumption)_.

## Question
How do images (not just text) get onto a terminal grid, and what are the
competing protocols?

## Key concepts
- why the text grid needs an out-of-band image protocol
- Kitty graphics protocol (APC) vs Sixel (DCS) vs iTerm2 (OSC 1337)
- how images bind to cells and interact with scrollback

## Findings

### Why a protocol at all
The base VT model is a matrix of fixed-size **text cells** — there is no
pixel-addressing primitive. So images need an out-of-band escape sequence that
ships pixel data and pins it to a rectangle of cells (Kitty `ImageRef`/
placements, Ghostty `PlacementMap`, WezTerm `assign_image_to_cells`, tmux
`image_store`). See `../comparisons/graphics.md`.

### The three protocols
- **Sixel** — DCS `\eP…q…\e\\`. 1980s DEC bitmap: six vertical pixels per
  character, palette-indexed. Simple, widely supported, but limited (color-
  register constrained, verbose, no placement/z-index model).
- **Kitty graphics** — APC `\e_G<control>;<base64>\e\\`. The most capable:
  explicit control keys, **multiple transmission mediums**
  (direct / file / temp-file / **POSIX shared memory** — avoids escape-stream
  bloat for large images), placements, **z-index layering** (images above or
  below text), animation, Unicode placeholders. Most complex.
- **iTerm2** — OSC `\e]1337;File=<key=val>:<base64>\a`. A single self-contained
  base64 blob of a standard image file (PNG/JPEG). Simplest to emit; no
  placement/animation/shared-memory model.

### Images are grid-bound and ephemeral
Images move with scroll (Kitty factors `scrolled_by` into `grman_update_layers`,
`graphics.c:1210`) but are freed when their underlying cells are overwritten or
scrolled — tmux explicitly `image_free`s on `image_check_line` / `image_scroll_up`
(`image.c`). So an image is tied to grid coordinates, not to a persistent object.

### Who supports what (verified — `../comparisons/graphics.md`)
- **Kitty** — reference impl of its own protocol; **no** Sixel in this checkout.
- **Ghostty** — Kitty graphics only; OSC 1337 `File=` is parsed but unimplemented.
- **WezTerm** — the generalist: all three (Kitty + Sixel + iTerm2).
- **tmux** — native **Sixel** only (`ENABLE_SIXEL`); everything else requires
  `allow-passthrough` DCS wrapping (same passthrough seen in exp 005).

## Open questions
- Kitty graphics Unicode-placeholder mechanism (image in scrollback via
  placeholder chars).
- Terminal capability negotiation for images (how apps detect support).

## Sources
- `../comparisons/graphics.md`; per-terminal graphics files cited there
