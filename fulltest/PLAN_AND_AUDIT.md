> **HISTORICAL (superseded by `docs/PRODUCTION_BLUEPRINT_LOCKED.md`).** This Pass A path used its own intent/compile planning schema, a duplicate of `film.json`; `film.json` is the only production planning schema. Kept as evidence only. Its wording that the pipeline "never reads" the reference video is withdrawn: reference material is mandatory creative input before lock and an answer key afterwards, never a render-time dependency.

# Plan and audit: YouTube Shorts system on branch `ricks-2d-core`
Date 2026-11-21. Nothing in the pipeline was built or changed for this document. Every "checked" item was checked against files on the branch or the Ricks zips, not memory. Labels: MEASURED = run and timed; ESTIMATE = not run, a guess; UNVERIFIED = I did not check it.

## 1. What we are building
A repeatable factory: a short script (and later a voice) goes in; a 9:16 Short comes out.
- Characters: Ricks 2D vector puppets (code in `rig.mjs`, `castkit`, cast sheets). Drawn to PNG sequences by Node + Playwright.
- World: 3D Blender scenes built by bpy scripts (the Western kit in `kit/`). Puppets stand in them as flat cards (`from_lock.card`).
- Look: Ricks `look/` (materials, scatter, lights, grade). Render: EEVEE on Colab T4. Joining, grade, captions: FFmpeg.
- Pass A test = the first 14 s (11 shots) of "Why the Second Draw Always Wins", silent. The reference video is only an answer key to compare against, never read by the pipeline.

## 2. Who builds what
| Job | Who | Tool |
|---|---|---|
| Story, shot plan, camera intent, checks, fixing mistakes in the plan | Me (director) | JSON plan, validators |
| Puppet drawings and acting | Ricks code, run by Node | rig.mjs, castkit, moves |
| Sets, props, terrain, scatter, lights | Blender, following my bpy scripts | kit/, look/scatter |
| Camera moves | Blender, following the plan (blueprint says use `blender_cine`; I did NOT) | cine.py (unused) |
| Render | Blender EEVEE on Colab T4 | one notebook |
| Joining, dissolves, grade, captions, loudness | FFmpeg | post.py |
| Sound | not built yet (see 6) | |
Blender does not "make mistakes"; every miss so far was a missing or wrong instruction from me.

## 3. Flow (target)
script -> beat sheet + PICTURE_PLAN (one row per named thing) -> film.json (film_plan check 0 FAIL) -> asset list -> kit/set built per video -> pre-flight (pitfall checks, set_check, shotmath validate, all CPU, seconds) -> ONE Colab run: cards, Blender stills for a contact sheet, preview -> numbers report (frame_checks, density, cine_look) -> I look at one small sheet -> full render -> FFmpeg post -> sound -> QA.
The first gate in the lean pipeline (CB_RULES section 11) is: whole film rough + the hook moving, shown to CB together. Our Pass A is that gate for 14 s.

## 4. Audit: where I deviated from the saved blueprint (checked against files)
1. `film.json` plan format and `tools/film_plan.py check` (37 gates) not used. I invented `intent_passA.json` + `compile_intent.py` instead.
2. `templates/blender_cine/cine.py` camera rigs (chase, mount, orbit, catch, push, ballistic_path, bake_subject) not used. I wrote `fit_camera`/`shotmath` myself. This is why the bullet camera "went somewhere else".
3. `templates/pieces` (fly_and_hit, highlight_part, burst, time_pass) not used. The bullet was a per-shot screen streak with no entity, no stopping point, no muzzle flash.
4. No `PICTURE_PLAN.md` (section 11d: a row per word/thing, what we see, effect on the word). Gaps (muzzle flame, holster, straw, glint, sweat, red barn, RED in shot 8) were all knowable there.
5. Skipped the three.js rough-film stage and the lock (`--export-lock`). Blender was fed straight from my plan. Partial use of `from_lock.card` only.
6. `blender_look/tex` (19 files, 14.6 MB), `references/look_locked` (4 files), 80 of 180 `views_golden` PNGs, `tools/frame_checks` outputs, `rules/dept` (19) were left out of the branch by me, unchecked. `materials.get(image_name=...)` cannot work without `tex`. MANIFEST.md says views_golden is active but 80 files are missing. The kit used PIL-drawn textures instead (you asked for tile textures with colour correction: not done).
7. The 20 `library/pitfall` notes are not wired as pre-flight checks.
8. `check_film.py`, `check_episode.py`, `measure/cine_look.py`, `token_report.py` never run on our output.
9. No separate department/judge agents; I did everything in one thread (section 11 says small-model helpers for mechanical work; I have not been asked to spawn any).
10. `run_full` density-gate lines read a key that the JSON does not write (reporting bug; the kit itself met the gate: 48 kinds, 884 objects).
11. Intentional, not a deviation: the pipeline does not read the reference video; no Rick reference board for this test.
Note on blueprint conflicts: section 11 says "no Blender layer unless a hero object needs it" and "no still-picture judge loops". You decided Blender environments are the product, so I treat section 9 of the stage table as the rule for the look, and section 11 for process cost.

## 5. Professional tools to use instead of my own code
| Need | Use | Status |
|---|---|---|
| Camera follow of a flying object | cine.py `ballistic_path` + `chase`/`mount` | on branch, proven by Ricks |
| Glow, bloom, muzzle flash | Blender compositor Glare + emissive card + point light, or Ricks `fx` pieces | Blender feature; UNVERIFIED in our render |
| Depth of field, motion blur | Blender camera DOF, EEVEE motion blur (`cine.motion_blur`) | built in |
| Dust, smoke, sparks | Blender particle system / Geometry Nodes; Mantaflow only if needed (CPU/GPU heavy) | UNVERIFIED on Colab |
| Dissolves, captions, grade, loudness | FFmpeg (xfade, ass, loudnorm) | ffmpeg 6.1.1 present here; MEASURED OK in post.py |
| Textures | Ricks `blender_look/tex` tiles (need copying to branch); no CC0 packs, per your rule | not on branch yet |
| Voice | Ricks `tools/fish_tts.py` (Fish API, needs a key and network) | needs your key; UNVERIFIED |
| Sound effects | CB_RULES: real samples from your SFX library folder, never synthetic stand-ins | I do not have the folder: genuinely missing |
| Music | `templates/audio` (numpy/scipy synth, instruments, mix to -15 LUFS) exists but is a timeline written for another film | reusable engine, new timeline needed |
| Mix / loudness | `templates/audio/mix.py` + ffmpeg ebur128 | proven on the Bridge film |
Honest limit: sox, fluidsynth, espeak are not installed here; Colab can `apt install` them (ESTIMATE, not tested).

## 6. This machine (checked)
2 CPU cores, 7.8 GB RAM, no GPU, no Blender. ffmpeg 6.1.1, node 22, Python 3.13 (PIL, numpy, scipy, cv2, matplotlib, playwright). `bpy` 5.2.4 exists on PyPI (same version as Colab Blender). `pip install bpy` into a venv was refused by the permission classifier twice. With it I could run real Blender check renders here (casino chat measured Cycles about 18 s/frame at 360x640, EEVEE only on software GL). Without it, only fake-bpy logic tests run here, and real checks wait for Colab. Your decision: allow `pip install bpy` in an isolated venv, yes or no.

## 7. Time and usage
| Stage | Time | Label |
|---|---|---|
| Plan compile + validate + set_check | seconds, on CPU here | MEASURED |
| Colab round, Pass A (stills ~90 s incl. one-time setup, preview ~50 s) | 214 s wall | MEASURED |
| Final-quality render, 12-14 s | 11-12 min | ESTIMATE |
| Sound for 14 s (voice + SFX + music + mix) | not measured | UNVERIFIED |
| Context windows so far on Pass A | ~6, plus this audit | proxy; no token counter exists |
| Colab rounds so far | 5 | MEASURED |
Ricks reference: armor film 63.5 s cost 1.66 B tokens and 22.7 h; their target is 450 M and 12 h. Our target is to reach a good Pass A in at most 2 Colab rounds after the fixes below.

## 8. What was kept, thrown, used
- Kept and proven: multi-character cards, Western kit (48 kinds, 884 objects), dissolves, Ricks grade, usage meter, plan validators, no casino dependency.
- Thrown (when you say go): per-shot independent bullet streaks; `compile_intent` shot geometry for the bullet and camera; PIL-only ground/wall textures.
- Used from the zips: 419 of 851 files (49%) / 100 of 172 MB (58%) copied; about 13 files really executed (1,175 lines) plus what they import. Left out: 432 files / 71 MB (listed in section 4 item 6 and `threejs_film/_pbr_test`, `examples`, `references/reports`, Remotion bridge).

## 9. Fix order (only on your "go")
1. Copy `tex`, `look_locked`, missing 80 views, `frame_checks`, `rules/dept` onto the branch; kit uses tile textures with Ricks colour grade.
2. Re-plan Pass A in `film.json` with PICTURE_PLAN rows; film_plan check 0 FAIL.
3. Bullet as one object with `ballistic_path`; camera `chase`; stops at its target; muzzle flame, holster, straw, glint, sweat drop, red livery barn, RED in shot 8; fix shot-4 bullet size.
4. Wire pitfall notes as pre-flight; fix `run_full` density reporting; add start/end stills per camera move.
5. One Colab notebook, last cell prints numbers only.
6. Sound after you give the SFX folder and a Fish key (or choose another voice route).
## 10. Missing inputs (only these)
(a) permission for `pip install bpy` here, (b) your SFX sample folder, (c) Fish API key or another voice choice, (d) a yes/no on Opus vs Sonnet is your call; the plan above is the safeguard either way: the checks catch plan errors before a Colab round.
