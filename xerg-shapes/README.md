# xerg — grainy shapes loop (1:1)

A 6.2s square piece in the xerg palette. The sequence runs:
1. A black window with grainy gradient bars.
2. A burst of shapes (xerg marks as the "pyramids") flying toward the camera.
3. White construction lines that build the 64px brand grid.
4. The mark assembles from grid cells, then the logo appears.

The whole piece is drawn on one canvas. Stippled gradients are baked into textures at load time, and the film grain is animated on top.

- Preview: open `index.html`. The logo comes from `../xerg-motion/assets/assets.js`, which is not committed (see that folder's README).
- Render: `node render.cjs` → `out/xerg-shapes.mp4` (1080×1080, 30fps).
- For X, re-encode lighter: `ffmpeg -i out/xerg-shapes.mp4 -c:v libx264 -preset slow -crf 25 -pix_fmt yuv420p -movflags +faststart out/xerg-shapes-x.mp4`
