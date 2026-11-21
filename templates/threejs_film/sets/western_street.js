// WESTERN STREET (hybrid Phase 5): the three.js reading of the kit recipe kit/recipes/western_noon.json (the SAME recipe the Blender kit builds from: street, landmarks, scatter,
// desert, motion). No second schema: film.json places.<name>.recipe names the recipe file kept in the episode folder (copied from the kit, a gate checks it is identical).
// Plan metres, Z up, Y down the street. Every mesh has a stable NAME (the lock objects the Blender layers select) and a ROLE / library material.
export async function build(THREE, scene, film, ctx) {
  const { B2T, toon } = ctx, pl = (film.places || {})[Object.keys(film.places || {}).find(k => (film.places[k].set || k) === 'western_street')] || {};
  const R = await (await fetch(ctx.dir + (pl.recipe || 'western_noon') + '.json')).json(); let seed = R.seed || 3; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  const n = {}, add = (m, name, role, o = {}) => { n[name] = (n[name] || 0) + 1; m.name = n[name] > 1 ? `${name}_${String(n[name]).padStart(2, '0')}` : name; m.userData.role = role; if (o.mat) m.userData.mat = o.mat; m.castShadow = o.cast !== false; m.receiveShadow = true; scene.add(m); return m; };
  const box = (name, role, w, d, h, at, col, o = {}) => { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), toon(col)); m.position.copy(B2T([at[0], at[1], at[2] + h / 2])); if (o.rot) m.rotation.y = o.rot; return add(m, name, role, o); };
  const cyl = (name, role, r, h, at, col, o = {}) => { const m = new THREE.Mesh(new THREE.CylinderGeometry(o.r2 ?? r, r, h, o.seg ?? 14), toon(col)); m.position.copy(B2T([at[0], at[1], at[2] + h / 2])); return add(m, name, role, o); };
  const W = R.half_width, S = R.street, L = R.landmarks, PAL = { saloon: '#a8613b', general: '#c9a56a', barber: '#9fb4c4', bank: '#c9c0a8', livery: '#8a5a3a', undertaker: '#5a4a52', hotel: '#d4b98a', jail: '#8c8478' };
  box('ground_far', 'ground', 400, 420, .2, [0, 110, -.16], '#d2b88a', { cast: false, mat: 'dirt' }); box('street_surface', 'ground', 2 * W + .2, 150, .03, [0, 60, -.02], '#c9a870', { cast: false, mat: 'dirt' });
  for (const sx of [-1.3, 1.3]) box('wheel_rut', 'ground', .45, 150, .02, [sx, 60, .0], '#a88a58', { cast: false });
  for (const [sd, key] of [[-1, 'styles_left'], [1, 'styles_right']]) {
    let y = S.y_start + (sd < 0 ? 0 : 1.5), i = 0;
    while (y < S.y_end) {
      const w = S.widths[(i + (sd < 0 ? 0 : 2)) % S.widths.length], st = S[key][i % S[key].length], h = 4.2 + (st === 'hotel' || st === 'bank' ? 1.6 : 0) + (i % 3) * .5, cx = sd * (W + 3.6), cy = y + w / 2, col = PAL[st] || '#b89a6a';
      box('building_' + st, 'wood', 7, w, h, [cx, cy, 0], col, { mat: 'wood_grain' }); box('false_front_' + st, 'wood', .35, w, h + 1.3, [sd * (W + .15), cy, 0], col, { mat: 'wood_grain' }); box('roof_' + st, 'roof', 7.2, w + .2, .25, [cx, cy, h], '#6b4a34');
      box('porch_roof_' + st, 'wood', 1.8, w, .15, [sd * (W - .9), cy, 2.9], '#6b4a34'); for (const k of [-w / 2 + .4, w / 2 - .4]) cyl('porch_post', 'wood', .07, 2.9, [sd * (W - 1.7), cy + k, 0], '#5a3d28');
      box('sign_' + st, 'wood', .08, w * .7, .7, [sd * (W - .02), cy, h + .35], '#e6d9b4', { mat: 'sign_flat' });
      for (let k = -w / 2 + 1.2; k < w / 2 - .8; k += 2.4) box('window_' + st, 'glass', .06, 1.0, 1.2, [sd * (W - .055), cy + k, 1.2], '#9fd0dc', { cast: false });   // on the street face of the false front (|x| = W - .025), not buried inside it
      y += w + S.gap[0] + rnd() * (S.gap[1] - S.gap[0]); i++;
    }
  }
  // landmarks: church, water tower (metal tank = a reflection target), windmill (blades turn), flag, wagons, wanted board
  box('church_body', 'plaster', 7, 9, 7, [0, L.church_y, 0], '#e8dfcc'); box('church_steeple', 'plaster', 2.4, 2.4, 6, [0, L.church_y - 3.2, 7], '#e8dfcc'); box('church_roof', 'roof', 7.4, 9.4, .3, [0, L.church_y, 7], '#7a4a34');
  const [tx, ty] = L.water_tower; for (const [a, b] of [[-1.6, -1.6], [1.6, -1.6], [-1.6, 1.6], [1.6, 1.6]]) cyl('water_tower_leg', 'wood', .14, 7, [tx + a, ty + b, 0], '#6b4a34');
  cyl('water_tower_tank', 'metal', 2.1, 3.0, [tx, ty, 7], '#7d8791', { mat: 'metal', seg: 24 }); cyl('water_tower_cap', 'metal', .1, .9, [tx, ty, 10], '#5b636b', { r2: 2.2, seg: 24 });
  const [wx, wy] = L.windmill; cyl('windmill_tower', 'metal', .25, 9, [wx, wy, 0], '#6b6f75', { r2: .7, mat: 'metal' }); const hub = cyl('windmill_hub', 'metal', .3, .5, [wx, wy - .4, 9.3], '#4a4f55', { mat: 'metal' }); hub.rotation.x = Math.PI / 2;
  const blades = new THREE.Group(); blades.position.copy(B2T([wx, wy - .7, 9.3])); blades.name = 'windmill_rotor'; blades.userData.noExport = true; scene.add(blades); const bl = [];
  for (let k = 0; k < 6; k++) { const b = new THREE.Mesh(new THREE.BoxGeometry(.5, 2.8, .05), toon('#b9bec4')); b.position.y = 1.7; const p = new THREE.Group(); p.rotation.z = k / 6 * Math.PI * 2; p.add(b); blades.add(p); b.name = 'windmill_blade'; b.userData.role = 'metal'; bl.push(b); }
  const [fx, fy] = L.flag; cyl('flag_pole', 'metal', .05, 6, [fx, fy, 0], '#d8d8d8', { mat: 'metal' }); const flag = box('flag_cloth', 'cloth', 1.6, .02, 1.0, [fx + .8, fy, 4.8], '#b3262e');
  for (const [x, y, r] of L.wagons) { box('wagon_bed', 'wood', 1.4, 3.0, .6, [x, y, .7], '#7a5a3e', { rot: r, mat: 'wood_grain' }); for (const sx of [-.8, .8]) for (const sy of [-1, 1]) { const w = new THREE.Mesh(new THREE.CylinderGeometry(.5, .5, .08, 16), toon('#4a3425')); w.rotation.z = Math.PI / 2; w.position.copy(B2T([x + sx, y + sy, .5])); add(w, 'wagon_wheel', 'wood'); } }
  box('wanted_board', 'wood', .1, 1.0, 1.4, [L.wanted_board[0], L.wanted_board[1], 1.0], '#e4d5ac', { mat: 'sign_flat' });
  for (let k = 0; k < R.street_props.hitch_posts; k++) { const sd = k % 2 ? 1 : -1, y = 9 + k * 10; cyl('hitch_post', 'wood', .07, 1.1, [sd * (W - 2.2), y, 0], '#6b4a34'); cyl('hitch_post', 'wood', .07, 1.1, [sd * (W - 2.2), y + 2, 0], '#6b4a34'); box('hitch_rail', 'wood', .08, 2.1, .08, [sd * (W - 2.2), y + 1, .95], '#6b4a34'); }
  for (let k = 0; k < R.street_props.troughs; k++) box('trough', 'wood', .7, 2.0, .5, [(k % 2 ? 1 : -1) * (W - 2.8), 15 + k * 14, 0], '#5a4a38', { mat: 'wood_grain' });
  // hero prop at the subject distance (IN FOCUS: a Blender reflection layer is only valid on in-focus objects, the base has its own DOF): a street lamp at the film's clock slot
  const cp = (film.props && film.props.clock && film.props.clock.pos) || [1.5, .6, 0];
  cyl('lamp_post', 'metal', .09, 2.1, cp, '#2b2d3a', { mat: 'painted_metal_chipped' }); cyl('lamp_foot', 'metal', .16, .14, cp, '#2b2d3a', { mat: 'painted_metal_chipped' }); box('lamp_neck', 'metal', .34, .34, .12, [cp[0], cp[1], 2.02], '#2b2d3a', { mat: 'painted_metal_chipped' });
  const ld = new THREE.Mesh(new THREE.CylinderGeometry(.3, .3, .5, 20), toon('#2b2d3a')); ld.position.copy(B2T([cp[0], cp[1], 2.5])); add(ld, 'lamp_drum', 'metal', { mat: 'painted_metal_chipped' });
  // ground scatter (recipe counts): tufts, pebbles, bushes in clusters, never on the wheel ruts (|x| < 2) and never in a grid
  const SC = R.scatter, tuftG = new THREE.ConeGeometry(.12, .4, 5), pebG = new THREE.DodecahedronGeometry(.07, 0), bushG = new THREE.SphereGeometry(.5, 8, 6), tuftM = toon('#a9a45a'), pebM = toon('#9a8466'), bushM = toon('#6f8a4a');
  const sc = (G, M, name, role, cnt, spread, hz, sz) => { for (let k = 0; k < cnt; k++) { const cl = k % 12 === 0, ax = (rnd() < .5 ? -1 : 1) * (2.4 + rnd() * spread), ay = 1 + rnd() * 100; const m = new THREE.Mesh(G, M); const sc_ = sz * (.6 + rnd() * .8); m.scale.set(sc_, sc_ * (1 + rnd() * .5), sc_); m.position.copy(B2T([ax, ay, hz * sc_])); add(m, name, role, { cast: false }); } };
  sc(tuftG, tuftM, 'grass_tuft', 'foliage', SC.tufts, 30, .2, 1); sc(pebG, pebM, 'pebble', 'stone', SC.pebbles, 12, .05, 1); sc(bushG, bushM, 'bush', 'foliage', SC.bushes, 40, .35, 1);
  // desert and far dressing (seeded, from the recipe counts)
  const D = R.desert; for (let k = 0; k < D.mesas; k++) { const a = -50 + k * 26, hh = 14 + rnd() * 10; box('mesa', 'stone', 20 + rnd() * 10, 14, hh, [a, 150 + rnd() * 25, 0], '#b5714a', { cast: false }); }
  for (let k = 0; k < D.saguaro; k++) { const x = (rnd() < .5 ? -1 : 1) * (14 + rnd() * 40), y = 10 + rnd() * 100; cyl('saguaro', 'foliage', .3, 3 + rnd() * 2, [x, y, 0], '#5d7f4a'); }
  for (let k = 0; k < D.rock_clusters; k++) { const x = (rnd() < .5 ? -1 : 1) * (10 + rnd() * 50), y = 8 + rnd() * 110; box('rock', 'stone', .8 + rnd(), .8 + rnd(), .5 + rnd() * .6, [x, y, 0], '#a08a6c', { rot: rnd() * 3, cast: false }); }
  for (let k = 0; k < D.dead_trees; k++) cyl('dead_tree', 'wood', .12, 2.6, [(rnd() < .5 ? -1 : 1) * (12 + rnd() * 25), 12 + rnd() * 80, 0], '#6a5a48');
  return { anchors: { windmill: [wx, wy, 9.3], water_tower: [tx, ty, 8.5], church: [0, L.church_y, 8] },
    update: (f, t) => { blades.rotation.z = -t * 1.4; flag.rotation.z = Math.sin(t * 3) * .08; } };
}
