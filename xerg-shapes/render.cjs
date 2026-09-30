// Renders index.html frame-by-frame into an MP4.
//   node render.cjs                      -> out/xerg-shapes.mp4 (1080x1080, 30fps)
//   node render.cjs --scale 1            -> 720x720
//   node render.cjs --stills 0.5,1.6,3   -> PNG stills into out/stills/
// Requires: playwright (npm i) and ffmpeg on PATH (or FFMPEG=/path/to/ffmpeg).
const { chromium } = require('playwright');
const { spawn } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf('--' + k); return i >= 0 ? args[i + 1] : d; };
const FPS = +opt('fps', 30);
const SCALE = +opt('scale', 1.5);
const OUT = path.resolve(__dirname, opt('out', 'out/xerg-shapes.mp4'));
const STILLS = opt('stills', null);
const FFMPEG = process.env.FFMPEG || 'ffmpeg';

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM || undefined });
  const page = await browser.newPage({ viewport: { width: 720, height: 720 }, deviceScaleFactor: SCALE });
  page.on('pageerror', e => console.error('page error:', e.message));
  await page.goto('file://' + path.resolve(__dirname, 'index.html') + '?render');
  await page.waitForFunction(() => window.__ready === true);
  const clip = { x: 0, y: 0, width: 720, height: 720 };

  if (STILLS) {
    const dir = path.resolve(__dirname, 'out/stills');
    fs.mkdirSync(dir, { recursive: true });
    for (const t of STILLS.split(',').map(Number)) {
      await page.evaluate(t => window.__render(t), t);
      await page.screenshot({ path: path.join(dir, `t${t.toFixed(2)}.png`), clip });
    }
    await browser.close();
    return;
  }

  const dur = await page.evaluate(() => window.__DUR);
  const frames = Math.round(dur * FPS);
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  const ff = spawn(FFMPEG, ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '15', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', OUT],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let i = 0; i < frames; i++) {
    await page.evaluate(t => window.__render(t), i / FPS);
    const buf = await page.screenshot({ type: 'png', clip });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 30 === 0) process.stdout.write(`\rframe ${i}/${frames}`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();
  console.log(`\nwrote ${OUT}`);
})();
