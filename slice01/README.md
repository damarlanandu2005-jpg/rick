# slice01: smallest vertical slice (2D Ricks puppet in the casino scene)

Goal: prove the chain end to end at LOW cost. No final render.

    existing Ricks rig + moves -> PNG frames (make_cards.mjs)
      -> existing blender_look/from_lock.py card() -> casino_eevee.blend
      -> Blender-native lights/materials/camera -> EEVEE 360x640 preview (12 s)
      -> ffmpeg mp4 + contact sheet + slice_report.md/json

## Run in Colab (T4)
1. Open `colab_slice01.ipynb` (branch `ricks-2d-core`), set runtime to T4 GPU.
2. Runtime > Run all. Steps 1-7 are the proven benchmark cells; step 0 clones the repo and places the blend; steps 8-10 are new.
3. Download `slice01_results.zip`: preview.mp4, contact_sheet.jpg, slice_report.md/json, logs, scene .blend, sample card PNGs.

## Files
- `config.json`: one test configuration (3 segments of 4 s: emo_think, emo_happy, emo_scared; preview resolution, stride, samples).
- `run_slice.py`: the single entry point (preflight, cards, Blender, ffmpeg, report). Failures print a clear message naming the missing dependency.
- `make_cards.mjs`: renders the existing puppet to a PNG sequence plus the `index.json` that `from_lock.card()` reads.
- `blender_slice.py`: the Blender glue (finds the character, places the card, lights, camera, EEVEE preview).
- `assets/casino_eevee.blend`: your casino scene, unmodified (the report checks it stays unchanged).

## Local check without Blender
`python3 run_slice.py --cards-only --out /tmp/s01` (needs Node and Playwright).

## Known limits
- A standing "standard" puppet replaces the seated 3D casino character.
- No lip-sync (no words.json), static camera, no contact shadow beyond the drawn foot shadow.
- Blender and Colab steps are UNTESTED; they were only exercised with a fake `bpy` locally. Timing numbers come from the first Colab run.
