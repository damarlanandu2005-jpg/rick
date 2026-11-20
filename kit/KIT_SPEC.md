# Kit spec: how a set is built (read this before adding a place)

A set is a recipe (`kit/recipes/<place>.json`) assembled from the parts library (`kit/parts.py`) by `kit/build_set.py`, inside Blender, by script. Nothing is downloaded or imported; textures that need drawing (signs, posters) are painted with PIL by `kit/textures.py`.

## Rules (from `ricks_reference/DENSITY_RULES.md`, the casino build, and the lessons of the first four Colab rounds)
1. **Density gate, measured:** 30+ kinds and 600+ objects per location, counted by `scatter.TALLY` and checked after the build (`DENSITY GATE` lines in the run report). Estimated before the build by `set_check.py`.
2. **Clusters, never lines:** big + medium + small (`cluster3`); scatter with `field`, never a grid.
3. **Hero objects have real detail:** frames, mullions, shutters, rails, doors, lanterns, signs with painted text. Every building style differs by something you can see.
4. **Layers:** foreground (verge scatter, props), midground (buildings, poles), background (landmarks: church, water tower, windmill), far (mesas, clouds, desert). Each third of the frame carries detail.
5. **Motion:** 2+ moving things (windmill blades, flag) driven by scripted-expression drivers, so no keyframe-API differences.
6. **Light and look:** Ricks `look.apply_look` and the locked material library; haze by distance; practical lights (lanterns) plus a key.
7. **Instance repeated props:** one mesh, many objects.
8. **Verify from the camera, not from the script** (casino lesson 2). Every textured face has UVs (lesson 3). Start exposure low when many things are emissive (lesson 1).
9. **Failures are reported, not hidden:** each build step is wrapped; the report lists failed steps.

## Adding a place
Write `recipes/<place>.json` (street, landmarks, scatter, desert, motion, density), add any new building styles to `parts.STYLES`, run `python3 kit/set_check.py <place>`. The director names the place in the intent spec (`"place": "<place>"`).

## Known limits (do not fake)
Only `western_noon` exists. No interiors, no dusk lighting recipe, no horses, no dust particles, no fire. Painted-sign text is drawn at build time with DejaVu fonts.
