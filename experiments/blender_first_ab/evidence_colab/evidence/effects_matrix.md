# Effect matrix (separate from the A/B verdict)

Columns 2-3 are code facts read from the source (film.js, render.mjs, look.py, grade.py, from_lock.py). Column 5 is for the human judge, filled in after the blind judgement. Nothing here is scored by a pixel metric.

| effect | owner in Route A | owner in Route B | look for | observed (judge) |
|---|---|---|---|---|
| bloom | three.js post (film.js bloom pass) + in-scene lamp/sun bloom sprites | Blender EEVEE/look + grade.py CPU bloom (threshold 0.8) | highlights glow, not clipped haze |  |
| dust motes | three.js post (look_dust, 520 particles by day) | NOT in Blender or overlay (expected absent) | motes present/absent in a still-camera moment |  |
| vignette | three.js post (~0.7) | grade.py vignette fitted once per range (never per frame) | edge darkening, no flicker across the range |  |
| depth of field | three.js post: far set + near-lens soft, characters always crisp | Blender camera DOF f/5.6 focused on the subject card | non-subject characters: crisp (A) vs blurred (B)? |  |
| lens glints | JS overlay layer (lens glints) | JS overlay layer (render.mjs --overlay), same code | identical in both unless composited differently |  |
| flashes / 2D fx / bolts | JS drawFx in overlay() | JS overlay layer, same code | position and timing identical; edge quality over the graded picture |  |
| captions | JS overlay() | JS overlay layer, laid over AFTER the grade | legibility, no colour shift by the grade |  |
| held props | three.js props | Blender props (lock set glb, library materials by tag) | attached to the hand? occlusion by the card? |  |
| reflections | three.js env + Blender lamp_reflect layer (201-210 only) | Blender EEVEE screen-space raytracing | glass / lamp glints, in-focus objects only |  |
| shadows | three.js shadow maps | EEVEE shadows (PRESET sun, not the lock's sun) | contact shadows under characters; direction vs the base |  |
| character cards (sharpness) | three.js plane, sprite filtering | Blender plane, Cubic interpolation + film filter 2.2 px | 1:1 crops: edge softness, linework, halos |  |
| materials | three.js set materials | materials.py library by mat: tag (unknown -> matte) | wood / dirt / metal read as the same objects? |  |
| sky / haze / time-of-day | three.js sky + fog | look.apply_look preset 'day' (sky, key/fill sun, haze) | colour temperature, horizon |  |
| motion blur | none | OFF (Route B run with motion_blur=False: characters never blurred) | — |  |
| flight (coin) 316-330 | flights.js | lock_motion.apply on the set node, same baked flight | same arc, same frames, readable |  |
