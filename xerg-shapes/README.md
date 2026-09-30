# xerg — grainy shapes (16:9)

A 5.85s 16:9 piece in the xerg palette. The sequence runs:
1. A black window with grainy gradient bars.
2. A burst of shapes (xerg marks as the "pyramids") flying toward the camera.
3. White construction lines that build the 64px brand grid.
4. The mark assembles from grid cells, then the logo appears.

The whole piece is drawn on one canvas. Stippled gradients are baked into textures at load time, and the film grain is animated on top.

- Preview: open `index.html`. The logo comes from `../xerg-motion/assets/assets.js`, which is not committed (see that folder's README).
- Render: `node render.cjs` → `out/xerg-shapes.mp4` (1920×1080, 30fps).
- For X, re-encode lighter: `ffmpeg -i out/xerg-shapes.mp4 -c:v libx264 -preset slow -crf 25 -pix_fmt yuv420p -movflags +faststart out/xerg-shapes-x.mp4`
- Sound: `python3 sound.py` → `out/sfx.wav`. It is minimal: three soft hits, swishes, a few ticks and four notes on the mark. Normalise it to -14 LUFS and mux it into the video, as described in `../xerg-motion/README.md`.
- Easing: `E` holds custom cubic-bezier curves (`settle`, `whip`, `pop`, `blast`, …) and every motion uses one of them.
