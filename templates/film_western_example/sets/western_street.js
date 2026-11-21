// The kit's western street + the flights hook (same pattern as flight_platform.js: any set calls addFlights at the end of build()).
import { build as base } from '/kit/sets/western_street.js';
import { addFlights } from '/kit/flights.js';
export async function build(THREE, scene, film, ctx) { const built = (await base(THREE, scene, film, ctx)) || {}; return addFlights(THREE, scene, ctx, built); }
