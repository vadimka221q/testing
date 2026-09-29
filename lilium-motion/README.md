# LILIUM — motion study

A ~7.8s kinetic-type / botanical motion piece: swiss grid, pixel transitions, specimen labels, anatomy cards, "IN BLOOM", "LIVING GEOMETRY", "STUDIES".
All flowers are drawn procedurally in SVG, so no stock photos are needed.

- **Preview:** open `index.html` in a browser. Space = play/pause, ←/→ = step one frame, or drag the timeline.
- **Render MP4:** `npm i && npm run render` → `out/lilium.mp4` (1920×1080, 30fps). You need `ffmpeg` on PATH, or set `FFMPEG=/path/to/ffmpeg`.
- **Stills:** `node render.cjs --stills 0.9,2.9,6.6` → `out/stills/`.

The whole animation is `render(t)`, a pure function of time. Scene timings are in `SCENES`. Text, colours (`:root`, `PAL`) and flower shapes (`lilySVG`, `partSVG`) are all in `index.html`.
