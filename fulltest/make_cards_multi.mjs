// fulltest/make_cards_multi.mjs -- GLUE ONLY. For every character in the script: runs EXISTING Ricks moves (templates/motion_styles)
// through the EXISTING rig (rig.mjs makeChar/drawPose), dressed with an EXISTING cast sheet outfit (cast_western.mjs = recolour only),
// and writes what the EXISTING Blender card code reads (blender_look/from_lock.py card()):
//   <out>/cards/<who>/s0001.png ... + index.json  (runs carry the shot number; Blender sets pos/flip per shot)
// usage: node fulltest/make_cards_multi.mjs <script.json> <out_lock_dir>
import fs from 'fs'; import path from 'path'; import crypto from 'crypto'; import { createRequire } from 'module';
import { fileURLToPath, pathToFileURL } from 'url';
const HERE = path.dirname(fileURLToPath(import.meta.url)), ROOT = path.resolve(HERE, '..');
const die = m => { console.error('FULL_ERROR make_cards_multi: ' + m); process.exit(1); };
const [, , scriptPath, outDir] = process.argv;
if (!scriptPath || !outDir) die('usage: node make_cards_multi.mjs <script.json> <out_lock_dir>');
const S = JSON.parse(fs.readFileSync(scriptPath, 'utf8')), FPS = S.fps || 30, SC = S.px_scale || 1;
let chromium;
try { ({ chromium } = await import('playwright')); } catch { try { ({ chromium } = createRequire(import.meta.url)(process.env.PLAYWRIGHT_DIR || 'playwright')); } catch (e) { die('playwright missing. Run: cd slice01 && npm install && npx playwright install --with-deps chromium'); } }
const rig = await import(pathToFileURL(path.join(ROOT, 'templates/motion_styles/rig.mjs')).href).catch(e => die('cannot load rig.mjs: ' + e.message.split('\n')[0]));
const { WESTERN } = await import(pathToFileURL(path.join(HERE, 'cast_western.mjs')).href).catch(e => die('cannot load cast_western.mjs: ' + e.message.split('\n')[0]));
const { makeChar, drawPose, G } = rig;
const MOVES = 'templates/motion_styles/moves/';
const loadMove = async (name, style) => { const own = path.join(HERE, 'moves', name + '.mjs'), f = fs.existsSync(own) ? own : path.join(ROOT, MOVES, name + '.mjs'); if (!fs.existsSync(f)) die(`move "${name}" not found in fulltest/moves or ${MOVES}`);
  const mod = (await import(pathToFileURL(f).href)).default; const st = mod?.styles?.find(x => x.key === style); if (!st) die(`style "${style}" not in move ${name} (has ${(mod?.styles || []).map(x => x.key).join(',')})`); return { mod, st }; };
function parts(st, t, ch) {
  const out = st.pose(t, ch), poses = Array.isArray(out.poses) ? out.poses : [out]; const defs = []; let ids = 0;
  const body = poses.map(P => { const r = drawPose(ch, P), pre = `q${ids++}_`; defs.push(r.defs.replace(/id="([gc]\d+)"/g, (m, id) => `id="${pre}${id}"`)); return r.svg.replace(/url\(#([gc]\d+)\)/g, (m, id) => `url(#${pre}${id})`); }).join('');
  return { defs: defs.join(''), g: (out.back || '') + body + (out.front || '') };
}
const shotFrames = S.shots.map(s => Math.round(s.sec * FPS)), total = shotFrames.reduce((a, b) => a + b, 0), starts = []; { let a = 1; for (const n of shotFrames) { starts.push(a); a += n; } }
const browser = await chromium.launch().catch(e => die('chromium failed: ' + e.message.split('\n')[0]));
const page = await browser.newPage({ viewport: { width: 1600, height: 1800 }, deviceScaleFactor: 1 });
await page.setContent('<html><body style="margin:0;background:transparent;overflow:hidden"></body></html>');
const wrap = (p, vb, W, H) => `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="${vb}"><defs>${p.defs}</defs><g id="c">${p.g}</g></svg>`;
const report = { total_frames: total, shots: S.shots.length, cards: {} };
for (const [who, cdef] of Object.entries(S.cast)) {
  const maker = WESTERN[cdef.spec]; if (!maker) die(`cast "${who}": spec "${cdef.spec}" not in fulltest/cast_western.mjs (has ${Object.keys(WESTERN).join(',')})`);
  const spec = maker(), ch = makeChar(spec.form || 'standard', { coat: spec.coat, spec });
  const frames = new Array(total).fill(null), shotOf = new Array(total).fill(0);
  for (const [si, sh] of S.shots.entries()) {
    const c = (sh.chars || []).find(x => x.id === who); if (!c) continue;
    const { st } = await loadMove(c.move, c.style);
    for (let k = 0; k < shotFrames[si]; k++) { const f = starts[si] - 1 + k; shotOf[f] = si + 1;
      try { frames[f] = parts(st, (c.start || 0) + k / FPS, ch); } catch (e) { die(`${who} shot ${sh.id} frame ${k}: ${e.message.split('\n')[0]}`); } }
  }
  const present = frames.filter(Boolean); if (!present.length) { console.log(`note: ${who} appears in no shot, skipped`); continue; }
  let ux0 = 1e9, ux1 = -1e9, uy0 = 1e9, uy1 = -1e9; const tops = [];
  for (const p of present) { const b = await page.evaluate(s => { document.body.innerHTML = s; const bb = document.getElementById('c').getBBox(); return [bb.x, bb.y, bb.x + bb.width, bb.y + bb.height]; }, wrap(p, '-1000 -400 2000 1800', 1600, 1440));
    ux0 = Math.min(ux0, b[0]); ux1 = Math.max(ux1, b[2]); uy0 = Math.min(uy0, b[1]); uy1 = Math.max(uy1, b[3]); tops.push(b[1]); }
  const M = 30, half = Math.ceil(Math.max(Math.abs(ux0), Math.abs(ux1)) + M), y0 = Math.floor(uy0 - M), y1 = Math.ceil(Math.max(uy1, G) + M);
  const Wp = Math.round(2 * half * SC), Hp = Math.round((y1 - y0) * SC), VB = `${-half} ${y0} ${2 * half} ${y1 - y0}`;
  tops.sort((a, b) => a - b); const figure_px = Math.round((G - tops[Math.floor(tops.length / 2)]) * SC);
  if (Wp > 4000 || Hp > 4000 || Wp < 50 || Hp < 50) die(`${who}: implausible card size ${Wp}x${Hp}`);
  const dir = path.join(outDir, 'cards', who); fs.rmSync(dir, { recursive: true, force: true }); fs.mkdirSync(dir, { recursive: true });
  await page.setViewportSize({ width: Wp, height: Hp }); const seen = new Map(), runs = []; let nimg = 0;
  for (let i = 0; i < total; i++) {
    const p = frames[i], f = i + 1, last = runs[runs.length - 1];
    if (!p) { if (last && last.visible === false && last.f1 === f - 1) last.f1 = f; else runs.push({ f0: f, f1: f, img: 1, pos: [0, 0, 0], visible: false, flip: false, shot: 0 }); continue; }
    const svg = wrap(p, VB, Wp, Hp), key = crypto.createHash('sha1').update(svg).digest('hex');
    if (!seen.has(key)) { await page.evaluate(s => { document.body.innerHTML = s; }, svg); nimg++; seen.set(key, nimg);
      await page.screenshot({ path: path.join(dir, `s${String(nimg).padStart(4, '0')}.png`), omitBackground: true, clip: { x: 0, y: 0, width: Wp, height: Hp } }); }
    const img = seen.get(key);
    if (last && last.visible && last.img === img && last.f1 === f - 1 && last.shot === shotOf[i]) last.f1 = f; else runs.push({ f0: f, f1: f, img, pos: [0, 0, 0], visible: true, flip: false, shot: shotOf[i] });
  }
  if (runs.some(r => !r.visible) && nimg === 0) die(`${who}: nothing drawn`);
  const K0 = (cdef.height_m || 1.8) / figure_px;
  fs.writeFileSync(path.join(dir, 'index.json'), JSON.stringify({ puppet: 'cast:' + cdef.spec, metres_per_px: K0, px: [Wp, Hp], ground_px: Math.round((G - y0) * SC), figure_px, height_m: cdef.height_m || 1.8, fps: FPS, images: nimg, runs }));
  report.cards[who] = { card_px: [Wp, Hp], figure_px, distinct_drawings: nimg, runs: runs.length, visible_frames: present.length };
}
await browser.close();
fs.mkdirSync(outDir, { recursive: true }); fs.writeFileSync(path.join(outDir, 'cards_report.json'), JSON.stringify(report, null, 1));
console.log('CARDS_REPORT ' + JSON.stringify(report));
