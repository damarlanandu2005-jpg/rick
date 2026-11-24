# PROJECT STATE — detailed handoff and history

Quick start: `CLAUDE.md`. This file holds the detail behind it.
If anything here disagrees with the repository, **the repository wins**: update this file.
Last updated: 2026-11-25, on branch `prod-the-gap` (handoff commit `2b395e4`; rendering-path/Colab correction in the following commit).

---

## 1. History in one screen

| Step | What it produced | Where | Status |
|---|---|---|---|
| Import | the three RicksClips V1.1 zips (skill, character views, character sheets), untouched | `main` `d26d845` | source; never modified |
| Phases 1–8 | hybrid architecture experiments (flight bridge, layers, hybrid QA, Western integration, orchestration, Blender-first A/B, the complete Western Short, a railroad canyon 10 s test) | `phase*/`, `experiments/`, `docs/IMPLEMENTATION.md` | done; measurements in `IMPLEMENTATION.md` |
| Blueprint | the locked architecture and owner decisions (2026-11-23) | `docs/PRODUCTION_BLUEPRINT_LOCKED.md` | authoritative |
| R1 | creative gates, `approval.json`, frame semantics | `tools/creative_gates.py`, `approval.py`, `frames.py`, `r1/` | PROVEN |
| R2 | storyboard, whole-film rough + hook animatic, independent judge, one fix round, G8 | `tools/review.py`, `r2/` | PROVEN |
| R3 | 2D character production (registry, four views, cards, lock) | `tools/characters.py`, `r3/` | PROVEN |
| R4 | Blender workshop → GLB → registry → three.js seam | `tools/blender_workshop.py`, `glb.py`, `asset_glb.js`, `r4/` | PROVEN |
| R5 | reference-driven shot "The Hat Toss" | `r5/episode/` | mechanics PROVEN; creative judge FAIL (preserved) |
| R6 | thin orchestrator, machine-enforced render gate, synthetic fixture | `tools/pipeline.py`, `r6/` | PROVEN |
| R7 | reusable asset/capability library (lifecycle, versions, capabilities) | `tools/assets.py`, `r7/` | PROVEN |
| R8 | minimal production audio layer (validate, mix, mux, decoded delivery QA) | `tools/audio.py`, `r8/` | PROVEN for its scope |
| R9 | final certification and freeze (fixture film to a decoded MP4) | `r9/certify.py`, `docs/R9_FINAL_CERTIFICATION.md` | PASS 47/0, FROZEN |
| Production 1 | "The Gap": railroad story-only test, V1.0 → V1.1 | `productions/railroad_gaps/` | stopped at judge FAIL, budget exhausted |

**Branch chain:** `main` → `ricks-2d-core` (R1–R7, `1346fe2`) → `r8-audio-integration` (`3ccafff`) → `r9-final-certification` (`72939e2`) → `prod-the-gap` (current). Each branch contains the previous ones, and all are on `origin`.

## 2. Regression evidence
- **Counts at R9** (`docs/R9_FINAL_CERTIFICATION.md`): R1 gates 27, R1 frames 33, R2 76, R3 79, R4 61, R5 60, R6 103, R7 96, R8 53, R9 47. Every suite had 0 FAIL.
- **Re-run on 2026-11-25 on `prod-the-gap`**, after the production's registry and set additions: `r1/test_gates.py` 27/0, `r1/test_frames.py` 33/0, `r4/test_assets.py` 61/0, `r3/test_characters.py` 79/0. `assets.py check`: registry OK, 16 entries.
- **Not re-run since R9** (long runs): r2, r5, r6 (about 9 min), r7, r8, r9 (about 25 min). The production touched none of their code. It added registry entries, an episode set and builders.
- **How to run:** `python3 r1/test_gates.py`, `python3 r1/test_frames.py`, `python3 r2/test_review.py`, `python3 r3/test_characters.py`, `python3 r4/test_assets.py`, `python3 r5/test_reference.py`, `python3 r6/test_orchestrator.py`, `python3 r7/test_library.py`, `python3 r8/test_audio.py` (+ `r8/e2e_production.py`), `python3 r9/certify.py [dir]`.

## 3. Capability status (PROVEN / SUPPORTED / NOT TESTED / NOT IMPLEMENTED)
- **PROVEN:**
  - the whole gated chain on CPU (reference → story → script/words → reference board → picture plan → look bible → 2D characters → registry assets → film.json → plan bake → G1–G7 → three.js storyboard → animatic → independent judge → G8 → human approval → G9 → lock → final render → composite → visual QA → audio → mux → delivery QA) to a decoded 720×1280 / 30 fps MP4 with synchronized AAC, **on a TEST_FIXTURE_ONLY film** (`production:false`). The fixture is not a real production film: **no real production film has yet passed the complete creative process and reached a successful final production render**;
  - approval / lock / asset / audio safety, fail-closed (R9 safety matrix);
  - the Blender → GLB → registry → three.js chain;
  - the 2D character pipeline;
  - reproducible base render (seeded dust).
- **PROVEN in production 1 (up to the judge):**
  - a story-only reference → original script, character, two original Blender assets (+ v1.1 versions), an original set, a gated plan, the storyboard, the full-rate animatic, `check_film` 0 FAIL, and two fresh-context judge runs;
  - owner approvals of a character and four asset versions through the real registry commands.
- **SUPPORTED (storyboard/animatic level, not certified in a final render):** multi-take films with hard cuts (The Gap has one cut), flights.
- **NOT TESTED:**
  - the three.js hardware-GPU production path: **NOT CERTIFIED** (needs the GPU PC: `templates/threejs_film/GPU_RENDER.md`, ANGLE/D3D11; see §4a);
  - the optional Blender enhancement layers end to end in R6+;
  - the R1–R9 gated pipeline end to end on Colab: **NOT CERTIFIED**, never run (§4a);
  - dense scenes;
  - a final render of a **real** owner-approved film.
- **NOT IMPLEMENTED:**
  - holding, throwing or moving registry GLBs (capabilities are only `static_prop`, `anchor_target`);
  - physics (cloth, fluid, destruction, vehicles);
  - audio ducking and the LUFS/true-peak gates;
  - TTS in this environment (Fish TTS needs a key + internet; huggingface is blocked here);
  - per-station camera focus control in the plan (`film.js` honours `c.focus`, but `film_plan.py` never emits it);
  - card poses that point down or kneel at an object beside the character.

## 4. Environment facts (this cloud container)
- **Machine:** 2 vCPU, no GPU (`/dev/dri` absent). WebGL is llvmpipe/SwiftShader, so all three.js rendering here is CPU.
- **Measured times:**
  - three.js final-quality frame: about 1.0 s/frame at 720×1280 (R9);
  - storyboard (8 panels): about 9 s;
  - full-rate 300-frame animatic (`review.py animatic --step 1`, 540×960 preview): about 290–320 s;
  - `check_film` on the animatic: about 3 s;
  - character production build: 13–20 s;
  - asset build: under 0.1 s;
  - asset validate: 2–3.5 s.
- **Network:** PyPI and the Ubuntu archive are reachable; huggingface.co returns 403. No speech recognizer and no TTS, so words are script-timed and labelled as such.
- **Local files:** the `*.whl` files and `RicksClips_*.zip` in the repo root are local installers/sources. The wheels must never be committed.

## 4a. Rendering paths and Colab (corrected 2026-11-25; keep these separate)
Sources: `docs/PRODUCTION_BLUEPRINT_LOCKED.md` §15 (raw-evidence table) and `docs/IMPLEMENTATION.md` (Phases 1C, 5+6, A/B, 7).

| Path | What it is | Status | Measured (only what the repository records) |
|---|---|---|---|
| Three.js CPU / software | the production base picture; the R9 certification was CPU-based | **PROVEN / measured** | this container about 1.0 s/f (R9 final render 428.2 s for 430 f); local 2-CPU 1.75 / 1.83 / 1.93 s/f; Colab CPU (Chrome = SwiftShader) 4.33–4.35 s/f (Phases 5/6, 7), 4.52 / 4.78 / 5.10 s/f (A/B ranges) |
| Three.js hardware-GPU production path | `render_gpu.mjs` (ANGLE) | **NOT CERTIFIED** | R9 container: Chromium reports llvmpipe (software), `render_gpu.mjs` refuses (exit 2); Colab T4: SwiftShader, refused as designed. The 0.55–0.9 s/f figure in `GPU_RENDER.md` is Ricks' RTX 2070 SUPER on another scene: not ours |
| **Route B = Blender-first FULL-FRAME render** | the entire frame rendered in Blender (`experiments/blender_first_ab/`, A/B vs the hybrid). It is **not** the masked enhancement/layer path and must not be called a layer pass | previously benchmarked on Colab T4; verdict: viable but not clearly better, the hybrid stays default | Blender 5.2.4 EEVEE, 64 samples, 720×1280, 175 frames: first frame 41.9 s, mean 3.387 s/f, median 3.331, P90 3.801, total 592.8 s, GPU util mean 78.6 % (P90 98 %), VRAM peak 1835 MiB of 15360; plus CPU grade/compose 0.891 s/f and overlay about 0.1 s/f: about 4.3 s/f end to end |
| Blender masked enhancement layers | a separate hybrid technique: three.js is the base picture, Blender renders an optional masked layer (glint, reflection, bounce light, lit smoke…) composited over it (`tools/layers.py`) | previously benchmarked on Colab T4; optional, not in the default path; NOT TESTED end to end in R6+ | 0.67–0.77 s/f steady (Phase 3 generic path reproducing 1C: 0.774; Phases 5+6 Colab runs: 0.661 / 0.669; Phase 7: 0.76), 49.6–51.2 s cold first frame |
| R1–R9 gated pipeline end to end on Colab | — | **NOT CERTIFIED** (never run; the notebooks predate R1 and are stale) | — |
| R1–R9 gated pipeline end to end on the CPU workspace | — | **CERTIFIED on a TEST_FIXTURE_ONLY film only** (R9) | 430 frames, clean run 519.6 s, resume 78.8 s |

**Colab status.**
- Colab is **not a proven path** for the current gated production pipeline.
- What earlier Colab runs measured:
  - a Blender-first full-frame render (Route B);
  - Blender masked enhancement layers;
  - the three.js base, as CPU/software rendering.
- Route B was a Blender-first full-frame render, not the Blender masked enhancement/layer route.
- The current gated R1–R9 pipeline has not been certified end to end on Colab.
- Treat Colab as an optional, experimental GPU environment, not the current production renderer.
- Kaggle and the owner's local GPU: no evidence (blueprint §15: UNKNOWN).

**Note on the blueprint.** Blueprint §15 still says "Default: develop and QA on Colab; render farm Kaggle/local only after a GPU path is proven". That was the plan before R6–R9. All actual R6–R9 work and certification ran in the CPU workspace. Its evidence table is correct; this section records the current status.

**Decision for the next production.**
- Keep using the current CPU workspace unless measurement on the real film shows rendering is actually the bottleneck.
- Do not add Colab, Kaggle or GPU plumbing merely because GPU rendering is available. Revisit GPU integration only when a measured production workload shows it is necessary.
- The engineering machinery (R1–R9) is finished. Creative quality, not compute, is the current bottleneck, and the next priority is a real Level-1 production film.

## 5. Production 1 — "The Gap" (railroad story-only test)

### 5.1 Brief (owner, 2026-11-24)
- **Source:** a 65 s vertical reference video, used for **STORY ONLY**: nothing visual, no remake, no imitation of the creator.
- **Output:** 720×1280, 30 fps, exactly 300 frames, made with the existing R1–R9 system: no R10, no new engine, no gate changes.
- **Judge:** at least 8.5 on every panel, without comparing it to the reference.
- **Stop for the owner** when the judge passes; only then lock, render once, add audio and run QA.
- **Measurements and a final `production_test_report.md` were requested** (still to be written: §5.9).

### 5.2 Story and design (all original)
- **Story idea extracted:** railroads leave gaps because steel expands in heat; a gapless line has nowhere to go and buckles sideways.
- **Script (32 words):** "Why do railroads have gaps? Steel grows in summer heat. Track laid perfectly end to end has nowhere to go, so it pushes until it snaps sideways. The gap gives it room."
- **Words:** `voice/words.json` is script-timed (3.60 w/s, 0.15–9.05 s) and must be re-timed to a real voice take.
- **Character:** Mara, a track keeper, `char_trackkeeper` v1.0. It is cast sheet 16 (`templates/vector2d_characters/code/sheets/sheet16.mjs`), built only from the locked libraries (lady form, roadWorker outfit, ponytail, straw sun hat). Owner-approved.
- **Set:** `productions/railroad_gaps/episode/sets/heat_line.js`. A high-summer meadow with two lines side by side:
  - line A (ours) is older, darker steel with 19 cm cartoon joints;
  - line B (the perfect line) is bright continuous steel, with a live buckle that shivers and bows from "pushes" and throws into an S on "snaps";
  - the "room" growth fills our hero joint in the last shot;
  - sun, heat shimmer, tie plates, crib ballast, telegraph poles, hut, kit3d trees.
- **Assets (all owner-approved):**
  - `prop_rail_joint_gapped` 1.0 (8 cm gap) and **1.1** (19 cm gap, polished end faces, tie plates);
  - `prop_track_buckled` 1.0 and **1.1** (bright steel, dragged and twisted sleepers, ballast spill);
  - builders `library/assets/builders/*_v1_1.py`; the 1.0 builders are untouched.
- **Not reused on purpose:** `canyon_rail.js` and `prop_rail_handcar` were made in Phase 8 from this same reference.

### 5.3 Timeline
- **V1.0:** creative → assets → plan → storyboard → animatic → judge v1 FAIL.
- **V1.1:**
  - the owner directed autonomous creative fixing (“fix it yourself, stop only at real governance gates”);
  - new asset versions → set and film rework → owner approve-glb for both 1.1 versions;
  - storyboard v2 → animatic (three builds until `check_film` reached 0 FAIL) → judge v2 FAIL.
- **Commits:** `c8e2c87`, `510be10`, `2832c6d`, `5a25ff7`, `e96b06b`, `39ce70a`, then this documentation commit.

### 5.4 Judge results (fresh-context `storyboard-judge` + `studio-director`; full JSON in `productions/railroad_gaps/evidence/`)
| Panel | V1.0 (v1) | V1.1 (v2) |
|---|---|---|
| s01_start (hook) | 5.0 | 5.0 |
| s01_end | 5.0 | 5.5 |
| s02_start (heat wide) | 5.0 | 5.5 |
| s02_end | 4.5 | 5.5 |
| s03_start (buckle) | 6.0 | 6.0 |
| s03_end | 6.0 | 6.5 |
| s04_start (payoff) | 4.0 | 5.0 |
| s04_end | 4.5 | 4.5 |
| char_mara | 6.5 | 7.0 |
| asset_prop_rail_joint_gapped | 4.0 | 6.0 |
| asset_prop_track_buckled | 6.0 | 6.0 |
| **Result** | FAIL (min 4.0), studio BACK | FAIL (min 4.5), studio BACK |

- **`review_history.json`:** version 1, fix round 0, FAIL; version 2, fix round 1, FAIL. `MAX_JUDGED` = 2, so **the budget is exhausted**. `creative/JUDGE.json` now holds v2; the v1 detail is in `evidence/judge_v1_result.json`.
- **V1.1 improvements the judge credited:**
  - the sideways S reads at a glance;
  - the "down the other line" camera idea works;
  - Mara is on model with distinct expressions;
  - the gap asset rose from 4.0 to 6.0.
- **Remaining V1.1 failures (judge v2):**
  - the gap is blurred and low in the opening and last shots;
  - heat reads weakly: the "tired" face's zZ reads as sleepy, and the shimmer is barely visible or reads as ghost lines;
  - "steel grows" is never shown;
  - the "room" growth reads as a small orange glitch at the frame edge;
  - the lean_in pose is weak, and there is no shadow under her feet;
  - the environment is clean but generic (box sleepers, plain hut).

### 5.5 Other measured gate results (V1.1)
- **Plan (`film_plan.py`):** 0 FAIL / 2 WARN (one cut in 10 s; one word station not at rest).
- **G1–G7:** PASS.
- **`check_film` on the full-rate animatic:** 0 FAIL / 3 WARN (4 rests per 10 s, 1 cut, roll p99 2.1°/f), after two picture-motion fixes (`evidence/check_film_v1_1_animatic.md`).
- **Nothing else happened:** no `approval.json`, no lock, no final render, no voice take, no SFX or music.

### 5.6 Diagnosis: what the failures were
- **Ordinary creative mistakes (fixable inside the film):**
  - the shimmer drawn as faint lines (reads as artefacts);
  - the meme face "tired" (zZ = sleepy);
  - the growth too small and at the frame edge;
  - line A joints invisible in the wide shot.
- **System limits revealed (patching the film does not remove them):**
  1. **Focus:** the post DOF focuses on the nearest depth at the frame centre, and the plan has no per-station focus. A foreground ground-level hero object is blurred whenever the character is at the centre.
  2. **Gates vs ground-level hero:** the plan's framing gates (head centre 0.39–0.51, whole-body figure height and feet position, face share) push every rest toward a centred character. A 19 cm object on the ground ends up low in frame, blurred or behind the legs.
  3. **Pose library:** no pose kneels at or points down to an object beside the character. `kneel_work` with the rail in front reads as standing, and `lean_in` reads as a stiff lean.
  4. **Finish:** toon box sleepers, flat rails and a simple hut. The judge called it "clean but generic" in both rounds.
  5. **Asset capability:** registry GLBs are static (`mechanical` is NOT_IMPLEMENTED), so moving parts such as the live buckle and the rail growth had to be drawn as set geometry next to the asset.

### 5.7 Lessons (keep for future films)
- Ground-level hero objects are hard in this engine. Pick story objects that are large, at character height, or able to fill the centre of an insert.
- Focus follows the frame centre: the story object must sit where focus lands, or have its own shot.
- Important story objects must read at phone size. Check a 720×1280 frame, not a thumbnail.
- Deformation needs a visible build-up (anticipation → bow → throw). An instant swap reads as a glitch.
- Heat and other invisible causes need strong, unambiguous visual language. Faint overlays read as artefacts.
- Meme faces carry their own meaning (zZ = sleepy). Choose faces by what they read as, not by their names.
- The plan gates and `check_film` both measure the camera, and they can disagree:
  - `check_film` counts picture motion (washes, pose changes, near-ground parallax) that the plan sees as rest;
  - keep washes and pose changes inside camera moves, and keep the creep tiny on wide rests with a near foreground.
- Render the rough animatic at `--step 1` before `check_film`. The default step-3 rough creates false "cuts" in fast travels.
- The judge brief's `animatic_sha1` is the hash of `creative/ANIMATIC.json` (as `review.py` computes it), not of the MP4. Judges may flag this; it is expected.
- A static scratch contact sheet is not enough for owner approval of a framing: the moving animatic exposes what the stills hide.

### 5.8 Owner approvals log (production 1)
| When (IST) | What | Command record |
|---|---|---|
| 2026-11-24 22:28 | `char_trackkeeper` 1.0, `prop_rail_joint_gapped` 1.0, `prop_track_buckled` 1.0 | registry `approved_by` = owner chat approval |
| 2026-11-24 22:56 | owner directive: autonomous creative fixing; V1.1 authorised | (chat) |
| 2026-11-24 23:26 | `prop_rail_joint_gapped` 1.1, `prop_track_buckled` 1.1 | `assets.py approve-glb` |
| — | `approval.py create`, lock, final render | **never given / not reached** |

### 5.9 Open items for production 1
- Write `productions/railroad_gaps/production_test_report.md`. It was requested in the original brief, with sections Source; Source usage (STORY ONLY); Story extracted; Our compressed story; Our visual concept; Character; Environment; Assets; Shots; Judge; Final decision; Timing; Quality; Most important conclusion.
- Its conclusion should state: the engine turned a story-only reference into original, coherent artwork up to a judged animatic, but **not** to the 8.5 bar. The limiting factors are in §5.6.
- **Machine times available:**
  - storyboard ~9 s;
  - full-rate animatic ~290–320 s each (×5 builds over V1.0/V1.1);
  - `check_film` ~3 s;
  - judge agents ~2.5 min each;
  - asset build+validate ~3–5 s each.
- **Human (owner) actions:** 4 approval messages. Downloads/uploads: the source video only.
- **Reopening The Gap** needs the owner's `python3 tools/review.py new-version productions/railroad_gaps/episode --owner NAME --reason TEXT`. The current recommendation is **not** to reopen it, but to move to the Level-1 benchmark.

## 6. Next production strategy (owner decision recorded 2026-11-25)
- Do not keep patching The Gap. Next comes a **Level-1/2 benchmark** whose conditions suit the engine's current, proven capabilities:
  - 5–10 s, one character, one environment, one or two large props;
  - an obvious central action and transformation;
  - 2–3 shots with a clear cause → effect;
  - no tiny ground-level hero, no physics, no multi-character interaction, no dependence on focus control or ground-interaction poses;
  - the current CPU workspace (§4a), one expensive final render only after approval, the judge at 8.5 or more on every panel, and the owner as final creative authority.
- **Steps:**
  1. record the railroad test in `productions/railroad_gaps/production_test_report.md`;
  2. start a new branch `prod/<name>`;
  3. run the Level-1 benchmark.
- **Ladder:** L1 simple successful short → L2 more complex action → L3 multiple props/environment → L4 railway / ground-level / focus-critical (The Gap lives here) → L5 physics-heavy.
- **Success** = all twelve steps, ending in a real MP4:
  1. the story works;
  2. the original artwork works;
  3. the storyboard works;
  4. the animatic works;
  5. the judge gives 8.5 or more on every panel;
  6. the owner approves;
  7. the production locks;
  8. the final 720×1280 render completes;
  9. audio is added;
  10. the mux succeeds;
  11. delivery QA passes;
  12. a real MP4 exists.
- **The benchmark needs from the owner:**
  - the story or reference;
  - a voice take (or a TTS route that works outside this container), plus SFX/music files;
  - asset and character approvals at the governance gates;
  - the final creative approval before the lock.

## 7. Where things are
- **Production sources:** `productions/<name>/episode/`:
  - `film.json`;
  - `sets/`;
  - `voice/words.json` (+ `voice.wav` when it exists);
  - `creative/*`.
- **Generated output** (gitignored): `<ep>/out/`, i.e. plan bake, storyboard panels, animatic MP4s, lock, stills, final.
- **Small committed evidence:** `productions/railroad_gaps/evidence/` (judge v1/v2 results, `check_film` report, plan report, storyboard sheet).
- **Asset library:**
  - `library/assets/registry.json`;
  - builders in `library/assets/builders/`;
  - GLBs in `library/assets/glb/<id>/<ver>/`;
  - previews in `library/assets/previews/`;
  - character views in `library/characters/`.
- **Earlier evidence:** `r*/evidence`, `r*/MEASUREMENTS.md`, `phase*/evidence*`, `experiments/blender_first_ab/evidence_colab/`.
