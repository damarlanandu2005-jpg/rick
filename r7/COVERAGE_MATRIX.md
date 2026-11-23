# Ricks Channel Coverage Test: classification matrix (prepared in R7, NOT run)

This is the frame for the coverage campaign that comes after R7-R9. R7 does not build any of the missing capabilities below; it only records how a representative Ricks video will be classified, and what the asset library already proves for each class.

## How a video is classified
1. Pick a representative Ricks-channel video (reference only, private; never copied).
2. Break it into beats the way the Ricks reference board does (`creative/reference_board.json`).
3. Give every beat ONE primary class (A-I below) and any secondary classes.
4. For each beat, mark every capability it needs as PROVEN / SUPPORTED BUT NOT NEWLY TESTED / NOT YET IMPLEMENTED / NOT YET TESTED (definitions at the end), using the evidence named in the table.
5. A video is "coverable" only when every beat's needs are PROVEN or SUPPORTED. Anything else becomes a gap ticket with the beat as its test case. A gap is never covered by inventing a new pipeline.

## Classes
| Class | What the beat is | Ricks machinery today | Library (R7) status |
|---|---|---|---|
| A character dialogue/action | one or two 2D puppet cards acting on words | R3 characters, poses, film.json acts, words timing | not an asset question (characters stay R3) |
| B simple prop interaction | a character next to or touching a prop | set placement (registry GLB via film.json or ctx.asset); held props = JS builders (film.json held3d) | GLB placement + anchors PROVEN; a character HOLDING a registry GLB NOT YET IMPLEMENTED |
| C object throw/flight | an object leaves a hand and flies | film.json flights -> flights_baked.json -> flights.js (kit object) | registry GLB as the flying object NOT YET IMPLEMENTED ("throwable" refused) |
| D multi-character interaction | two or more cards together (carry, hand-over) | held3d carry/box (JS builders), hand_at | not newly tested by R7 |
| E dense environment | a busy set (30+ prop kinds, 600+ objects) | kit sets, Blender dressing lists | many registry assets in one set NOT YET TESTED (R7 used 2 assets per film) |
| F mechanical interaction | moving parts (pump handle, wheels, doors) | per-set JS motion | moving parts of a registry GLB NOT YET IMPLEMENTED ("mechanical", "openable" refused) |
| G physics/simulation-heavy | cloth, fluid, destruction | optional Blender layers (phase2) | NOT YET IMPLEMENTED for library assets; out of R7 scope |
| H fast camera/action | fast moves, whip pans | film_plan camera, check_film video bands | not an asset question |
| I effects-heavy | sparks, glow, smoke, practical lights | film.json fx/moods, lamp bloom, card_shade lights[].anchor | lamp bloom on a registry GLB SUPPORTED (seen in R7 storyboards, no metric); light at an asset anchor SUPPORTED BUT NOT NEWLY TESTED |

## Status definitions
- PROVEN: an R1-R7 test exercises it on real code with a pass criterion (cite the test).
- SUPPORTED BUT NOT NEWLY TESTED: the existing Ricks kit does it and nothing in R7 changed it, but no R7 test measures it.
- NOT YET IMPLEMENTED: no code path exists (R7 refuses the capability name with the reason).
- NOT YET TESTED: a code path probably works but there is no evidence.
