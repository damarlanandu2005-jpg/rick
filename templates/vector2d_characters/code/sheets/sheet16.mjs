// SHEET 16 — PRODUCTION CAST (first real production, 2026-11-24). Built ONLY from the locked libraries: body form/size (bodies.mjs), outfit (outfits_300 'roadWorker'),
// hair (hair_lib 'ponytail'), hat (head_wear 'sunHat'). New characters are registered as CANDIDATES; the owner approves them (tools/characters.py register).
import { wear } from '../head_wear.mjs';
export const TITLE = 'Cast sheet 16: production cast';
export const CAST = [
  wear({ name: 'trackkeeper', label: 'Mara, track keeper', form: 'lady', size: 'standard', face: 'standard', outfit: 'roadWorker' }, 'ponytail', { hat: 'sunHat', hatCol: '#e7c26a', hatDrop: -34, hatScale: 0.92 }),
];
