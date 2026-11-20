# fulltest: Pass A (0-14 s of the reference "Why the Second Draw Always Wins"), silent

Goal: prove the pipeline can stage a script, not just render one shot. Input is `script_passA.json` (11 shots: camera framing, characters, props).
The reference shot plan (`REF_SHOT_PLAN.md`) is the answer key only; the pipeline never reads the video.

## Run (Colab, T4)
Open `colab_fulltest.ipynb` (branch `ricks-2d-core`), Runtime > T4 GPU, Run all. Send back the output of step 9 (or `full_results.zip`).
It renders one still per shot first (contact sheet, about 1 min), then the 14 s preview (360x640, every 2nd frame, 16 samples).

## What runs
- `make_cards_multi.mjs`: existing Ricks rig + moves + cast sheet 05 outfits (recoloured in `cast_western.mjs`) -> PNG sequences per character.
- `street_kit.py`: the Western street, built in Blender from the existing `blender_look` materials/scatter/clouds (look preset `day`).
- `blender_full.py`: camera framing per shot (deterministic fitter: visible_frac / center_frac of the target's height, az/el, push), cards via the existing `from_lock.card()`, bullet and tumbleweed props, contact shadows, stills / preview render.
- `run_full.py`: the entry point (preflight, cards, Blender, ffmpeg, report). Errors start with `FULL_ERROR`; failed street decorations are listed as warnings, not fatal.

## Only edit to an existing Ricks file
`templates/motion_styles/rig.mjs`: 3 additive lines so a rig puppet can wear a cast spec (hat, moustache, outfit). Default behaviour is unchanged.

## Known gaps (documented, not hidden)
No audio or lip-sync; hard cuts only (the reference dissolves at 8 s); no revolver or aiming pose (RED uses the angry emote); no depth of field; props are simple. Blender steps were exercised only with a fake `bpy` here, so the first Colab run is the real test.

## Kit (since commit "real environment kit")
The set now comes from `kit/` (rules `KIT_SPEC.md`, parts `parts.py`, recipe `recipes/western_noon.json`, builder `build_set.py`, sign textures `textures.py`, pre-check `set_check.py`). The old thin `street_kit.py` is removed. The run report ends with a usage meter (measured seconds per step; Colab compute units are an assumed-rate estimate).
