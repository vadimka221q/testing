# xerg — brand identity reel

A 9.2s motion reel for the xerg identity by Sollas, built on the brand's reticle language: corner brackets, focus frames, calibration scales and the 64px grid.

**Assets are not in git** (this repo is public). Put them in `assets/`:
`Logomark_White.svg`, `ill0–3.svg` (site illustrations), `hoodie.jpg`, `cap.jpg`, `folder.jpg`, `mark.jpg`, `billboard.jpg`, `reticle.jpg` (from the brand book). Then run `npm run assets`.

- Preview: open `index.html`. Space = play/pause, ←/→ = step one frame.
- Render: `npm i && npm run render` → `out/xerg.mp4` (1920×1080, 30fps). Needs ffmpeg (or set `FFMPEG=`).
- Palette, copy and timings are all in `index.html` (`C`, `SCENES`, the per-scene `render*` functions).
