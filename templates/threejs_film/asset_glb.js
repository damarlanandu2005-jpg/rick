// R4 SEAM: registry asset id -> approved GLB -> three.js group inside a set module. The ONLY asset loader of the kit.
//   Blender makes the asset (library/assets/builders/*.py, tools/blender_workshop.py) and exports the GLB; library/assets/registry.json owns its identity, version, hash and status;
//   tools/assets.py resolve copies the approved GLB into <episode>/out/assets/ and writes out/plan/assets_baked.json (id -> url, version, sha1, contract). This file only CONSUMES that.
//   A set module calls:  const car = await ctx.asset('prop_rail_handcar', { name: 'handcar', at: [0.0, 4, 0], rot: 90, scale: 1 });   (plan metres, Z up; rot = degrees about plan Z)
//   It returns { group, anchors: { grip_left: Vector3, ... } (group-local, the Ricks held-prop anchor shape), materials, bbox }.
// Fails CLOSED: an id that is not resolved for this film, not declared in film.json places.<place>.assets, or whose bytes do not hash to the resolved sha1, THROWS. There is no placeholder.
// Materials keep their GLB names (mat:<library name>[.rrggbb], the lock's convention); the base colour is read from the GLB and drawn with the film's own toon material (three.js owns the final look).
import { GLTFLoader } from './vendor/GLTFLoader.js';
const hex = b => [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, '0')).join('');
export function makeAssets(THREE, B2T, toon, dir, baked, scene, declared, stats) {
  const cache = new Map();
  const get = async id => {
    const e = baked && baked.assets && baked.assets[id];
    if (!e) throw new Error(`asset "${id}" is not resolved for this film (run tools/assets.py resolve; the registry entry must be approved)`);
    if (!declared.has(id)) throw new Error(`asset "${id}" is not declared in film.json places.<place>.assets`);
    if (cache.has(id)) return cache.get(id);
    const t0 = performance.now(), r = await fetch(dir + e.url); if (!r.ok) throw new Error(`asset "${id}": GLB missing (${e.url})`);
    const buf = await r.arrayBuffer(), t1 = performance.now(), h = hex(await crypto.subtle.digest('SHA-1', buf));
    if (h !== e.sha1) throw new Error(`asset "${id}": GLB hash ${h} is not the approved ${e.sha1}`);
    let gltf; try { gltf = await new GLTFLoader().parseAsync(buf, ''); } catch (x) { throw new Error(`asset "${id}": malformed GLB (${x.message})`); }
    stats.push({ id, bytes: buf.byteLength, fetch_ms: +(t1 - t0).toFixed(1), parse_ms: +(performance.now() - t1).toFixed(1) });
    cache.set(id, { e, gltf }); return cache.get(id);
  };
  return async (id, o = {}) => {
    const { e, gltf } = await get(id), g = gltf.scene.clone(true), inst = o.name || id, anchors = {}, mats = new Set(), want = new Set(Object.keys((e.contract && e.contract.anchors) || {}));
    g.updateMatrixWorld(true); const doomed = [];
    g.traverse(n => {
      if (want.has(n.name) && !n.isMesh) { anchors[n.name] = n.position.clone(); doomed.push(n); return; }
      if (!n.isMesh) return;
      const m = Array.isArray(n.material) ? n.material[0] : n.material, mn = m.name || '', lib = mn.startsWith('mat:') ? mn.slice(4).split('.')[0] : null;
      if (!lib) throw new Error(`asset "${id}": mesh "${n.name}" has no mat: material name (${JSON.stringify(mn)})`);
      const col = '#' + m.color.getHexString(), tm = toon(col); tm.name = mn; n.material = tm; n.userData.mat = lib; n.userData.role = (n.userData.role || (e.contract.roles && e.contract.roles[n.name]) || 'prop'); mats.add(mn);
      n.castShadow = o.cast ?? true; n.receiveShadow = true; n.name = `${inst}.${n.name}`;
    });
    for (const d of doomed) d.removeFromParent();
    for (const k of want) if (!anchors[k]) throw new Error(`asset "${id}": anchor "${k}" is missing in the GLB`);
    g.name = inst; g.position.copy(B2T(o.at || [0, 0, 0])); g.rotation.y = (o.rot || 0) * Math.PI / 180; g.scale.setScalar(o.scale ?? 1); g.userData.asset = { id, version: e.version, sha1: e.sha1 };
    if (o.add !== false) scene.add(g);
    g.updateMatrixWorld(true); const anchors_plan = {}; for (const k in anchors) { const w = anchors[k].clone().applyMatrix4(g.matrixWorld); anchors_plan[k] = [+w.x.toFixed(4), +(-w.z).toFixed(4), +w.y.toFixed(4)]; }   // world, back in plan metres (the inverse of B2T): what film.json anchors / held props use
    return { group: g, anchors, anchors_plan, materials: [...mats].sort(), bbox: new THREE.Box3().setFromObject(g) };
  };
}
