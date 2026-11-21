// The kit's platform set + the flights hook (hybrid Phase 2). Any set can do the same: call addFlights at the end of build().
import { build as base } from '/kit/sets/platform.js';
import { addFlights } from '/kit/flights.js';
export async function build(THREE, scene, film, ctx) { const built = (await base(THREE, scene, film, ctx)) || {}; return addFlights(THREE, scene, ctx, built); }
