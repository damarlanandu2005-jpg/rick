// HEAT LINE ("The Gap", first real production 2026-11-24): an ORIGINAL high-summer meadow with two railway lines side by side.
// Story only came from the reference; nothing here is taken from its look. Plan metres, Z up, Y away from the opening camera.
// Line A (ours, x = -1.8): 12 m rail lengths with an open joint between each; the hero joint at y = 0 is the registry asset
//   prop_rail_joint_gapped@1.0 (placed by film.json, name "joint"), so this set leaves y in [-3, 3] empty on line A.
// Line B (the "perfect" one, x = +1.8): one continuous rail, brighter steel. The 6 m centred on the kink asset's film.json position is straight until the word
//   "snaps", then that 6 m is swapped for the registry asset prop_track_buckled@1.0 (film.json name "kink") under a kick + dust.
// Rails are drawn toon in the assets' own colours on purpose (no PBR/toon seam where the set's rails meet the registry assets). Every mesh has a stable NAME and a ROLE / library material (the lock and the Blender layers read them). Same helpers as the kit sets.
export async function build(THREE, scene, film, ctx) {
  const { B2T, toon } = ctx, n = {};
  let seed = 11; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  const add = (m, name, role, o = {}) => { n[name] = (n[name] || 0) + 1; m.name = n[name] > 1 ? `${name}_${String(n[name]).padStart(2, '0')}` : name; m.userData.role = role; if (o.mat) m.userData.mat = o.mat; m.castShadow = o.cast ?? true; m.receiveShadow = true; (o.parent || scene).add(m); return m; };
  const box = (name, role, w, d, h, at, mat, o = {}) => { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), typeof mat === 'string' ? toon(mat) : mat); m.position.copy(B2T([at[0], at[1], at[2] + h / 2])); if (o.rot) m.rotation.y = o.rot; return add(m, name, role, o); };
  const cyl = (name, role, r, h, at, mat, o = {}) => { const m = new THREE.Mesh(new THREE.CylinderGeometry(o.r2 ?? r, r, h, o.seg ?? 12), typeof mat === 'string' ? toon(mat) : mat); m.position.copy(B2T([at[0], at[1], at[2] + h / 2])); return add(m, name, role, o); };

  // materials: real relief on the ground, real steel on the rails (kit3d), toon fallbacks when kit3d is off
  const grass = ctx.relief('grass', '#8db04a', { scale: 1.0 }), ballast = ctx.relief('cobble', '#9d9284', { scale: .09 }), wood = toon('#6b4a2e');
  const steelA = toon('#8c9197'), steelB = toon('#9aa0a6');   // the same steel colours as the two registry assets (the asset loader draws them with the film's toon material), so no seam at y = +-3 / 17 / 23; the perfect line is the brighter, newer steel
  const BED = .12, RAIL_H = .17, GAUGE = .72;
  const kinkAt = (((film.places || {}).meadow || {}).assets || []).find(a => a && a.name === 'kink'), KY = kinkAt ? kinkAt.at[1] : 20;   // where film.json puts the buckled 6 m (the straight stretch it replaces is centred there)

  // ground: one big meadow, a darker mown strip along the lines
  box('meadow', 'ground', 420, 420, .2, [0, 120, -.2], grass, { cast: false, mat: 'turf' });
  box('mown_strip', 'ground', 9, 160, .02, [0, 50, -.01], ctx.relief('grass', '#7d9f40', { scale: .7 }), { cast: false, mat: 'turf' });

  // two ballast beds (top at z = BED); the registry assets stand on it (film.json at z = 0.12)
  for (const [x, nm] of [[-1.8, 'ballast_a'], [1.8, 'ballast_b']]) {      // a heaped bed: sloped shoulders, not a wall
    const g = new THREE.BoxGeometry(3.6, BED, 170), P = g.attributes.position; for (let i = 0; i < P.count; i++) if (P.getY(i) > 0) P.setX(i, P.getX(i) * 2.85 / 3.6); g.computeVertexNormals();
    const m = new THREE.Mesh(g, ballast); m.position.copy(B2T([x, 45, BED / 2])); add(m, nm, 'ground', { cast: false, mat: 'gravel' });
  }

  // sleepers every 0.65 m (none where an asset stands)
  const sleepers = (cx, skip) => { for (let y = -40; y < 130; y += .65) { if (y > skip[0] && y < skip[1]) continue; box('sleeper', 'wood', 2.5, .24, BED, [cx, y, BED], wood, { cast: false, mat: 'wood_grain' }); } };
  sleepers(-1.8, [-3.1, 3.1]); sleepers(1.8, [KY - 3.1, KY + 3.1]);

  // line A: 12 m lengths with an open 7 cm joint between them (the hero joint at y = 0 is the asset)
  for (const sx of [-1, 1]) for (let y0 = 3; y0 < 130; y0 += 12) box('rail_a', 'metal', .07, 12 - .07, RAIL_H, [-1.8 + sx * GAUGE, y0 + 6, 2 * BED], steelA, { mat: 'metal' });
  for (const sx of [-1, 1]) for (let y1 = -3; y1 > -40; y1 -= 12) box('rail_a', 'metal', .07, 12 - .07, RAIL_H, [-1.8 + sx * GAUGE, y1 - 6, 2 * BED], steelA, { mat: 'metal' });
  // line B: continuous, brighter steel; [17, 23] is the stretch that buckles
  const straight = [];
  for (const sx of [-1, 1]) {
    box('rail_b', 'metal', .07, KY - 3 + 40, RAIL_H, [1.8 + sx * GAUGE, (KY - 3 - 40) / 2, 2 * BED], steelB, { mat: 'metal' });
    box('rail_b', 'metal', .07, 130 - (KY + 3), RAIL_H, [1.8 + sx * GAUGE, (130 + KY + 3) / 2, 2 * BED], steelB, { mat: 'metal' });
    straight.push(box('rail_b_before_buckle', 'metal', .07, 6, RAIL_H, [1.8 + sx * GAUGE, KY, 2 * BED], steelB, { mat: 'metal' }));
  }
  for (let y = KY - 2.8; y < KY + 3; y += .65) straight.push(box('sleeper_before_buckle', 'wood', 2.5, .24, BED, [1.8, y, BED], wood, { cast: false, mat: 'wood_grain' }));

  // far side: telegraph poles every 15 m with two sagging wires (scale and depth down the line)
  const pole = '#5e4632', poles = [];
  for (let y = -12; y < 130; y += 15) { cyl('telegraph_pole', 'wood', .11, 6.2, [5.6, y, 0], pole, { r2: .09 }); box('telegraph_arm', 'wood', 1.2, .1, .1, [5.6, y, 5.7], pole); poles.push(y); }
  for (const dx of [-.45, .45]) for (let k = 0; k + 1 < poles.length; k++) { const a = poles[k], b = poles[k + 1], N = 8; for (let j = 0; j < N; j++) { const u0 = j / N, u1 = (j + 1) / N, z = u => 5.75 - Math.sin(Math.PI * u) * .45; const p0 = new THREE.Vector3(...B2T([5.6 + dx, a + (b - a) * u0, z(u0)]).toArray()), p1 = new THREE.Vector3(...B2T([5.6 + dx, a + (b - a) * u1, z(u1)]).toArray()); const len = p0.distanceTo(p1), m = new THREE.Mesh(new THREE.CylinderGeometry(.012, .012, len, 4), toon('#2c2a2a')); m.position.copy(p0).add(p1).multiplyScalar(.5); m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), p1.clone().sub(p0).normalize()); add(m, 'telegraph_wire', 'metal', { cast: false }); } }

  // a little lineside hut and a mile post (scale cues near the hero joint, off the camera arc)
  box('hut_wall', 'wood', 2.2, 2.0, 2.0, [-6.4, 7.5, 0], ctx.relief('wood', '#b4603c', { scale: .6 }), { mat: 'wood_grain' });
  const roof = new THREE.Mesh(new THREE.ConeGeometry(1.85, .9, 4), toon('#4d3b33')); roof.rotation.y = Math.PI / 4; roof.position.copy(B2T([-6.4, 7.5, 2.45])); add(roof, 'hut_roof', 'roof');
  box('hut_door', 'wood', .05, .8, 1.5, [-5.28, 7.5, 0], '#3e2f28'); box('mile_post', 'wood', .14, .14, 1.0, [-3.6, -1.6, 0], '#f1eadb'); box('mile_post_cap', 'wood', .2, .2, .06, [-3.6, -1.6, 1.0], '#c84a32');

  // trees (kit3d), placed off both lines; hills far away
  for (const [x, y, h, k] of [[-11, 16, 7.5, 'oak'], [-17, 44, 9, 'oak'], [12, 30, 8, 'oak'], [15, 68, 10, 'oak'], [-9, -9, 6.5, 'oak'], [9, 6, 6, 'olive'], [-24, 80, 9, 'oak']]) ctx.trees.tree({ kind: k, at: [x, y, 0], height: h, seed: Math.round(x * 7 + y) });
  for (let k = 0; k < 7; k++) { const h = new THREE.Mesh(new THREE.SphereGeometry(1, 20, 12), toon(k % 2 ? '#7f9e5a' : '#6f9255')); h.scale.set(40 + rnd() * 30, 12 + rnd() * 8, 18 + rnd() * 10); h.position.copy(B2T([-150 + k * 50, 190 + rnd() * 40, -6])); add(h, 'hill', 'ground', { cast: false }); }

  // meadow scatter: grass tufts and wildflowers in clusters, never on the ballast (|x| < 4) and never in a grid
  const tuftG = new THREE.ConeGeometry(.1, .38, 5), flG = new THREE.IcosahedronGeometry(.06, 0), tuftM = toon('#6f9a38'), flM = ['#f4e9c8', '#e9c23a', '#c9566b', '#f1f1f1'].map(c => toon(c)), sway = [];
  for (let k = 0; k < 360; k++) { const cx = (rnd() < .5 ? -1 : 1) * (4 + rnd() * 18), cy = -14 + rnd() * 90; for (let j = 0; j < 3; j++) { const m = new THREE.Mesh(tuftG, tuftM), s = .6 + rnd() * .9; m.scale.set(s, s * (1 + rnd() * .6), s); m.position.copy(B2T([cx + (rnd() - .5) * .6, cy + (rnd() - .5) * .6, .17 * s])); add(m, 'grass_tuft', 'foliage', { cast: false }); if (k % 9 === 0) sway.push([m, rnd() * 6]); } }
  for (let k = 0; k < 220; k++) { const m = new THREE.Mesh(flG, flM[k % 4]), x = (rnd() < .5 ? -1 : 1) * (3.8 + rnd() * 14), y = -10 + rnd() * 70; m.position.copy(B2T([x, y, .32 + rnd() * .12])); add(m, 'wildflower', 'foliage', { cast: false }); }

  ctx.sky.clouds({ kind: 'clear-day' });

  // the buckle: straight until the word "snaps", then the asset (the kick and the dust in film.json cover the swap)
  let snapF = Infinity;
  try { const W = await (await fetch(ctx.dir + (film.words || 'voice/words.json'))).json(); const w = W.find(w => /^snaps/.test(w.w.trim().toLowerCase())); if (w) snapF = Math.round(w.s * (film.fps || 30)); } catch (e) { /* no words: stays straight */ }
  let kink = null;
  return {
    anchors: { joint: [-1.08, 0, .41], kink: [1.8, KY - 1, .41], line_b: [1.8, KY - 6, .4], meadow: [0, 25, 0], pole: [5.6, 18, 5.7] },
    update: (f, t) => {
      if (!kink) kink = scene.getObjectByName('kink');
      const after = f >= snapF; for (const m of straight) m.visible = !after; if (kink) kink.visible = after;
      for (const [m, ph] of sway) m.rotation.z = Math.sin(t * 2.2 + ph) * .08;      // secondary motion: the meadow breathes in the heat
    },
  };
}
