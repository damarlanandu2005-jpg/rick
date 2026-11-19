// slice01/make_cards.mjs  --  GLUE ONLY. Runs EXISTING Ricks moves (templates/motion_styles) through the EXISTING rig
// (rig.mjs makeChar / drawPose) and writes what the EXISTING Blender card code (blender_look/from_lock.py card()) reads:
//   <out>/cards/hero/s0001.png ... (transparent PNGs, one per distinct drawing) + <out>/cards/hero/index.json
// usage: node slice01/make_cards.mjs <config.json> <out_lock_dir>
import fs from 'fs'; import path from 'path'; import crypto from 'crypto'; import { createRequire } from 'module';
import { fileURLToPath, pathToFileURL } from 'url';
const HERE = path.dirname(fileURLToPath(import.meta.url)), ROOT = path.resolve(HERE, '..');
const die = m => { console.error('SLICE_ERROR make_cards: ' + m); process.exit(1); };
const [, , cfgPath, outDir] = process.argv;
if (!cfgPath || !outDir) die('usage: node make_cards.mjs <config.json> <out_lock_dir>');
if (!fs.existsSync(cfgPath)) die('config not found: ' + cfgPath);
const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8')), FPS = cfg.fps || 30, SC = cfg.puppet?.px_scale || 1;

let chromium;
try { ({ chromium } = await import('playwright')); }
catch { try { ({ chromium } = createRequire(import.meta.url)(process.env.PLAYWRIGHT_DIR || 'playwright')); }
  catch (e) { die('playwright is not installed. Run: cd slice01 && npm install && npx playwright install chromium   (' + e.message.split('\n')[0] + ')'); } }
let rig;
try { rig = await import(pathToFileURL(path.join(ROOT, 'templates/motion_styles/rig.mjs')).href); }
catch (e) { die('cannot load templates/motion_styles/rig.mjs (is the branch complete?): ' + e.message.split('\n')[0]); }
const { makeChar, drawPose, G } = rig;

// ---- 1. every frame of every segment -> svg parts (same id-prefixing as templates/motion_styles/stage.mjs)
function parts(st, t, ch) {
  const out = st.pose(t, ch), poses = Array.isArray(out.poses) ? out.poses : [out]; const defs = []; let ids = 0;
  const body = poses.map(P => { const r = drawPose(ch, P), pre = `q${ids++}_`;
    defs.push(r.defs.replace(/id="([gc]\d+)"/g, (m, id) => `id="${pre}${id}"`));
    return r.svg.replace(/url\(#([gc]\d+)\)/g, (m, id) => `url(#${pre}${id})`); }).join('');
  return { defs: defs.join(''), g: (out.back || '') + body + (out.front || '') };
}
const frames = [], segs = [];
for (const [si, s] of (cfg.segments || []).entries()) {
  const file = path.join(ROOT, s.move); if (!fs.existsSync(file)) die(`segment ${si}: move file missing: ${s.move}`);
  const mod = (await import(pathToFileURL(file).href)).default; if (!mod?.styles) die(`segment ${si}: ${s.move} has no default export with styles`);
  const st = mod.styles.find(x => x.key === s.style); if (!st) die(`segment ${si}: style ${s.style} not in ${s.move} (has ${mod.styles.map(x => x.key).join(',')})`);
  const ch = makeChar(s.form || st.form || mod.form || cfg.puppet?.form || 'standard', { coat: st.coat });
  const n = Math.round(s.seconds * FPS), f0 = frames.length + 1;
  for (let k = 0; k < n; k++) { let p; try { p = parts(st, k / FPS, ch); } catch (e) { die(`segment ${si} frame ${k}: ${e.message.split('\n')[0]}`); } frames.push(p); }
  segs.push({ move: s.move, style: s.style, f0, f1: frames.length });
}
if (!frames.length) die('no segments in config');

// ---- 2. one fixed window for the whole card (union of every frame, symmetric about x = 0, feet on the rig ground line G)
const t0 = Date.now(), browser = await chromium.launch().catch(e => die('chromium failed to launch: ' + e.message.split('\n')[0] + '  (run: npx playwright install --with-deps chromium)'));
const page = await browser.newPage({ viewport: { width: 1600, height: 1800 }, deviceScaleFactor: 1 });
await page.setContent('<html><body style="margin:0;background:transparent;overflow:hidden"></body></html>');
const wrap = (p, vb, W, H) => `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="${vb}"><defs>${p.defs}</defs><g id="c">${p.g}</g></svg>`;
let ux0 = 1e9, ux1 = -1e9, uy0 = 1e9, uy1 = -1e9; const tops = [];
for (const p of frames) {
  const b = await page.evaluate(s => { document.body.innerHTML = s; const bb = document.getElementById('c').getBBox(); return [bb.x, bb.y, bb.x + bb.width, bb.y + bb.height]; }, wrap(p, '-1000 -400 2000 1800', 1600, 1440));
  ux0 = Math.min(ux0, b[0]); ux1 = Math.max(ux1, b[2]); uy0 = Math.min(uy0, b[1]); uy1 = Math.max(uy1, b[3]); tops.push(b[1]);
}
const M = 30, half = Math.ceil(Math.max(Math.abs(ux0), Math.abs(ux1)) + M), y0 = Math.floor(uy0 - M), y1 = Math.ceil(Math.max(uy1, G) + M);
const Wp = Math.round(2 * half * SC), Hp = Math.round((y1 - y0) * SC), VB = `${-half} ${y0} ${2 * half} ${y1 - y0}`;
tops.sort((a, b) => a - b); const topMed = tops[Math.floor(tops.length / 2)], figure_px = Math.round((G - topMed) * SC);
if (Wp > 4000 || Hp > 4000 || Wp < 50 || Hp < 50) die(`implausible card size ${Wp}x${Hp} (union bbox x ${ux0.toFixed(0)}..${ux1.toFixed(0)}, y ${uy0.toFixed(0)}..${uy1.toFixed(0)}). A move probably draws far-away props.`);

// ---- 3. render the distinct drawings only (a held pose is one picture), then one run per held stretch
const dir = path.join(outDir, 'cards', 'hero'); fs.rmSync(dir, { recursive: true, force: true }); fs.mkdirSync(dir, { recursive: true });
await page.setViewportSize({ width: Wp, height: Hp }); const seen = new Map(), runs = []; let nimg = 0;
for (const [i, p] of frames.entries()) {
  const svg = wrap(p, VB, Wp, Hp), key = crypto.createHash('sha1').update(svg).digest('hex');
  if (!seen.has(key)) {
    await page.evaluate(s => { document.body.innerHTML = s; }, svg); nimg++; seen.set(key, nimg);
    await page.screenshot({ path: path.join(dir, `s${String(nimg).padStart(4, '0')}.png`), omitBackground: true, clip: { x: 0, y: 0, width: Wp, height: Hp } });
  }
  const img = seen.get(key), f = i + 1, last = runs[runs.length - 1];
  if (last && last.img === img && last.f1 === f - 1) last.f1 = f; else runs.push({ f0: f, f1: f, img, pos: [0, 0, 0], visible: true, flip: false });
}
await browser.close();
const K0 = 0.0017;   // provisional metres per px; blender_slice.py sets the real one from the casino character's size
fs.writeFileSync(path.join(dir, 'index.json'), JSON.stringify({ puppet: 'form:standard', metres_per_px: K0, px: [Wp, Hp], ground_px: Math.round((G - y0) * SC), figure_px, height_m: +(figure_px * K0).toFixed(3), fps: FPS, images: nimg, runs }));
const rep = { frames: frames.length, seconds: +(frames.length / FPS).toFixed(2), distinct_drawings: nimg, runs: runs.length, card_px: [Wp, Hp], figure_px, ground_px: Math.round((G - y0) * SC), segments: segs, render_s: +((Date.now() - t0) / 1000).toFixed(1) };
fs.writeFileSync(path.join(outDir, 'cards_report.json'), JSON.stringify(rep, null, 1));
console.log('CARDS_REPORT ' + JSON.stringify(rep));
