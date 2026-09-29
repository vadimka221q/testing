// Packs the brand SVGs from assets/ into assets/assets.js so index.html can
// inline them (works from file:// without a server).  Run once after changing assets.
const fs = require('node:fs');
const path = require('node:path');
const dir = path.join(__dirname, 'assets');
const read = f => fs.readFileSync(path.join(dir, f), 'utf8');
// strip the "FROM INSTALL TO GOVERNANCE" caption and the <<<< arrows baked into the site illustrations
const clean = s => s.replace(/<path d="(M49\.4 61|M759\.668 557|M743\.5 557)[^"]*"[^>]*\/>/g, '');
const out = {
  logo: read('Logomark_White.svg'),
  ill0: clean(read('ill0.svg')),
  ill1: clean(read('ill1.svg')),
  ill2: clean(read('ill2.svg')),
  ill3: clean(read('ill3.svg')),
};
fs.writeFileSync(path.join(dir, 'assets.js'), 'window.ASSETS=' + JSON.stringify(out) + ';\n');
console.log('wrote assets/assets.js');
