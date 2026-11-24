// HEAT LINE ("The Gap", first real production 2026-11-24; V1.1 after independent judge v1): an ORIGINAL high-summer meadow with two railway lines side by side.
// Story only came from the reference; nothing here is taken from its look. Plan metres, Z up, Y away from the opening camera.
// Line A (ours, x = -1.8): older darker steel in 12 m lengths, an open cartoon-scale joint between each; the hero joint at y = 0 is the registry asset
//   prop_rail_joint_gapped (film.json name "joint"), so this set leaves y in [-3, 3] empty on line A.
// Line B (the "perfect" one, x = +1.8): one continuous ribbon of bright new steel. The 6 m centred on the kink asset's film.json position
//   is drawn here as a LIVE track that shows the mechanism: from "pushes" it shivers and starts to bow, on "snaps" it throws into the S
//   (the same curve the asset is built from), then the registry asset prop_track_buckled (film.json name "kink") takes over for the hold.
// V1.1 also shows "room": from the word "The" the rail ends on line A grow into the open joint, hot at the tip, and stop short.
// Heat: a white-hot sun over the far end of the line and a rising shimmer over both lines (overlays, noExport). Rails sit on tie plates, sleepers bed into crib ballast.
// Rails are toon in the assets' own colours (no PBR/toon seam where set rails meet the registry assets). Every mesh has a stable NAME and a ROLE.
export async function build(THREE, scene, film, ctx) {
  const { B2T, toon } = ctx, n = {};
  let seed = 11; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  const add = (m, name, role, o = {}) => { n[name] = (n[name] || 0) + 1; m.name = n[name] > 1 ? `${name}_${String(n[name]).padStart(2, '0')}` : name; m.userData.role = role; if (o.mat) m.userData.mat = o.mat; if (o.noExport) m.userData.noExport = true; m.castShadow = o.cast ?? true; m.receiveShadow = true; (o.parent || scene).add(m); return m; };
  const box = (name, role, w, d, h, at, mat, o = {}) => { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), typeof mat === 'string' ? toon(mat) : mat); m.position.copy(B2T([at[0], at[1], at[2] + h / 2])); if (o.rot) m.rotation.y = o.rot; return add(m, name, role, o); };
  const cyl = (name, role, r, h, at, mat, o = {}) => { const m = new THREE.Mesh(new THREE.CylinderGeometry(o.r2 ?? r, r, h, o.seg ?? 12), typeof mat === 'string' ? toon(mat) : mat); m.position.copy(B2T([at[0], at[1], at[2] + h / 2])); return add(m, name, role, o); };

  const grass = ctx.relief('grass', '#8db04a', { scale: 1.0 }), ballast = ctx.relief('cobble', '#8f8578', { scale: .16 }), wood = toon('#4a3626'), plateM = toon('#3d4146');
  const steelA = toon('#767c83'), steelB = toon('#c3c9cf'), endM = toon('#d4d9de');      // the v1.1 assets' own colours: ours older and darker, the perfect line bright and new
  const BED = .12, RAIL_H = .17, GAUGE = .72, SLEEP = .65;
  const pl = (film.places || {}).meadow || {}, kinkAt = (pl.assets || []).find(a => a && a.name === 'kink'), KY = kinkAt ? kinkAt.at[1] : 20;

  // ground: one big meadow, a darker mown strip along the lines
  box('meadow', 'ground', 420, 420, .2, [0, 120, -.2], grass, { cast: false, mat: 'turf' });
  box('mown_strip', 'ground', 9, 160, .02, [0, 50, -.01], ctx.relief('grass', '#7d9f40', { scale: .7 }), { cast: false, mat: 'turf' });

  // two ballast beds with sloped shoulders (top z = BED) + crib ballast between the sleepers (top z = BED + .06): sleepers bed in, they do not sit on a slab
  for (const [x, nm] of [[-1.8, 'ballast_a'], [1.8, 'ballast_b']]) {
    const g = new THREE.BoxGeometry(3.6, BED, 170), P = g.attributes.position; for (let i = 0; i < P.count; i++) if (P.getY(i) > 0) P.setX(i, P.getX(i) * 2.85 / 3.6); g.computeVertexNormals();
    const m = new THREE.Mesh(g, ballast); m.position.copy(B2T([x, 45, BED / 2])); add(m, nm, 'ground', { cast: false, mat: 'gravel' });
    const c = new THREE.BoxGeometry(2.62, .06, 170), Q = c.attributes.position; for (let i = 0; i < Q.count; i++) if (Q.getY(i) > 0) Q.setX(i, Q.getX(i) * 2.45 / 2.62); c.computeVertexNormals();
    const cm = new THREE.Mesh(c, ballast); cm.position.copy(B2T([x, 45, BED + .03])); add(cm, nm + '_crib', 'ground', { cast: false, mat: 'gravel' });
  }

  // sleepers every 0.65 m with a tie plate under each rail (none where an asset or the live buckle stands)
  const sleepers = (cx, skip) => { for (let y = -40; y < 130; y += SLEEP) { if (y > skip[0] && y < skip[1]) continue; box('sleeper', 'wood', 2.5, .24, BED, [cx, y, BED], wood, { cast: false, mat: 'wood_grain' }); for (const sx of [-1, 1]) box('tie_plate', 'metal', .34, .2, .016, [cx + sx * GAUGE, y, 2 * BED - .004], plateM, { cast: false, mat: 'metal' }); } };
  sleepers(-1.8, [-3.1, 3.1]); sleepers(1.8, [KY - 3.1, KY + 3.1]);

  // line A: 12 m lengths, an open 19 cm joint between them (same cartoon scale as the hero asset) with a bright end face; the hero joint at y = 0 is the asset
  const JA = .19;
  for (const sx of [-1, 1]) {
    for (let y0 = 3; y0 < 130; y0 += 12) { box('rail_a', 'metal', .07, 12 - JA, RAIL_H, [-1.8 + sx * GAUGE, y0 + 6 + JA / 2, 2 * BED], steelA, { mat: 'metal' }); box('rail_a_end', 'metal', .074, .008, .042, [-1.8 + sx * GAUGE, y0 + JA - .004, 2 * BED + .13], endM, { mat: 'metal', cast: false }); }
    for (let y1 = -3; y1 > -40; y1 -= 12) box('rail_a', 'metal', .07, 12 - JA, RAIL_H, [-1.8 + sx * GAUGE, y1 - 6 - JA / 2, 2 * BED], steelA, { mat: 'metal' });
  }
  // line B: one continuous bright ribbon either side of the live buckle stretch
  for (const sx of [-1, 1]) {
    box('rail_b', 'metal', .07, KY - 3 + 40, RAIL_H, [1.8 + sx * GAUGE, (KY - 3 - 40) / 2, 2 * BED], steelB, { mat: 'metal' });
    box('rail_b', 'metal', .07, 130 - (KY + 3), RAIL_H, [1.8 + sx * GAUGE, (130 + KY + 3) / 2, 2 * BED], steelB, { mat: 'metal' });
  }

  // ---- the LIVE buckle (line B, KY - 3 .. KY + 3): the asset's own curve dx(y) = A sin(2 pi u) sin^2(pi u), amplitude driven by the words
  const L = 6, A_FULL = .42, NS = 30, dx = (y, A) => { const u = (y + L / 2) / L; return A * Math.sin(2 * Math.PI * u) * Math.sin(Math.PI * u) ** 2; };
  const live = new THREE.Group(); live.name = 'live_buckle'; scene.add(live); const liveRails = [], liveSleepers = [];
  for (const sx of [-1, 1]) for (let i = 0; i < NS; i++) { const m = new THREE.Mesh(new THREE.BoxGeometry(.07, RAIL_H, L / NS + .014), steelB); add(m, 'rail_b_live', 'metal', { mat: 'metal', parent: live }); liveRails.push([m, sx, i]); }
  for (let k = 0; k < 10; k++) { const g = new THREE.Group(), s = new THREE.Mesh(new THREE.BoxGeometry(2.5, BED, .24), wood); s.position.y = BED / 2; add(s, 'sleeper_b_live', 'wood', { mat: 'wood_grain', cast: false, parent: g }); for (const sx of [-1, 1]) { const tp = new THREE.Mesh(new THREE.BoxGeometry(.34, .016, .2), plateM); tp.position.set(sx * GAUGE, BED + .004, 0); add(tp, 'tie_plate_b_live', 'metal', { cast: false, parent: g }); } live.add(g); liveSleepers.push([g, -L / 2 + .3 + .6 * k]); }
  const slope = (y, A) => Math.atan((dx(y + .01, A) - dx(y - .01, A)) / .02);
  const poseLive = (A, jit) => {
    for (const [m, sx, i] of liveRails) { const y0 = -L / 2 + (i + .5) * L / NS; m.position.copy(B2T([1.8 + dx(y0, A) + sx * GAUGE + jit, KY + y0, 2 * BED + RAIL_H / 2])); m.rotation.y = ROT * slope(y0, A); }
    for (const [g, y0] of liveSleepers) { g.position.copy(B2T([1.8 + dx(y0, A) + jit * .5, KY + y0, BED])); g.rotation.y = ROT * slope(y0, A) * .9; }
  };
  const ROT = -1;      // sign of a plan-space slope as a three.js rotation about Y (B2T: plan y -> three -z)
  poseLive(0, 0);

  // ---- "room": the rail ends on line A grow into the hero joint (hot tip), then stop 5.5 cm short of the far rail end
  const grow = [];
  for (const sx of [-1, 1]) { const g = new THREE.Group(); g.position.copy(B2T([-1.8 + sx * GAUGE, .095, 2 * BED])); g.name = 'room_grow'; scene.add(g);
    const body = new THREE.Mesh(new THREE.BoxGeometry(.072, RAIL_H, 1), steelA); body.position.set(0, RAIL_H / 2, 0); add(body, 'rail_a_growth', 'metal', { mat: 'metal', parent: g, cast: false });
    const tip = new THREE.Mesh(new THREE.BoxGeometry(.078, RAIL_H * .5, .014), new THREE.MeshBasicMaterial({ color: '#ff9a3c', toneMapped: false })); tip.position.set(0, RAIL_H * .78, 0); add(tip, 'rail_a_growth_tip', 'lamp', { noExport: true, parent: g, cast: false });
    g.visible = false; grow.push([g, body, tip]); }

  // ---- heat: a white-hot sun over the far end of the line + a slow rising shimmer over both lines (overlays, not exported to the lock)
  const glowTex = (() => { const c = document.createElement('canvas'); c.width = c.height = 256; const g = c.getContext('2d'), r = g.createRadialGradient(128, 128, 0, 128, 128, 128); r.addColorStop(0, 'rgba(255,255,250,1)'); r.addColorStop(.16, 'rgba(255,252,230,.97)'); r.addColorStop(.34, 'rgba(255,228,150,.45)'); r.addColorStop(1, 'rgba(255,200,120,0)'); g.fillStyle = r; g.fillRect(0, 0, 256, 256); return new THREE.CanvasTexture(c); })();
  const sun = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, transparent: true, depthWrite: false, fog: false, toneMapped: false })); sun.scale.set(70, 70, 1); sun.position.copy(B2T([30, 260, 120])); sun.name = 'sun_glow'; sun.userData.noExport = true; scene.add(sun);
  const shTex = (() => { const c = document.createElement('canvas'); c.width = 256; c.height = 128; const g = c.getContext('2d'); g.strokeStyle = 'rgba(255,246,228,.6)'; g.lineWidth = 2;
    for (let r = 0; r < 9; r++) { g.beginPath(); for (let x = 0; x <= 256; x += 4) { const y = 8 + r * 14 + Math.sin(x / 256 * Math.PI * 4 + r) * 4; x ? g.lineTo(x, y) : g.moveTo(x, y); } g.stroke(); } const tx = new THREE.CanvasTexture(c); tx.wrapS = tx.wrapT = THREE.RepeatWrapping; return tx; })();
  const shimmer = [];
  for (const cx of [-1.8, 1.8]) for (let y = 4; y < 70; y += 3.5) { const tx = shTex.clone(); tx.needsUpdate = true; tx.repeat.set(1.5, 1); const mt = new THREE.MeshBasicMaterial({ map: tx, transparent: true, opacity: 0, depthWrite: false, toneMapped: false, side: THREE.DoubleSide });
    const m = new THREE.Mesh(new THREE.PlaneGeometry(2.8, .55), mt); m.position.copy(B2T([cx, y, .62])); m.name = 'heat_shimmer'; m.userData.noExport = true; m.renderOrder = 5; scene.add(m); shimmer.push([m, rnd() * 6]); }

  // far side: telegraph poles every 15 m with two sagging wires (scale and depth down the line)
  const pole = '#5e4632', poles = [];
  for (let y = -12; y < 130; y += 15) { cyl('telegraph_pole', 'wood', .11, 6.2, [5.6, y, 0], pole, { r2: .09 }); box('telegraph_arm', 'wood', 1.2, .1, .1, [5.6, y, 5.7], pole); poles.push(y); }
  for (const ox of [-.45, .45]) for (let k = 0; k + 1 < poles.length; k++) { const a = poles[k], b = poles[k + 1], N = 8; for (let j = 0; j < N; j++) { const u0 = j / N, u1 = (j + 1) / N, z = u => 5.75 - Math.sin(Math.PI * u) * .45; const p0 = B2T([5.6 + ox, a + (b - a) * u0, z(u0)]), p1 = B2T([5.6 + ox, a + (b - a) * u1, z(u1)]); const len = p0.distanceTo(p1), m = new THREE.Mesh(new THREE.CylinderGeometry(.012, .012, len, 4), toon('#2c2a2a')); m.position.copy(p0).add(p1).multiplyScalar(.5); m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), p1.clone().sub(p0).normalize()); add(m, 'telegraph_wire', 'metal', { cast: false }); } }

  // a lineside hut (plank walls, framed door and window, a tin roof) and a mile post: scale cues off the camera arc
  const hutWood = ctx.relief('wood', '#b4603c', { scale: .35 });
  box('hut_wall', 'wood', 2.2, 2.0, 2.0, [-6.4, 7.5, 0], hutWood, { mat: 'wood_grain' }); box('hut_skirt', 'wood', 2.3, 2.1, .18, [-6.4, 7.5, 0], '#5e3d2a', { mat: 'wood_grain' });
  const roof = new THREE.Mesh(new THREE.ConeGeometry(1.95, .9, 4), toon('#6d7176')); roof.rotation.y = Math.PI / 4; roof.position.copy(B2T([-6.4, 7.5, 2.45])); add(roof, 'hut_roof', 'roof');
  box('hut_door_frame', 'wood', .07, .95, 1.62, [-5.27, 7.3, 0], '#e9dcc0'); box('hut_door', 'wood', .07, .8, 1.52, [-5.25, 7.3, 0], '#3e2f28'); box('hut_window_frame', 'wood', .06, .65, .55, [-5.28, 8.15, 1.05], '#e9dcc0'); box('hut_window', 'glass', .07, .55, .45, [-5.27, 8.15, 1.1], '#9fc8d8', { cast: false });
  box('mile_post', 'wood', .14, .14, 1.0, [-3.6, -1.6, 0], '#f1eadb'); box('mile_post_cap', 'wood', .2, .2, .06, [-3.6, -1.6, 1.0], '#c84a32');

  // trees (kit3d), placed off both lines; hills far away
  for (const [x, y, h, k] of [[-11, 16, 7.5, 'oak'], [-17, 44, 9, 'oak'], [12, 30, 8, 'oak'], [15, 68, 10, 'oak'], [-9, -9, 6.5, 'oak'], [9, 6, 6, 'olive'], [-24, 80, 9, 'oak']]) ctx.trees.tree({ kind: k, at: [x, y, 0], height: h, seed: Math.round(x * 7 + y) });
  for (let k = 0; k < 7; k++) { const h = new THREE.Mesh(new THREE.SphereGeometry(1, 20, 12), toon(k % 2 ? '#7f9e5a' : '#6f9255')); h.scale.set(40 + rnd() * 30, 12 + rnd() * 8, 18 + rnd() * 10); h.position.copy(B2T([-150 + k * 50, 190 + rnd() * 40, -6])); add(h, 'hill', 'ground', { cast: false }); }

  // meadow scatter: grass tufts and wildflowers in clusters, never on the ballast (|x| < 4) and never in a grid
  const tuftG = new THREE.ConeGeometry(.1, .38, 5), flG = new THREE.IcosahedronGeometry(.06, 0), tuftM = toon('#6f9a38'), flM = ['#f4e9c8', '#e9c23a', '#c9566b', '#f1f1f1'].map(c => toon(c)), sway = [];
  for (let k = 0; k < 360; k++) { const cx = (rnd() < .5 ? -1 : 1) * (4 + rnd() * 18), cy = -14 + rnd() * 90; for (let j = 0; j < 3; j++) { const m = new THREE.Mesh(tuftG, tuftM), s = .6 + rnd() * .9; m.scale.set(s, s * (1 + rnd() * .6), s); m.position.copy(B2T([cx + (rnd() - .5) * .6, cy + (rnd() - .5) * .6, .17 * s])); add(m, 'grass_tuft', 'foliage', { cast: false }); if (k % 9 === 0) sway.push([m, rnd() * 6]); } }
  for (let k = 0; k < 220; k++) { const m = new THREE.Mesh(flG, flM[k % 4]), x = (rnd() < .5 ? -1 : 1) * (3.8 + rnd() * 14), y = -10 + rnd() * 70; m.position.copy(B2T([x, y, .32 + rnd() * .12])); add(m, 'wildflower', 'foliage', { cast: false }); }

  ctx.sky.clouds({ kind: 'clear-day' });

  // word frames (script-timed now, the real voice later: the set follows words.json, never fixed frames)
  const fps = film.fps || 30, W = {};
  try { const ws = await (await fetch(ctx.dir + (film.words || 'voice/words.json'))).json(); for (const w of ws) { const k = w.w.replace(/[^a-z]/gi, '').toLowerCase(); if (!(k in W)) W[k] = [Math.round(w.s * fps), Math.round(w.e * fps)]; } } catch (e) { /* no words: nothing moves */ }
  const at = (k, d) => (W[k] ? W[k][0] : d), endOf = (k, d) => (W[k] ? W[k][1] : d);
  const fHeat = at('steel', 1e9), fPush = at('pushes', 1e9), fSnap = at('snaps', 1e9), fThe = at('the', 1e9), fRoom = endOf('gives', 1e9);
  const ease = u => (u <= 0 ? 0 : u >= 1 ? 1 : u * u * (3 - 2 * u));
  let kink = null;
  return {
    anchors: { joint: [-1.08, 0, .41], kink: [1.8, KY - 1, .41], line_b: [1.8, KY - 6, .4], meadow: [0, 25, 0], pole: [5.6, 18, 5.7] },
    update: (f, t) => {
      if (!kink) kink = scene.getObjectByName('kink');
      // the buckle: at rest -> shiver and bow from "pushes" -> thrown into the S on "snaps" (8 f, small overshoot) -> the registry asset holds the result
      let A = 0, jit = 0;
      if (f >= fPush && f < fSnap) { const u = (f - fPush) / Math.max(1, fSnap - fPush); A = .07 * u * u; jit = Math.sin(f * 2.7) * .014 * u; }
      else if (f >= fSnap) { const u = (f - fSnap) / 8; A = u < 1 ? .07 + (A_FULL * 1.07 - .07) * ease(u) : A_FULL * (1 + .07 * Math.max(0, 1 - (u - 1) * 2)); }
      const assetOn = f >= fSnap + 12; live.visible = !assetOn; if (kink) kink.visible = assetOn; if (!assetOn) poseLive(A, jit);
      // "room": the rail ends grow into the hero joint from "The" and stop 5.5 cm short at the end of "gives" (so the room is seen, held, on "room")
      const g = f < fThe ? 0 : ease((f - fThe) / Math.max(1, fRoom - fThe)) * .135;
      for (const [grp, body, tip] of grow) { grp.visible = g > .002; body.scale.z = Math.max(g, .001); body.position.z = g / 2; tip.position.z = g; tip.material.color.set(f < fRoom ? '#ff9a3c' : '#ffc27a'); }
      // heat shimmer rises from the word "Steel" on, faint and sun-white
      const hs = f < fHeat ? 0 : Math.min(1, (f - fHeat) / 20) * .32;
      for (const [m, ph] of shimmer) { m.material.opacity = hs * (.7 + .3 * Math.sin(t * 3 + ph)); m.material.map.offset.y = (t * .35 + ph) % 1; m.material.map.offset.x = Math.sin(t * 1.3 + ph) * .05; }
      for (const [m, ph] of sway) m.rotation.z = Math.sin(t * 2.2 + ph) * .08;      // secondary motion: the meadow breathes in the heat
    },
  };
}
