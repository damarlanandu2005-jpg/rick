// CANYON RAIL (Phase 8 second-script test): a railroad cut through a striped canyon, a head-on train, then the track runs out onto a steel trestle over a deep blue void and on to the desert.
// Plan metres, Z up, Y away from the opening camera. The track runs along +Y at x = +-0.72 (sleepers across). Rail segment 'rail_gap' marks the sawn gaps (0.14 m, every 12 m near the start).
// Every mesh has a stable NAME and a ROLE / library material (the lock and the Blender layers read them). Same helpers as sets/platform.js, no new schema.
export function build(THREE, scene, film, ctx) {
  const { B2T, toon } = ctx, n = {};
  const add = (m, name, role, o = {}) => { n[name] = (n[name] || 0) + 1; m.name = n[name] > 1 ? `${name}_${String(n[name]).padStart(2, '0')}` : name; m.userData.role = role; if (o.mat) m.userData.mat = o.mat; m.castShadow = o.cast ?? true; m.receiveShadow = true; scene.add(m); return m; };
  const box = (name, role, w, d, h, at, col, o = {}) => { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), toon(col)); m.position.copy(B2T([at[0], at[1], at[2] + h / 2])); return add(m, name, role, o); };
  const cyl = (name, role, r, h, at, col, o = {}) => { const m = new THREE.Mesh(new THREE.CylinderGeometry(o.r2 ?? r, r, h, o.seg ?? 16), toon(col)); m.position.copy(B2T([at[0], at[1], at[2] + h / 2])); return add(m, name, role, o); };
  const STRIPE = ['#d9642b', '#b8442c', '#e08a3c', '#8e3a38', '#c9552d', '#e8a050'], E = 12;   // E = where the ground ends and the trestle begins
  // ground and track bed up to the canyon edge, then the far desert beyond the trestle (y 108+)
  box('ground_cut', 'ground', 30, E + 20, .3, [0, (E - 20) / 2, -.3], '#d97b43', { cast: false, mat: 'gravel' }); box('track_bed', 'ground', 3.4, E + 20, .22, [0, (E - 20) / 2, -.08], '#8a7a6c', { cast: false, mat: 'gravel' });
  box('ground_desert', 'ground', 300, 200, .3, [0, 210, -.3], '#e9b574', { cast: false, mat: 'dirt' });
  for (const x of [-.72, .72]) for (let y = -4, k = 0; y < E; y += 12, k++) { box('rail', 'metal', .1, 11.86, .14, [x, y + 5.93, .0], '#6a6f76', { mat: 'metal' }); }
  for (let y = -4; y < E; y += .62) box('sleeper', 'wood', 2.2, .22, .1, [0, y, -.05], '#6e4b32', { cast: false, mat: 'wood_grain' });
  // canyon walls: stacked layers of orange/red rock either side of the cut, taller and further apart toward the trestle
  for (const sd of [-1, 1]) for (let y = -6, i = 0; y < E + 70; y += 7, i++) { const x = sd * (6.5 + (y > 5 ? Math.min(y - 5, 14) * .5 : 0) + (i % 3) * .4), z0 = y > E - 4 ? -70 : 0; for (let z = z0, k = 0; z < 26; z += (z < 0 ? 7 : 3.2), k++) box('canyon_wall_' + (sd < 0 ? 'l' : 'r'), 'stone', 5 + (k % 2) * 1.2, 7.1, z < 0 ? 7.1 : 3.3, [x + sd * (k % 2) * .7, y, z], STRIPE[(i + k) % STRIPE.length], { cast: false }); }
  // the void under the trestle: a deep blue wall of air (a big dark plane far below) and the far canyon wall
  box('void_floor', 'water', 200, 140, .4, [0, E + 40, -70], '#2552d6', { cast: false, mat: 'matte' }); for (const sd of [-1, 1]) box('canyon_face_' + (sd < 0 ? 'l' : 'r'), 'stone', 4, 140, 70, [sd * 24, E + 40, -70], STRIPE[(sd + 3) % 6], { cast: false });
  // the steel trestle: deck on top of lattice towers, handrail posts, cross braces
  box('trestle_deck', 'metal', 3.4, 62, .3, [0, E + 31, -.4], '#8a9099', { mat: 'metal' }); for (const x of [-.72, .72]) box('trestle_rail', 'metal', .1, 62, .14, [x, E + 31, -.1], '#6a6f76', { mat: 'metal' });
  for (let y = E + 4; y < E + 60; y += 8) { for (const sx of [-1.4, 1.4]) cyl('trestle_leg', 'metal', .09, 68, [sx, y, -68.4], '#6a6f76', { mat: 'metal' }); for (let z = -66; z < -2; z += 8) box('trestle_brace', 'metal', 2.8, .08, .08, [0, y, z], '#6a6f76', { mat: 'metal' }); box('trestle_post', 'metal', .06, .06, 1.1, [1.5, y, -.1], '#4b4f56', { mat: 'metal' }); }
  // a loose plank sticking out over the void from the edge (where the engineer ends up)
  box('plank', 'wood', .5, 4, .1, [3.2, E + 2, -.35], '#8a6a46', { mat: 'wood_grain' });
  // the train: head-on, 6 m up the cut, with a headlight and a smoke pillar
  box('engine_body', 'metal', 2.3, 5.2, 2.6, [0, 9, .4], '#2f7a58', { mat: 'painted_metal_chipped' }); cyl('engine_boiler', 'metal', 1.0, 6, [0, 8, 1.6], '#3f8a66', { seg: 20 }).rotation.x = Math.PI / 2; cyl('engine_chimney', 'metal', .3, 1.6, [0, 7.2, 2.9], '#16161c', { r2: .5 });
  box('engine_headlight', 'lamp', .5, .15, .5, [0, 8.2, 2.2], '#fff2b0'); box('engine_cowcatcher', 'metal', 2.2, .9, .5, [0, 8.3, .2], '#2a2a30'); 
  return { anchors: { train: [0, 8, 1.2], trestle: [0, E + 20, -.2], edge: [0, E, 0], plank: [3.2, E + 2, 0] }, update: (f, t) => {} };
}
