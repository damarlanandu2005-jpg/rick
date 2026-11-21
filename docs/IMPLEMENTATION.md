# Implementation (what actually exists; updated per phase)
Branch `ricks-2d-core`. Phase 1C (`phase1c/`) is the frozen baseline: three.js base + one masked Blender layer at 720x1280 proved the seam; not modified.

## Phase 2: flight bridge (gate PASS, Colab T4 run, evidence in `phase2/evidence/`)
- **Reused:** film.json plan table, `film_plan.py` camera/follow bake, `fly_and_hit.js` timetable numbers, three.js `ctx`/set `update()`/anchors, lock export (`motion/<place>.json` already carried moving nodes).
- **Extended:** `film_plan.py` (`bake_flights`, `follow: "flight:<id>"`, 3 gates, writes `flights_baked.json`; `film_example` bake byte-identical); `render.mjs --export-lock` hashes and copies `flights_baked.json`; `from_lock.read` verifies every hashed file.
- **New:** `threejs_film/flights.js` (plays the baked rows), `blender_look/lock_motion.py` (lock motion -> Blender by lock_id, glTF axis rule), `templates/film_flight_example`, `phase2/*`.
- **Gates (all PASS):** plan/three.js/lock (7 mid positions, hit exact, fx on hit, registration <=1.4 px, lock fresh); Blender world==plan 0.0 m; projection vs three.js blob 0.49-0.70 px; alpha centroid vs projection <=0.2 px (2nd run); hit frame exact.
- **Limitation:** the coin is occluded by a character card on some frames in the base (reported as OCCLUDED, needs >=3 registered frames); only one flight shape (arc + stay/hide); Blender gate renders the flight object alone.
- **Run:** `python3 phase2/run_phase2.py --blender <blender> --out <dir>` (Colab: `phase2/colab_phase2.ipynb`).

## Phase 3: layers and assets
- **Plan:** `film.json "layers": [{id,type,place,objects[],frames[a,b],gain}]`, validated by a `layers` gate group in `film_plan.py`, baked to `out/plan/layers_baked.json` (frame range deterministic).
- **Blender:** `blender_look/layer_render.py`, one process per layer (layer + idmask + align). The mask is the named lock objects (must all exist, else the run stops). Only type `reflection` has a proven recipe (Phase 1C); other types are refused.
- **Orchestrator:** `tools/layers.py status|run`: refuses a stale lock, hashes inputs (spec, lock.json, place glb, scripts, resolution, base stills) -> cache hit or STALE; composites with `phase1b/compose_1b.py` (base + layer x alpha); gate = 1C thresholds (A outside mask 0, B <= +0.06, D <= 15 s/frame, E <= 0.5 px). C (visual) is a human review of `before_after_sheet.png`, never auto-passed.
- **Assets:** `library/assets/registry.json` + `tools/assets.py check` (name, category, source, version, dependencies, license, preview, Blender representation). 2 real entries: `flight_coin`, `platform_clock`.
- **Tests:** `phase3/test_layers_cpu.py` (CPU, no Blender): spec gate, deterministic bake, MISSING/FRESH/STALE/STALE-LOCK, named objects in the glb.
- **Not done / open:** three.js-owned character matte (characters are still Holdout cards in Blender; the card head offset seen in Phase 1 is undiagnosed); only the reflection type is gated.
- **Run:** `python3 phase3/run_phase3.py --blender <blender> --out <dir>` (Colab: `phase3/colab_phase3.ipynb`).

## Phase 3 result (Colab T4, gate PASS)
Generic path reproduced Phase 1C: A outside mask 0, B +0.0472 (<= 0.06), steady 0.774 s/frame (cold 51.2 s), layer edges vs base 0.03/0.05 px, second run cache hit (0.01 s), status FRESH, registry OK. C (visual) stays a manual look at `before_after_sheet.png`.

## Phase 4: hybrid QA (gate PASS, CPU)
- **Reused:** `film_plan.py check` (plan stage), `phase2/gate_flight.py`, `layers.py` status/hashes, `tools/check_film.py` (camera, plan-vs-picture, frozen/flicker, faces/captions; only on a full-film video because its plan numbers are whole-film), `tools/frame_checks/check.mjs` (optional `--frame-checks`, needs the GPU path).
- **New (the hybrid-only seams):** `tools/final_video.py` (base + every FRESH, PASSED layer -> `out/final/frames`, `final.mp4`, `final_manifest.json` with sha1 of every input), `tools/qa_hybrid.py` (5 stages: plan, three.js, blender, composite, video; reads the actual composite and decodes the actual mp4).
- **What the composite stage proves:** final frame == base + layer x alpha recomputed from the CURRENT inputs (hash-checked); outside every layer's named mask the final frame == the base; the decoded video frames equal the composite PNGs (PSNR >= 35 dB).
- **Tests:** `phase4/test_qa.py`: Q1 real flight range, Q2 layer range (synthetic layer: mechanism test), and six negative cases that must be caught (pixel outside mask, layer PNG changed after assembly, base still changed, flight changed after lock, video not the composite, blank base frame). All PASS.
- **Fixed on the way:** `gate_flight.py` treated a coin partly hidden behind a card as misregistered (centroid of the visible part); it now checks the visible pixels lie inside the expected disc (partial occlusion) and reports it.
- **Limitations:** `check_film.py` and `frame_checks` were not run on a hybrid full-film video yet (Phase 6 test Short); no audio checks (silent); the layer in the QA test is synthetic.
- **Run:** `python3 tools/final_video.py <ep> [--frames a-b]` then `python3 tools/qa_hybrid.py <ep>`.

## Phase 5: Western integration (CPU gate PASS; Blender layer gate pending Colab)
- **No separate architecture:** the Western is a place in a normal film.json. `templates/threejs_film/sets/western_street.js` reads the kit's own recipe (`kit/recipes/western_noon.json`, copied into the episode folder, a gate checks it is byte-identical) and builds the street, landmarks (church, water tower, windmill with turning blades, flag, wagons), hitch posts/troughs, desert and the recipe's ground scatter as named three.js meshes. Everything downstream (plan, lock, flights, layers, QA) is the same code as for the platform.
- **Extended:** `film.js` passes the episode folder URL to set modules (`ctx.dir`); `layer_render.py` / the layer test treat `name_02` / `name.001` as the same named object kind.
- **Episode:** `templates/film_western_example` (Ricks cast, coin flight, layer `window_glint` = reflection on the 8 `window_<style>` kinds, 21 windows in frame on frames 0-9).
- **Gate (`phase5/test_western_cpu.py`, all PASS):** recipe identical; plan 0 FAIL; base 720x1280 + lock; density 785 objects / 76 kinds (recipe: 600 / 30); layer objects exist in the lock glb; flight gates on the street; final video + QA PASS on the flight range.
- **Limitations:** the three.js street is a toon-box reading of the recipe, not the Blender kit's detailed geometry (porch details, signs with painted text, textures); Blender-built kit geometry is not exported to glb for three.js yet (a possible later step); the Blender window-glint layer has not been run yet (Colab).

## Phase 6: orchestration (CPU gate PASS)
- **`tools/pipeline.py <ep> [--frames a-b|all] [--blender B] [--renderer auto|cpu|gpu] [--accept-layers]`**: scripted stages (plan, base, lock, flight gate, layers, final, QA) are hash-cached and stop at the first FAIL; the creative steps are listed as INPUT/REVIEW and never executed by the script: the plan (`film.json`, incl. `layers[]`, `flights[]`) and the layer review (`out/layers/<id>/review.json {keep}`; a layer without keep=true is omitted from the final, `--accept-layers` writes a flagged auto-accept for test runs only).
- **Cache:** base stills and lock carry a key of every input (film.json, baked plan, kit/episode sets and renderer sources, resolution, renderer); a changed key re-renders the whole range.
- **Tests (`phase6/test_pipeline_cpu.py`, all PASS):** end-to-end first run (final.mp4 + QA PASS), second run cache hits (2.9 s), edited film.json invalidates the base, a failing stage stops the run, unreviewed layer omitted.
- **Measured locally (2 CPU):** base 2.06 s/frame at 720x1280; lock 31 s; QA 2.4 s.
- **Not done:** sound (silent), GPU base renderer (render_gpu.mjs) not yet measured on the T4, `check_film.py`/`frame_checks` not yet run on a hybrid full-film video.
- **Commands:** pipeline `python3 tools/pipeline.py templates/film_western_example --frames all --blender <blender> --accept-layers`; the Colab test Short `phase6/colab_phase6.ipynb`.

## Phase 5+6 first Colab run (T4): FAIL at stage 5, diagnosed and fixed (evidence: this note)
- P5 CPU gate PASS; pipeline stages 1-4 PASS; **stage 5 layers FAIL**: the `window_glint` layer rendered zero pixels, so the composite step crashed. Cause (mine): the `window_*` boxes sat INSIDE the false-front boxes, so they were invisible in three.js and Blender alike; my earlier CPU visibility check was projection-only (no occlusion) and did not catch it.
- **Fix:** windows moved onto the street face of the false front; new pre-check `layers.py visible` / pipeline stage `5a visible` (`render.mjs --object-visibility`, `window.objectVisibility` in film.js: 36x64 ray grid, occlusion counted) fails BEFORE any Blender time if a layer's named objects are not seen on every layer frame (>= 5 rays); `layers.evaluate` now fails with a clear message on an empty mask and returns the composite stderr. Tests: W5b (windows seen on frames 0-9: 20-31 rays) and W5c negative (water tower / windmill out of frame: 0 rays, caught).
- **GPU base renderer, measured:** `render_gpu.mjs` on Colab T4 reports SwiftShader (Chrome has no GPU) and stops as designed; the CPU fallback rendered 150 frames at 720x1280 in 649 s = **4.33 s/frame**. A real GPU path in Colab Chrome is NOT working; a 15 s Short costs about 33 min of base rendering on Colab CPU (about 15 min on a local 2-CPU machine at 1.8-2.1 s/frame).
