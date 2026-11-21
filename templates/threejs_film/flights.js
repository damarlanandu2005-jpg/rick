// FLIGHTS (hybrid Phase 2). Plays out/plan/flights_baked.json: the plan (tools/film_plan.py bake_flights) evaluates every flight ONCE (leave frame, frames of flight,
// arc, from, to; a {char} target is led to where it is on the hit frame). This file does NO path maths: it only turns baked rows into a mesh position,
// the same way film.js plays camera_baked.json. A set module opts in with one line at the end of build():   return addFlights(THREE, scene, ctx, built);
// Each flight becomes a mesh named flight_<id> (so --export-lock writes its per-frame transform to motion/<place>.json, which the Blender side reads) and an
// anchor <id> (a function of the frame, so film.json fx / highlights can say on: "<id>"). Hidden = scale ~0 (not .visible), so the lock motion carries it too.
export function makeFlights(baked) {
  if (!baked) return null;
  const ids = Object.keys(baked), row = (id, f) => { const r = baked[id].frames; return r[Math.max(0, Math.min(r.length - 1, f))]; };
  return { ids, baked, at: (id, f) => { const r = row(id, f); return [r[1], r[2], r[3]]; }, visible: (id, f) => row(id, f)[4] === 1, info: id => ({ leave: baked[id].leave, hit: baked[id].hit, fly: baked[id].fly }) };
}
export function addFlights(THREE, scene, ctx, built = {}) {
  const F = ctx.flights; if (!F) return built;
  const meshes = {}, anchors = { ...(built.anchors || {}) };
  for (const id of F.ids) {
    const spec = (ctx.film.flights || []).find(x => x.id === id) || {}, m = new THREE.Mesh(new THREE.SphereGeometry(spec.r ?? .06, 16, 12), new THREE.MeshBasicMaterial({ color: spec.color || '#ff2fd6' }));
    m.name = 'flight_' + id; m.userData.role = 'metal'; m.castShadow = false; scene.add(m); meshes[id] = m; anchors[id] = f => F.at(id, f);
  }
  const prev = built.update, update = (f, t, R) => {
    if (prev) prev(f, t, R);
    for (const id of F.ids) { const m = meshes[id]; m.position.copy(ctx.B2T(F.at(id, f))); m.scale.setScalar(F.visible(id, f) ? 1 : 1e-5); }
  };
  update(0, 0); return { ...built, update, anchors };
}
