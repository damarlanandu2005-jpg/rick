// fulltest/moves/aim_gun.mjs -- NEW MOVE (glue for a missing pose): front-view puppet aims a revolver sideways at shoulder height, gritted teeth.
// Uses only existing rig parts: pose fields (view, feet, hands lx/ly, held svg, head, face) exactly as templates/motion_styles/moves/act_tool.mjs does.
import { track, blinkAt } from '../../templates/motion_styles/rig.mjs';
const sin = Math.sin, PI = Math.PI, INK = '#2a1a1f';
// revolver drawn AT the hand, barrel pointing +x (screen right)
const revolver = (x, y) => `<g transform="translate(${x - 18},${y - 10})"><path d="M0,-6 L150,-6 L150,10 L40,12 L0,26 L-10,10 Z" fill="#8d93a3" stroke="${INK}" stroke-width="6" stroke-linejoin="round"/><rect x="14" y="-20" width="38" height="30" rx="8" fill="#aeb4c2" stroke="${INK}" stroke-width="6"/><path d="M-10,12 L8,70 L40,64 L30,16 Z" fill="#6e4527" stroke="${INK}" stroke-width="6" stroke-linejoin="round"/><path d="M40,14 Q56,40 74,22" fill="none" stroke="${INK}" stroke-width="5"/><rect x="146" y="-10" width="10" height="12" fill="${INK}"/></g>`;
function aim(t, ch) {
  const tremble = 2.2 * sin(2 * PI * t * 7), lift = track([[0, 0], [.35, 1, 'out']], t);
  const hx = ch.sh[0] + ch.armL * .94, hy = ch.sh[1] + 12 - 10 * (1 - lift) * -1 + tremble;
  return { view: 'front', dir: 1, x: 0, y: 2 * sin(2 * PI * t / 1.4), rot: 0, feet: [{ x: -58 }, { x: 58 }], hands: [null, { lx: hx, ly: hy }], held: [{ hand: 1, svg: revolver }], head: -5 + 2 * sin(2 * PI * t * 3), face: 'k:angry', blink: blinkAt(t, 2.2, 1.0), cam: 0 };
}
export default { title: 'AIM GUN  ·  pick A', dur: 4, styles: [{ key: 'A', name: 'Aim sideways', blurb: 'arm out, revolver levelled, gritted teeth', pose: aim }] };
