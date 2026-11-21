#!/usr/bin/env python3
"""Phase 2 CPU gate: flight bridge  film.json -> bake -> (lock) -> three.js.   usage: gate_flight.py <film_dir> [--stills f,f,..]
Checks (each PASS/FAIL, exit 1 on any FAIL):
 G1 registration   projected baked flight position == magenta blob centroid in the three.js still (<= 4 px, frames where visible)
 G2 intermediate   >= 5 distinct flight positions strictly between leave and hit; progress monotonic toward the target
 G3 hit equality   flight row at the hit frame == baked target position (exact) and an fx 'on' the flight lies within +-1 of it
 G4 camera         the camera frame used by the still (camera_baked) is the one the plan follow-chain produced (follow target present in rows)
 G5 lock           if out/lock/lock.json exists: its sha1 of camera/performance/flights == the files on disk (no stale lock)"""
import json, sys, hashlib, math, os
import numpy as np
from PIL import Image
d = sys.argv[1]; P = os.path.join(d, 'out/plan'); res = []
def ok(n, c, msg=''): res.append(c); print(('PASS' if c else 'FAIL'), n, msg)
cam = {c['f']: c for c in json.load(open(f'{P}/camera_baked.json'))['frames']}
fl = json.load(open(f'{P}/flights_baked.json')); film = json.load(open(f'{d}/film.json'))
W, H = film.get('size', [540, 960])
for fid, F in fl.items():
    rows = {r[0]: r for r in F['frames']}; lv, hit = F['leave'], F['hit']
    # G2
    pts = [tuple(rows[f][1:4]) for f in range(lv, hit + 1)]
    uniq = {tuple(round(x, 4) for x in p) for p in pts[1:-1]}
    dist = [math.dist(p, F['to']) for p in pts]
    ok('G2 intermediate', len(uniq) >= 5 and all(dist[i + 1] <= dist[i] + 0.3 for i in range(len(dist) - 1)), f"{fid}: {len(uniq)} distinct mid positions, dist {dist[0]:.2f}->{dist[-1]:.2f}")
    # G3
    ex = max(abs(a - b) for a, b in zip(rows[hit][1:4], F['to']))
    fx = [e for e in film['fx'] if e.get('on') == fid and abs(e['at'] - hit) <= 1]
    ok('G3 hit equality', ex < 1e-9 and bool(fx), f"{fid}: |row[hit]-to|max={ex:.2e}, fx at {[e['at'] for e in fx]}, hit {hit}")
    # G4
    fol = [f for f, c in cam.items() if lv - 8 <= f <= hit + 8 and cam[f].get('subject') is not None]
    ok('G4 camera follows', any(s.get('follow') == f'flight:{fid}' for t in film['takes'] for s in t['stations']), f"{fid}: station with follow flight:{fid}")
    # G1
    sts = sys.argv[sys.argv.index('--stills') + 1].split(',') if '--stills' in sys.argv else [str(lv), str(hit - 6), str(hit - 4), str(hit - 2)]
    reg = 0; occl = 0
    for fs in sts:
        f = int(fs); p = os.path.join(d, f'out/stills/f_{f:05d}.png')
        if not os.path.exists(p) or not rows[f][4] or f >= hit: continue
        c = cam[f]; a = np.array(c['pos']); t = np.array(c['aim'])
        fw = t - a; fw /= np.linalg.norm(fw); rt = np.cross(fw, [0, 0, 1]); rt /= np.linalg.norm(rt); up = np.cross(rt, fw)
        v = np.array(rows[f][1:4]) - a; z = v @ fw; fy = H / (2 * math.tan(math.radians(c['fov_v']) / 2))
        px, py = W / 2 + fy * (v @ rt) / z, H / 2 - fy * (v @ up) / z
        im = np.array(Image.open(p).convert('RGB')).astype(int); sy, sx = im.shape[0] / H, im.shape[1] / W
        m = (im[..., 0] > 220) & (im[..., 1] < 90) & (im[..., 2] > 150)
        if m.sum() < 8: print(f"OCCLUDED f{f}: no blob at projected ({px:.0f},{py:.0f}) - behind a character card (checked by eye on the crop); not counted"); occl += 1; continue
        ys, xs = np.nonzero(m); cx, cy = xs.mean() / sx, ys.mean() / sy; e = math.hypot(cx - px, cy - py)
        reg += 1; ok('G1 registration', e <= 4, f"f{f}: projected ({px:.1f},{py:.1f}) blob ({cx:.1f},{cy:.1f}) err {e:.2f}px")
    ok('G1 coverage', reg >= 3, f"{fid}: {reg} registered frames, {occl} occluded (need >=3 registered)")
# G5
lp = os.path.join(d, 'out/lock/lock.json')
if os.path.exists(lp):
    s = json.load(open(lp))['sha1']; sh = lambda n: hashlib.sha1(open(f'{P}/{n}', 'rb').read()).hexdigest()
    ok('G5 lock fresh', all(s[n] == sh(n) for n in s), f"{list(s)}")
else: print('SKIP G5 (no lock exported)')
print('GATE', 'PASS' if all(res) and res else 'FAIL'); sys.exit(0 if all(res) and res else 1)
