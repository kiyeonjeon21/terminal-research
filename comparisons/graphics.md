# Inline Graphics / Image Protocols — Comparison

> Breadth/learning study. How images (not just text) get onto the grid. Cite
> `file:line`. Background in `../notes/graphics.md`.

## Question
Which inline-image protocols does each terminal support, and how?

Three protocols exist: **Kitty graphics** (APC `\e_G…`, Kitty invented it),
**Sixel** (DCS, 1980s DEC bitmap), **iTerm2** (OSC 1337 `File=…:base64`).

| Terminal | Kitty graphics | Sixel | iTerm2 `File=` | Notes |
| -------- | -------------- | ----- | -------------- | ----- |
| **Kitty** | **reference impl** — APC parsed `vt-parser.c:1421`, executed `graphics.c:2219` | **no** (0 matches in this checkout) | no | invented the protocol; z-index layers, shared-mem transport |
| **Ghostty** | **full** — `graphics_exec.zig`, `Terminal.zig:3354` | no decode (only a DA enum value `device_attributes.zig:53`) | parsed but **unimplemented → `.invalid`** (`iterm2.zig:190`) | Kitty graphics is its only image path |
| **WezTerm** | **full** — `apc.rs`, `kitty.rs:174` | **full native decoder** (`sixel.rs:10`) | **full** (`iterm.rs:10`) | **the only one supporting all three** |
| **tmux** | **passthrough only** (`allow-passthrough` DCS wrap) | **native** (`ENABLE_SIXEL`, `input.c:2629` → `image-sixel.c`) | passthrough only | natively decodes Sixel; wraps the rest in `\ePtmux;…` |

## Notes
- **Why a protocol at all:** the base VT grid is fixed-size text cells with no
  pixel-addressing primitive. Each protocol ships pixel data out-of-band and pins
  it to a rectangle of cells (Kitty `ImageRef`/placements, Ghostty `PlacementMap`,
  WezTerm `assign_image_to_cells`, tmux `image_store`).
- **Three transports:** Sixel = DCS `\eP…q…` (six pixels/char, palette-indexed,
  verbose, no z-index); Kitty = APC `\e_G<control>;<base64>` with control keys,
  **multiple transmission mediums** (direct/file/temp-file/**shared memory**,
  `graphics.c:557`), z-index layering (`graphics.c:1210-1395`), animation, Unicode
  placeholders; iTerm2 = OSC 1337 `File=` — a single self-contained base64 blob of
  a standard image file (simplest to emit, no placement/animation).
- **Images are grid-bound and ephemeral.** They move with scroll (Kitty factors
  `scrolled_by` into `grman_update_layers`) but are freed when their cells are
  overwritten/scrolled — tmux explicitly `image_free`s on `image_check_line` /
  `image_scroll_up` (`image.c`).
- **Notable:** Kitty (the protocol's inventor) decodes **no** Sixel in this
  checkout; Ghostty does images **only** via the Kitty protocol (its OSC 1337
  `File=` is explicitly unimplemented); WezTerm is the generalist (all three);
  tmux natively does only Sixel and leans on `allow-passthrough` for the rest —
  the same passthrough seen for cwd/OSC in exp 005.

## Sources
Per-terminal graphics files above; `../notes/graphics.md`.
