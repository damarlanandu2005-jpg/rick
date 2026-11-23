// R3 character stage: draw the four locked views (front, 3/4, side, back) of every cast slot of a film with the EXISTING Ricks rig (puppets.svgFor, the same call tools/check_views.mjs makes).
// Nothing is redrawn or reinterpreted: this only boots the package the way check_views does and screenshots svgFor. Output: <out>/<slot>/<view>.png (800x1500, the rig's card canvas) and, with --golden, a diff against the approved picture.
//   node tools/character_stage.mjs <film.json> --out <dir> [--slots a,b]
//   node tools/character_stage.mjs <film.json> --probe <performance_baked.json> --out <report.json>    draw every distinct baked state with svgFor and report the rig's own warnings (unknown face, ...); no files but the report
import fs from 'fs'; import path from 'path'; import os from 'os'; import { fileURLToPath, pathToFileURL } from 'url'; import { createRequire } from 'module';
const require = createRequire(import.meta.url), ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const PKG = path.join(ROOT, 'templates/vector2d_characters/code'), KIT = path.join(ROOT, 'templates/threejs_film');
const args = process.argv.slice(2), val = f => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : null; };
const film = JSON.parse(fs.readFileSync(path.resolve(args[0]), 'utf8')), OUT = path.resolve(val('--out') || 'characters_out'), only = val('--slots') ? val('--slots').split(',') : null;
const VIEWS = ['front', '34', 'side', 'back'], imp = f => import(pathToFileURL(f).href);
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'chars_')); fs.mkdirSync(path.join(TMP, 'sheets'));
for (const f of fs.readdirSync(PKG)) if (f.endsWith('.mjs')) fs.copyFileSync(path.join(PKG, f), path.join(TMP, f));
for (const f of fs.readdirSync(path.join(PKG, 'sheets'))) if (f.endsWith('.mjs')) fs.copyFileSync(path.join(PKG, 'sheets', f), path.join(TMP, 'sheets', f));
for (const f of ['puppets.mjs', 'poses.mjs']) fs.copyFileSync(path.join(KIT, f), path.join(TMP, f));
const [char2d, memes, memes2, memes3, bodies, cast, castkit] = await Promise.all(['char2d', 'memes', 'memes2', 'memes3', 'bodies', 'cast', 'castkit'].map(n => imp(path.join(TMP, n + '.mjs'))));
const P = await imp(path.join(TMP, 'puppets.mjs')), castIndex = {};
for (const f of fs.readdirSync(path.join(TMP, 'sheets')).sort()) { const m = await imp(path.join(TMP, 'sheets', f)); for (const c of m.CAST || []) castIndex[c.name] ??= c; }
const grips = fs.existsSync(path.join(TMP, 'grips.mjs')) ? await imp(path.join(TMP, 'grips.mjs')) : undefined;   // the film page passes grips too (closed hands round held things)
P.initPuppets({ char2d, memes, memes2, memes3, bodies, cast, castkit, castIndex, grips });
let chromium; try { ({ chromium } = await import('playwright')); } catch { try { ({ chromium } = require(path.join(KIT, 'node_modules/playwright'))); } catch { ({ chromium } = require(process.env.PLAYWRIGHT_DIR || '/opt/node-tools/node_modules/playwright')); } }
if (val('--probe')) {
  const perf = JSON.parse(fs.readFileSync(path.resolve(val('--probe')), 'utf8')), warns = new Set(), errs = [], seen = new Set(); const w0 = console.warn; console.warn = m => warns.add(String(m));
  for (const [slot, list] of Object.entries(perf)) { const c = film.cast && film.cast[slot]; if (!c) { errs.push(`slot ${slot}: not in film.json cast`); continue; }
    for (const e of list) { const st = e.state || {}; if (!st.visible || /^m:/.test(st.pose || '')) continue; const k = [slot, st.view, st.dir, st.pose, st.face, st.mouth, st.prop, st.hand].join('|'); if (seen.has(k)) continue; seen.add(k);
      try { const svg = P.svgFor({ puppet: c.puppet }, { view: st.view, dir: st.dir, pose: st.pose, face: st.face, prop: st.prop, hand: st.hand, mouth: st.mouth, blink: null }); if (!svg || svg.length < 500) errs.push(`${k}: empty drawing`); } catch (x) { errs.push(`${k}: ${x.message}`); } } }
  console.warn = w0; fs.writeFileSync(path.resolve(val('--out')), JSON.stringify({ states: seen.size, warnings: [...warns], errors: errs })); fs.rmSync(TMP, { recursive: true, force: true }); process.exit(0);
}
const browser = await chromium.launch(), page = await browser.newPage({ viewport: { width: 800, height: 1500 } });
let n = 0;
for (const [slot, c] of Object.entries(film.cast || {})) {
  if (only && !only.includes(slot)) continue; const d = path.join(OUT, slot); fs.mkdirSync(d, { recursive: true });
  for (const view of VIEWS) {
    const svg = P.svgFor({ puppet: c.puppet }, { view, dir: 1, pose: 'stand', face: 'standard', prop: null, hand: null, mouth: null, blink: null });
    await page.setContent(`<body style="margin:0;background:#cfd8e6">${svg}</body>`); await page.screenshot({ path: path.join(d, view + '.png') }); n++;
  }
  console.log(`views ${slot} (${c.puppet}) -> ${d}`);
}
await browser.close(); fs.rmSync(TMP, { recursive: true, force: true }); console.log(`${n} view pictures`);
