// fulltest/cast_western.mjs -- GLUE: two characters for the Western street, taken from EXISTING cast sheet 05 (sheriff, outlaw)
// and only RECOLOURED (colour remap on the existing drawing code). Nothing is redrawn.
import { CAST } from '../templates/vector2d_characters/code/sheets/sheet05.mjs';
const byName = n => CAST.find(c => c.name === n);
// wrap every drawing function of a spec so that its svg strings get colours swapped
const rm = (map, v) => typeof v === 'string' ? v.replace(/#[0-9a-fA-F]{6}/g, c => map[c.toLowerCase()] || c) : Array.isArray(v) ? v.map(x => rm(map, x)) : v;
const wrap = (spec, map) => { const o = { ...spec }; for (const k of ['faceTop', 'hat', 'details', 'props', 'over', 'behind', 'headBack']) if (typeof spec[k] === 'function') o[k] = (...a) => rm(map, spec[k](...a)); return o; };
export const WESTERN = {
  // CALM: cream hat, moustache, brown vest over a teal shirt (sheriff body, dad form)
  calm: () => { const s = wrap(byName('sheriff'), { '#e9dcc0': '#efe3c2', '#2e2a33': '#8a5a34', '#e8e2d6': '#2fb5a8', '#5e5a66': '#d8c9a0', '#8a8590': '#cdbd90', '#b8a682': '#e6d7ac' });
    s.coat = '#8a5a34'; delete s.over; s.arms = undefined; return s; },
  // RED: red body + dark-red shirt strip (sheriff body), black hat from the outlaw, no moustache
  red: () => { const base = wrap(byName('sheriff'), { '#6e4527': '#a82028', '#5a4a3a': '#8d1f29', '#e8e2d6': '#b8282e', '#2e2a33': '#d8332e', '#5e5a66': '#e8c040', '#8a8590': '#e8c040', '#b8a682': '#e8c040' });
    const s = { ...base, hat: byName('outlaw').hat, coat: '#d8332e' }; delete s.over; delete s.faceTop; s.arms = undefined; s.face = undefined; return s; },
};
