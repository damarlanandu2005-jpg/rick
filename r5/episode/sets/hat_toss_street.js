// R5: THE HAT TOSS street = the kit's western_street set (reused unchanged) + the R4 barrel asset by registry id + the coin flight. No copy of the street, no copy of the barrel geometry.
import { build as base } from '/kit/sets/western_street.js';
import { addFlights } from '/kit/flights.js';
export async function build(THREE, scene, film, ctx) {
  const built = await base(THREE, scene, film, ctx);
  const lamps = []; scene.traverse(o => { if (o.name && o.name.startsWith('lamp_')) lamps.push(o); }); lamps.forEach(o => o.parent && o.parent.remove(o));   // fix round 1 (judge v1): the dark lamp post at the frame edge competed with the hero; this shot's street has none
  await ctx.asset('prop_saloon_barrel', { at: [-0.85, 0.35, 0], rot: 20, scale: 0.8 });   // Blender -> GLB -> registry -> here; scale cue and foreground depth beside the gambler (reference b1_a)
  return addFlights(THREE, scene, ctx, built);                                   // the coin (film.json flights[] -> baked -> mesh flight_coin)
}
