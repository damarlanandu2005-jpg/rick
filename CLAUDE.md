# CLAUDE.md — quick start for every new Claude session

**GitHub is the persistent source of truth. Chat history is not.**
This file is the quick start; `docs/PROJECT_STATE.md` is the detailed handoff and history.
If this file and the repository disagree, **the repository is authoritative**: fix this file to match it.

## STARTUP PROTOCOL (do this first, every new chat)
1. Read `CLAUDE.md` (this file).
2. Read `docs/PROJECT_STATE.md`.
3. Run:
   ```bash
   git status
   git branch --show-current
   git log --oneline -10
   ```
4. Inspect the current production state if a production is active (its `creative/`, `film.json`, `creative/review_history.json`, `creative/JUDGE.json`).
5. Identify what is finished, what is blocked, what is next, and what needs owner approval.
6. Do NOT restart completed phases.
7. Do NOT rebuild existing infrastructure.
8. Do NOT invent a new architecture.
9. Continue from the current state.
10. Before substantial changes, say the intended next action in a line or two.
11. After the action, update `PROJECT_STATE` below and `docs/PROJECT_STATE.md`, and commit the change.

**"Continue the project."** means: run the protocol, answer with this short status, then keep working:
```text
PROJECT: / CURRENT BRANCH: / LAST COMPLETED: / CURRENT BLOCK: / LAST RESULT: / NEXT ACTION: / OWNER APPROVAL REQUIRED: YES/NO
```
Do not ask the owner to explain the project again.

> **Branch note.** These two files live on the working branch `prod-the-gap`, not on `main`. `main` is the untouched import of the RicksClips zips (`d26d845`) and is never modified without the owner. A new chat must check out `prod-the-gap`, or the owner must say which branch to use.

## PROJECT IDENTITY
An automated creative production system for short vertical videos (720×1280, 30 fps), built on the **RicksClips methodology** (the Ricks skill, agents and rule book in `ricks_reference/`). The locked production flow:

```text
REFERENCE → STORY → SCRIPT / WORDS → REFERENCE BOARD → PICTURE PLAN → LOOK BIBLE → CHARACTERS → ASSETS → film.json
→ PLAN BAKE → G1–G7 → THREE.JS STORYBOARD → WHOLE-FILM ANIMATIC → INDEPENDENT JUDGE (G8) → HUMAN APPROVAL → G9
→ LOCK → ONE EXPENSIVE FINAL RENDER → OPTIONAL MASKED BLENDER ENHANCEMENT → COMPOSITE → VISUAL QA → AUDIO → MUX → DELIVERY QA
```
This architecture is established, implemented (R1–R9) and frozen. Do not casually redesign it.

## RICKS METHODOLOGY
- Solve creative problems on paper first: script, reference board, picture plan and look bible come before any render.
- Use a reference only as the owner instructs. For example, "story only" means take nothing visual from it. The output is original artwork.
- The words (`voice/words.json`) drive timing; camera stations land on words.
- The reference board is the creative and QA answer key.
- Build cheap evidence first (three.js storyboard, then the full-rate animatic), then the independent judge (8.5 on every panel), then owner approval. The expensive final render comes last, once.
- Prefer measured evidence (`film_plan.py`, `check_film.py`, decoded QA) over assumptions.
- Keep lessons from failed films (`docs/PROJECT_STATE.md` → lessons).
- The owner is the final creative authority.
- **The judge is a feedback mechanism.** A FAIL is diagnosed, not a reason to abandon the project. Fix ordinary creative problems yourself. If a failure exposes a real system limitation, document it instead of patching the film forever.

## AUTONOMOUS CREATIVE DECISION RULE
**Claude decides, tests and moves on (no question to the owner):** camera distance, framing, object size, poses, caption timing, missing visual cues, transitions, contrast, environment detail, asset staging, cause/effect clarity, minor animation timing, ordinary visual cleanup, and new asset *versions* needed for those fixes.

**The owner decides:**
- final creative approval;
- a major story or premise change;
- a major character identity change;
- a major production direction change;
- abandoning a production;
- `assets.py approve-glb` / approved character registration (the governance gate before a production render can use an asset);
- `review.py new-version` (reopening an exhausted judge budget);
- `approval.py create`, the lock, and authorising the final render;
- final delivery.

Do not turn small decisions into questions. Stop only at a real owner gate.

## ENGINEERING GOVERNANCE (never bypass)
- Never lower the 8.5 judge threshold. Never write or edit a judge result yourself: the judge is a fresh-context agent and `review.py judge-record` computes PASS/FAIL.
- Never bypass gates. `--unapproved-test-run` and `--accept-layers` are for named test fixtures only, never for a real film.
- Never mutate an approved asset or overwrite a registered version: make a new version with `assets.py new-version id X.Y --from X.Z`. Old versions stay reproducible from their own builder file.
- No final render before G9 approval and the lock. `render.mjs` refuses without them, and that refusal stays.
- Never claim GPU rendering without measured proof (see the GPU rule).
- Never commit MP4s, frame sequences, caches, wheels (`*.whl` in the repo root are local installers), `out/` folders, `templates/vector2d_characters/views_golden/_last_run/`, or Colab/Kaggle workspace data. `.gitignore` covers `out/`.
- Do not build a second production engine; the Ricks tooling in `tools/` and `templates/` already does the job.

## CURRENT ARCHITECTURE (verified in code)
- **Three.js** (`templates/threejs_film/`: `film.js`, `render.mjs`, `look3d.mjs`, `asset_glb.js`, sets/) is the **final base picture**. It also renders the storyboard, animatic, lock export and visibility.
- **Blender** is the asset workshop (`tools/blender_workshop.py`, `library/assets/builders/*.py` → deterministic GLB) plus the **optional** masked enhancement layers (`tools/layers.py`; not in the default path).
- **Characters** are 2D Ricks puppets drawn as cards (`templates/vector2d_characters/`, `poses.mjs`, `puppets.mjs`), registered and governed by `tools/characters.py` (R3).
- **Assets** come from one registry, `library/assets/registry.json`, with lifecycle candidate → validated → approved → deprecated (`tools/assets.py`, R7). Capabilities are only `static_prop` and `anchor_target`.
- **Plan:** `film.json` is the one plan, baked by `tools/film_plan.py` (41 plan gates).
- **Gates:** creative gates G1–G7 are `tools/creative_gates.py`. Review is `tools/review.py`: storyboard, animatic, judge brief/record, at most one fix round, G8.
- **Approval:** `tools/approval.py` writes `approval.json` and signs the plan, words, picture plan, look bible, storyboard, animatic, reference board, bake, character sheets and asset versions. That is G9.
- **Lock:** `render.mjs --export-lock` + `tools/lock_stamp.py`.
- **Orchestrator:** `tools/pipeline.py`, stages `ORDER` + `DELIVERY`. It fails closed and resumes by re-running the same command.
- **Final picture and QA:** `tools/final_video.py` composites; visual QA is `tools/qa_hybrid.py` + `tools/check_film.py`.
- **Audio:** `tools/audio.py` (R8) validates, mixes, muxes (video copied) and runs decoded delivery QA. Voice prep is `tools/voice_prep.py`; `tools/fish_tts.py` needs a key plus internet.

## CURRENT VERIFIED STATUS (details and evidence: `docs/R9_FINAL_CERTIFICATION.md`)
| Item | Status |
|---|---|
| R1 gates, approval, frame semantics | PROVEN (r1: 27 + 33 PASS, re-run 2026-11-25 on `prod-the-gap`) |
| R2 storyboard / animatic / judge / G8 | PROVEN (r2 76/0 at R9) |
| R3 2D character production | PROVEN (r3 79/0, re-run 2026-11-25) |
| R4 Blender → GLB → registry → three.js | PROVEN (r4 61/0, re-run 2026-11-25) |
| R5 reference-driven shot "Hat Toss" | mechanics PROVEN (60/0); creative judge **FAIL**, preserved |
| R6 orchestrator + render gate | PROVEN (103/0) |
| R7 asset library and capabilities | PROVEN (96/0) |
| R8 audio layer | PROVEN for its scope (53/0). Ducking, LUFS gates and TTS are NOT IMPLEMENTED |
| R9 certification | PASS 47/0 on CPU. The full chain ran: reference → … → G8 → human approval → G9 → lock → final render → composite → visual QA → audio → mux → delivery QA, giving a decoded 720×1280 MP4 with synced AAC. The film was a **TEST_FIXTURE_ONLY** film (`production:false`). FROZEN |
| Final MP4 of a **real** (non-fixture) film | **NOT YET DONE**: no real production film has passed the complete creative process and reached a final production render |
| Three.js hardware-GPU path | NOT CERTIFIED (see RENDERING PATHS) |
| Optional Blender layers end to end in R6+ | NOT TESTED |
| Multi-take / flight films in a final render | SUPPORTED (plan, storyboard, animatic), NOT TESTED in a final render |
| Holding/throwing/moving registry GLBs, physics | NOT IMPLEMENTED |
| Registry | 16 entries. Owner-approved: `prop_rail_joint_gapped` 1.0 + 1.1, `prop_track_buckled` 1.0 + 1.1, `char_trackkeeper`; 4 older approved characters. Handcar, barrel and lantern are validated only |

## CURRENT REAL PRODUCTION: "The Gap" (railroad story-only test) — STOPPED AT JUDGE
- **Location:** `productions/railroad_gaps/episode/`; small evidence in `productions/railroad_gaps/evidence/`.
- **What it tested:** reference story only → original story, character (`char_trackkeeper`), assets, set (`sets/heat_line.js`) → storyboard → animatic → independent judge.
- **V1.0:** judge FAIL, min 4.0.
- **V1.1:** judge FAIL, min 4.5, max 6.5 (s03_end); Mara 7.0, both assets 6.0, last frame 4.5.
- **Review budget: EXHAUSTED.** 2 judged versions; only the owner can reopen with `review.py new-version`.
- **Status:** nothing locked, no `approval.json`, no final render, no audio. `production_test_report.md` is not written yet.
- **Classification:** a useful HARDER/STRESS test (ground-level, focus-critical hero object), not the basic engine benchmark. Lessons are in `docs/PROJECT_STATE.md`.

## NEXT PRODUCTION STRATEGY
Do not keep modifying the railroad film. The next real production is a **Level-1/2 benchmark**:
- about 5–10 s, one character, one environment, 1–2 LARGE props;
- an obvious central action and a visual transformation;
- 2–3 shots with clear cause → effect;
- no tiny ground-level hero object, no physics, no multi-character interaction, no dependence on focus control or advanced poses;
- the current CPU workspace, one expensive final render only after approval, the judge at 8.5 or more on every panel, and the owner as final creative authority.

Steps: (1) record the railroad test in `productions/railroad_gaps/production_test_report.md`; (2) start a new branch `prod/<name>`; (3) run the Level-1 benchmark. The engineering machinery (R1–R9) is finished; the next priority is a real Level-1 film, not more infrastructure.

Testing ladder (not a new engine): L1 simple successful short → L2 more complex action → L3 multiple props / environment complexity → L4 railway / ground-level / focus-critical → L5 physics-heavy.

**Benchmark success means all of these:**
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

Goal: **REFERENCE STORY → ORIGINAL ARTWORK → GOOD FILM → FINAL MP4**, not just an animatic.

## GITHUB WORKFLOW
- Always check `git status`, `git branch --show-current` and `git log --oneline -10` before changing anything.
- Never modify `main` casually.
- Production work goes on a dedicated branch. Existing convention: `prod-the-gap`; for new work use `prod/<short-name>`, branched from the current working tip so R1–R9 is included.
- Branch history: `main` (`d26d845`) → `ricks-2d-core` (R1–R7) → `r8-audio-integration` → `r9-final-certification` → `prod-the-gap`. Each one contains the previous.
- After a meaningful step: run the relevant tests, inspect the diff, then commit with the session attribution trailers and push. No streams of meaningless commits.
- **Commit:** code, config, creative plans, metadata, small evidence (JSON/MD, compressed contact sheets), docs.
- **Do not commit:** MP4s, frames, caches, wheels, `out/`.

## NOTEBOOK / COLAB STRATEGY
GitHub is the source of truth; Colab is a disposable executor. A notebook is a thin launcher (clone → detect environment → install → run `tools/pipeline.py` → QA → MP4), never the engine.

**Colab is NOT a proven path for the current gated production pipeline.**
- **What earlier Colab runs measured (all pre-R1, `phase*/colab_*.ipynb`):**
  - a Blender-first full-frame render (Route B);
  - Blender masked enhancement layers;
  - the three.js base, which fell back to CPU/software rendering there.
- **Route B is not the layer route.** It was a Blender-first full-frame render, not the Blender masked enhancement/layer technique.
- **Never certified on Colab:** the R1–R9 gated pipeline end to end; the existing notebooks are stale for it.
- **How to treat Colab:** an optional, experimental GPU environment, not the current production renderer.

**Next production:** keep using the current CPU workspace unless measurement on the real film shows rendering is actually the bottleneck. Do not add Colab, Kaggle or GPU plumbing just because a GPU is available. Revisit GPU integration only when a measured production workload shows it is necessary. Compute is not the current bottleneck; creative quality is.

## RENDERING PATHS (keep these separate; numbers from `docs/PRODUCTION_BLUEPRINT_LOCKED.md` §15 and `docs/IMPLEMENTATION.md`)
| Path | What it is | Status | Measured |
|---|---|---|---|
| **Three.js CPU / software** | the production base picture (the R9 certification was CPU-based) | **PROVEN / measured** | this container about 1.0 s/f (R9); local 2-CPU 1.75–1.93 s/f; Colab CPU (SwiftShader) 4.33–5.10 s/f |
| **Three.js hardware-GPU production path** | `render_gpu.mjs` (ANGLE) | **NOT CERTIFIED** | R9 container: Chromium = llvmpipe (software), refused as designed; Colab T4: SwiftShader, refused. Ricks' own RTX 2070 figure (0.55–0.9 s/f) is not ours |
| **Route B: Blender-first FULL-FRAME render** | the whole frame rendered in Blender (A/B experiment); NOT a layer pass | previously benchmarked (Colab T4), not the default | EEVEE, 720×1280, 175 f: mean 3.387 s/f, median 3.331, P90 3.801, GPU util mean 78.6 %, VRAM peak 1835 MiB; with compose about 4.3 s/f end to end |
| **Blender masked enhancement layers** | optional masked layer (glint, reflection…) composited over the three.js base | previously benchmarked (Colab T4); NOT TESTED end to end in R6+ | 0.67–0.77 s/f steady, 49.6–51.2 s cold first frame |
| **R1–R9 gated pipeline end to end on Colab** | — | **NOT CERTIFIED** | never run |
| **R1–R9 gated pipeline end to end, CPU workspace** | — | **CERTIFIED on a TEST_FIXTURE_ONLY film only** (R9) | 430-frame MP4, clean run 519.6 s |

No real production film has yet passed the complete creative process and reached a successful final production render.

## GPU RULE
GPU present ≠ GPU rendering. When a GPU is used, record:
- GPU model, driver and CUDA;
- the renderer/device string actually used (e.g. the ANGLE/WebGL renderer);
- utilisation and VRAM;
- s/frame (mean, median, P90) and total time.

A software fallback (SwiftShader, llvmpipe) is reported as CPU, never as GPU.

## AUTHORITATIVE FILES
- **Architecture:**
  - `docs/PRODUCTION_BLUEPRINT_LOCKED.md`: the locked architecture and owner decisions; it wins over older notes.
  - `docs/R9_FINAL_CERTIFICATION.md`: the verified status, coverage, limits and production requirements.
- **History and project state:**
  - `docs/IMPLEMENTATION.md`: what was built per phase and R step, with measurements.
  - `docs/PROJECT_STATE.md`: the detailed state and history (this handoff).
- **Registries:**
  - `library/assets/registry.json`: the one asset and character registry.
- **Ricks method:**
  - `ricks_reference/`: the Ricks method (SKILL, CB_RULES, agents/storyboard-judge.md, agents/studio-director.md, …).
  - `MANIFEST.md`: what was imported from the RicksClips zips. Its old "Blender renders" note is superseded, as the file itself says.
- **Per production (`<ep>/`):**
  - `film.json`;
  - `creative/` (SCRIPT, PICTURE_PLAN, LOOK_BIBLE, reference_board, characters, character_production, STORYBOARD, ANIMATIC, JUDGE, review_history);
  - `approval.json` and `out/lock/` once they exist.

## PROJECT_STATE
```text
PROJECT_STATUS: R1–R9 frozen and certified (fixture end-to-end MP4). First real production stress test complete (not passed).
CURRENT_BRANCH: prod-the-gap
CURRENT_PRODUCTION: productions/railroad_gaps/episode ("The Gap", railroad story-only test) — STOPPED
CURRENT_PRODUCTION_VERSION: V1.1 (storyboard/judge version 2)
CURRENT_STAGE: 4 judge (G8) — FAIL; review budget exhausted
LAST_COMPLETED_STAGE: independent judge v2 recorded (commit 39ce70a)
LAST_JUDGE_RESULT: FAIL, fix round 1, min 4.5 (s04_end), max 6.5 (s03_end), threshold 8.5
FINAL_RENDER_STATUS: NOT RENDERED (no approval.json, no lock)
AUDIO_STATUS: none for The Gap (no voice take, no SFX/music); R8 audio layer certified on the fixture only
GPU_STATUS: three.js hardware-GPU path NOT CERTIFIED; three.js CPU PROVEN; Route B (Blender-first full frame) and Blender masked layers only benchmarked pre-R1 on Colab; R1–R9 E2E on Colab NOT CERTIFIED; next film stays on the CPU workspace
REVIEW_BUDGET_STATUS: The Gap exhausted (2/2 judged); reopening needs owner review.py new-version
NEXT_RECOMMENDED_ACTION: write productions/railroad_gaps/production_test_report.md (record only), then start the Level-1 benchmark on a new branch prod/<name>
OWNER_ACTION_REQUIRED: YES — choose/approve the Level-1 benchmark story (or explicitly reopen The Gap with review.py new-version)
```
