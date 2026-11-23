# PRODUCTION BLUEPRINT — LOCKED (single source of truth)

Branch `ricks-2d-core`. Written 2026-11-23 from the forensic audit and a full read of the Ricks sources the audit had marked UNKNOWN (all 16 agent files, CB_RULES sections 0-11, `cine.py`, `GPU_RENDER.md`, the deleted translation spec in git history, the raw A/B timing files).

**STATUS: LOCKED (2026-11-23).** The owner approved D-1, D-2 (as corrected) and D-3 (section 22) and the documentation contradictions were resolved (section 30). Anything that conflicts with this blueprint must stop and be reported (section 21 rule 12). Changes follow section 23.

**Authority order when documents disagree:** (1) this blueprint; (2) `ricks_reference/CB_RULES.md` (newest rule wins inside it); (3) `ricks_reference/SKILL.md` "THE PIPELINE"; (4) everything else. `docs/RICKS_HYBRID_ARCHITECTURE_SPEC.md` (v2) and `docs/IMPLEMENTATION.md` are subordinate: v2 is the reasoning record, IMPLEMENTATION.md is the "what exists" log. `MANIFEST.md` is a file-origin list only and holds no architecture.

Labels used throughout: **A** = what Ricks does; **B** = what we agreed to change; **C** = what is implemented. UNKNOWN = evidence not present.

---
## 1. Mission
An automated production system for high-quality vertical Shorts in the Ricks Clips methodology: reference or idea in, approved and locked plan, one expensive render, a finished Short out. It minimises Claude coding, render rounds, GPU use, duplicated scene descriptions, asset rebuilding and architecture drift; it maximises Ricks visual quality, consistency, reuse and determinism. The creative methodology comes first; the machinery serves it.

**The architectural finding (confirmed against code and the Ricks rule file):** the project was never mainly missing a renderer. It is missing **enforcement of the Ricks creative front half** and the **Blender-asset-to-picture seam**. The back half (plan bake, lock, three.js base, composite, QA) is built, proven and kept. The back half is NOT the whole Ricks system and must never be described as such.

## 2. Non-negotiable principles
1. **Rule No. 1:** quality is judged against a reference, side by side, not by whether the code runs. Passing a gate never excuses a result below the reference.
2. **Hard Rule No. 2:** nothing generic passes; five specific details per main object.
3. **Creative decision is not compute execution.** Claude and agents decide, plan, review; machines render.
4. **Plan once, bake once, play everywhere:** `film.json` + `words.json` are the only plan; every renderer reads the baked files.
5. **Numbers before pictures:** a script measures what it can; a person or judge looks for what it cannot.
6. **Cheap before expensive:** nothing expensive runs before the approval gate (section 12).
7. **The lock is immutable;** changes after it require unlock and re-approval.
8. **Nothing is "proven" or "failed" without evidence;** an untested thing is UNPROVEN, a confounded experiment settles nothing.
9. **No silent change** to a Ricks rule, an agent, a gate threshold or this blueprint (section 21).

## 2a. Locked statements (owner-approved 2026-11-23; each is binding)
1. The Ricks reference-driven creative methodology is preserved.
2. **Reference material is mandatory creative input before lock and remains available as an answer key for QA; it is not a render-time dependency.**
3. three.js is the Ricks-approved final base picture. The hybrid is the default; full-frame Blender is not reopened without concrete evidence from a future production failure. The Blender-first A/B is supporting evidence only and is never used to justify deleting three.js, creating another renderer or rebuilding the Ricks three.js look.
4. Blender is the asset workshop plus an optional enhancement renderer. It is not mandatory for any shot and not the default final renderer.
5. 2D characters (Ricks vector puppets as cards) remain the channel architecture; 3D environments, props and effects; no 3D characters now.
6. `film.json` is the only production planning schema.
7. `camera_baked.json` is the authoritative camera result (`film.json` -> `film_plan.py` -> `camera_baked.json` -> LOCK -> three.js and Blender). three.js camera must equal Blender camera; no Blender script invents camera coordinates; if `cine.py` is integrated it feeds the bake and never competes with it.
8. Baked timing is authoritative (`words.json` + `film.json` -> baked timing). Character acting, camera, flights, fx, sound events, cuts and Blender enhancement timing all consume it; no downstream tool invents independent timing.
9. GLB is the approved asset interchange seam (section 8).
10. `approval.json` is a hard gate on every expensive render (section 19).
11. The judge is independent (section 14).
12. 720x1280 at 30 fps is locked; any change is class E.
13. The `--frames` bug is fixed before production (section 19; R1).
14. No speculative architecture is built: R1-R9 are incremental, one phase at a time, started only on the owner's explicit "GO R<n>".

## 3. What Ricks actually is (A)
A methodology and a quality system with an execution layer. Its order (`WORKFLOW.md`, SKILL.md "THE PIPELINE", CB_RULES 11a "lean pipeline"): topic and facts; script; voice and `words.json`; reference board (2-4 reference frames per beat, hard gate); PICTURE_PLAN (a row for every named thing); `film.json` with camera idea, stations, acts, fx, moods, sound cues; simple sets and storyboard; **the one gate: whole film rough in three.js plus the hook moving, shown with the picture plan and line check**; build-out by stretch from one shared sets folder; lock; (look pass); final render; sound; grade; captions, QA, proof page, delivery.

**Ricks' own newest rules already match our hybrid (resolves the biggest contradiction):**
- CB_RULES §3 "BLENDER = ONLY THE LAYERS IT DOES BETTER" (2026-11-13): the coded three.js frame is the FINAL BASE; a full Blender frame is no longer the final picture; Blender renders only masked layers from the lock camera, composited over the coded frame; each layer needs a before/after and is kept only if it clearly adds.
- CB_RULES §11a (2026-11-15): "A Blender layer" is NOT in the default pipeline any more (it cost about 80 M tokens and 6 h for a gain hard to see on a phone); use it only when a polished, glass or wet hero object is the star; only where the improved thing covers at least 1.5 % of the picture (§10).
- `WORKFLOW.md` step 9 and the `3d-designer` / `look-finisher` agents still describe the older Blender look pass. They are older; under Ricks' own precedence rule (newest wins) they are superseded for the final picture.

**Consequence:** our hybrid is not mainly a deviation we introduced; it is Ricks' own newest architecture. Earlier statements (audit Part 13, v2 §9) that we "replaced the Blender look pass on A/B evidence" overstate our authorship; the replacement was already Ricks' rule, and the A/B result is supporting, not deciding, evidence.

## 4. What we changed (B) and what we did not
| Item | Ricks | Ours | Basis |
|---|---|---|---|
| Final picture | three.js coded frame (newest rule) | same | Ricks CB_RULES §3 |
| Blender | masked layers, optional | same; asset workshop added (§8) | Ricks + user decision |
| Resolution / fps | 1440x2560 | **720x1280, 30 fps** | user decision (cost); a Ricks deviation (class G, approved) |
| Render machine | local RTX 2070, RunPod 4090 | Colab T4 / Kaggle T4 / local GPU | environment; GPU paths proven only where listed in §15 |
| Characters | 2D puppets | same, no 3D characters | unchanged |
| Reference board | required, hard gate | restored (§12.1): reference is a creative input before lock and a QA answer key after; never a render-time dependency | D-2 (corrected) |
| Judge / gate | judge 8.5; one human gate | reconciled in §14 | D-1 (approved) |
| Sound | stage 11 | after the visual lock; `words.json` timing is NOT optional (§17) | Ricks |
| Remotion, OneDrive, PC plumbing | present | not carried | environment |
| Flight bridge, layers/composite/final-video/QA hybrid tools, hash cache | none | added | proven (§6) |

## 5. The 20-stage table (A vs C)
Status words: COMPLETE/PROVEN, COMPLETE, PARTIAL, NOT IMPLEMENTED, UNKNOWN.

| # | Stage | Original Ricks | Purpose | Required | Current implementation (C) | Status |
|---|---|---|---|---|---|---|
| 1 | Story | 3 pitches, places 5-8, 2-3 lights; CB picks | true mock-and-twist story | yes | none (Claude by hand; canyon text copied by OCR) | NOT IMPLEMENTED as a stage |
| 2 | Script | writer: SCRIPT.md, beats, `script_stats.py` | action hook, one idea per line | yes | templates only; `tools/measure/script_stats.py` exists, never run | PARTIAL |
| 3 | Voice / words | Fish TTS, `words.json`, 3.5-4.5 w/s | time anchor for everything | yes | `words.json` hand/OCR for 2 films; `fish_tts.py`, `voice_prep.py` never run | PARTIAL |
| 4 | Reference examples | rick-researcher, 2-4 frames per beat | parity floor | yes, hard gate | none | NOT IMPLEMENTED |
| 5 | Reference board | `refs/REFERENCE_BOARD.md` + department index | measuring stick for every judge | yes | none | NOT IMPLEMENTED |
| 6 | Picture plan | `PICTURE_PLAN.md`, row per named thing | solve before build | yes | template only | NOT IMPLEMENTED |
| 7 | Look bible | `LOOK_BIBLE.md` | palette, light per chapter, grade | yes | template only | NOT IMPLEMENTED |
| 8 | Characters | character-artist: cast from 150, views, check_views | right role at first sight | yes | puppet kit works; casting stage not run; canyon borrowed stationmaster | PARTIAL |
| 9 | Blender assets | props-hero/3d-designer: hero object alone, BlenderKit, glb | detail | yes | `kit/` (Western only) builds in Blender; not exported to the picture | PARTIAL, isolated |
| 10 | three.js set | set-builder: dense module, 30+ kinds/600+ objects | the world | yes | 3 sets (129 lines total); Western reads the kit recipe | PARTIAL |
| 11 | Storyboard | START/END panel per camera move | cheap look at framing | yes | Ricks tool exists (`render.mjs --storyboard`), not run on our films | PARTIAL (tool only) |
| 12 | Storyboard judge | independent, 0-10, 8.5 | independent review | yes | none | NOT IMPLEMENTED |
| 13 | Animatic | whole film rough + hook moving | the one gate | yes | produced by `pipeline.py` base stage, but only after render, no gate | PARTIAL |
| 14 | Human approval | CB at the gate | final creative authority | yes | `review.json` for layers only | NOT IMPLEMENTED for the picture |
| 15 | Lock | `--export-lock` | freeze | yes | works, hashed | COMPLETE/PROVEN |
| 16 | Blender look / enhancement | look pass (old) / masked layers (newest) | polish a hero object | optional | `lamp_reflect` PASS, `window_glint` FAIL | PARTIAL (optional) |
| 17 | Final rendering | local GPU three.js (0.55-0.9 s/f at 1080x1920, Ricks) | frames | yes | CPU three.js 1.8-4.4 s/f at 720x1280; Colab GPU path blocked | COMPLETE (CPU) |
| 18 | Sound | sound-designer from `sound_events.json` | SFX, ambience, music | yes | baked cue file only | NOT IMPLEMENTED |
| 19 | QA | plan, frame, film, cine_look, 16-frame, proof page | measured gates | yes | plan, film, hybrid composite/video; no frame_checks (GPU only), no judge, no proof page | PARTIAL |
| 20 | Delivery | MP4, thumbnail, metadata, NOTES.md, lessons | publish | yes | `final.mp4` only | PARTIAL |
Additional Ricks stages that exist: density gates (`density_check.py`, `detail_density.py`, present on the branch, never run on our sets), `cine_look.py` (present), 16-frame check, random-frame check, "IT MUST NOT LOOK LIKE" list, YouTube metadata, lessons into `library/`, one folder per film `episodes/<name>/`. Missing from the branch: `check_motion.mjs`, `rules/dept/*`, `episodes/`, `blender_look/tex`, `references/look_locked`.

## 6. Proven backend: PRESERVE (evidence)
| Capability | Evidence |
|---|---|
| Plan bake + gates | `tools/film_plan.py` (758 l); 0.23 s on film_example; 0 FAIL on four example films; gate count is 45 in pipeline output (documentation drift: older docs say 37 / 41) |
| Lock export + stale detection | Phase 2/3 tests; `from_lock.read` verifies hashes |
| Deterministic camera, `follow`, `flight:` follow | evidence notes H2 (+0.297 m); Phase 2 |
| Character cards | Ricks code; Western/canyon renders; B/A sharpness 1:1 crops (A/B evidence) |
| Flight bridge | `phase2/evidence/phase2_report.json`: Blender world == plan 0.0 m, projection <= 0.7 px |
| three.js base renderer | local 1.75-2.06 s/f; Colab CPU 4.35 s/f (`phase7/evidence_colab`) |
| Blender layer + masking | Phase 3 Colab: A 0, B +0.047, 0.774 s/f; `window_glint` rejected by gate (`phase6/evidence`) |
| Composite, final assembly, decode check | `tools/final_video.py`, `phase4/test_qa.py` (6 negative cases caught) |
| Hash cache, orchestration | Phase 6 test (2.9 s rerun); Phase 7 full film (460 f) |
| QA gates | `qa_hybrid.py`, `check_film.py`; QA correctly stops on a content FAIL |
| 720x1280 production | all phases |
Keep all of it. None may be deleted because the front half was incomplete.

## 7. FINAL LOCKED ARCHITECTURE (every arrow validated)
```
REFERENCE / IDEA                          [Ricks 1,4]
 ↓  Claude: studio-director + writer + rick-researcher
STORY → SCRIPT / WORDS (voice → words.json)   [Ricks 1-3]
 ↓
REFERENCE BOARD → PICTURE_PLAN → LOOK_BIBLE   [Ricks 4-5, CB_RULES 0, 11d]   (hard gates)
 ↓
CHARACTER PRODUCTION  (casting from the 150-cast, views, expressions; check_views)   [character-artist]
 ↓
ASSET WORKSHOP (Blender, once)  →  GLB + preview + registry entry   [props-hero, 3d-designer, set-builder; our seam]
 ↓
film.json  →  PLAN BAKE / Ricks gates  (film_plan check, 0 FAIL)   [camera-director, animator, lighting, vfx]
 ↓
three.js STORYBOARD (START/END) → WHOLE-FILM ROUGH BOARD / HOOK ANIMATIC   [cheap, CPU]
 ↓
ONE advisory judge pass (fresh context) → HUMAN APPROVAL → approval.json; formal independent judge on the polished stretch
 ↓
LOCK   (--export-lock, hashes)
 ↓
ONE EXPENSIVE FINAL RENDER:  three.js final base (Colab/Kaggle/local)  [+ Blender masked layer only where approved, §10]
 ↓
FFmpeg composite / edit / captions → SOUND (after visual lock) → grade → FINAL QA → DELIVERY
```
Validation notes: the boxes "Asset workshop → GLB → three.js" and "approval.json gate" are **new bridges** (they do not exist in Ricks or in code today). All other arrows exist in Ricks. Storyboard, animatic and final base are three different things (§9).

## 8. Blender (precise role)
**Is:** asset workshop (sets, props, materials, textures), environment and prop builder, simulation tool, lighting tool for assets and layers, source of reusable GLB, selective masked-layer renderer where a hero object earns it, optional full-frame renderer only when evidence on equal-detail assets proves it better.
**Is not:** a per-frame rebuild of every shot, a replacement for three.js, a mandatory full-frame renderer, the default final picture.
**Seam (mandatory path, no isolated experiments):** `Blender asset → GLB (+ mat: names, scale, anchors) → asset registry → three.js set loads it → storyboard → lock → final render.` A Blender asset that never reaches the picture does not count as done.
**Ricks-native alternatives that remain legal:** dense coded three.js set modules (Ricks set-builder, 30+ kinds, 600+ objects) and BlenderKit `props/<object>.glb` for hero objects (props-hero). Whether Ricks' own three.js kit loads `.glb` props: UNKNOWN (only `GLTFExporter` is vendored in `templates/threejs_film/vendor/`; no `GLTFLoader` on the branch). The seam therefore needs a small loader bridge (R4); that is the only new three.js code it needs.
**Seam requirements (D-3, approved):** (1) add only the minimum GLB loading capability to the three.js kit; (2) no second scene description; (3) no second asset schema (the existing `library/assets/registry.json` is extended in place); (4) Blender remains the source/workshop for approved 3D assets; (5) `film.json` remains the only plan schema; (6) three.js remains the final-base renderer; (7) the registry identifies approved assets; (8) the same asset is reusable across episodes; (9) a three.js set module references an asset ID, never duplicated Blender geometry; (10) the seam preserves Ricks anchors, scale, material identity (`mat:` names) and placement. Goal: BUILD ONCE, APPROVE ONCE, REUSE MANY TIMES. Blender creates/reuses approved assets; three.js assembles them into the final coded picture per the Ricks plan; it does NOT mean every scene is generated inside Blender.
**Rule:** new detailed geometry is produced as an asset (Blender or recipe) and reused; a set is not "written once more" per film. The Western's single recipe (`kit/recipes/western_noon.json`) read by both the Blender kit and `western_street.js` is the model: one description, two consumers, byte-identity gate.

## 9. three.js (precise role)
**Owns:** final base picture (sets as loaded/authored, light, shadow, PBR), character cards and their shading, camera playback from `camera_baked.json` ("owns NO camera maths"), DOF with characters crisp, bloom/halation, dust motes, grain-free finish, vignette, 2D fx and highlights, `fx_bolt`, transitions, frame timing, the storyboard, the rough board, the hook animatic.
**Three distinct outputs, never conflated:**
| Output | Purpose | Quality | Cost | Gate |
|---|---|---|---|---|
| Storyboard | START/END of each camera move with caption | stand-in cast and simple sets allowed | seconds (Ricks: 19 s for 20 panels, CPU) | judge + human |
| Rough board + hook animatic | the one gate: whole film key frames + 10-15 s moving with voice/captions | no polish | minutes CPU | human approval |
| Final base | the picture of record | full detail, full-size characters (Ricks: never a half-size animatic scaled up) | the one expensive render | QA |

## 10. Blender layers policy (Ricks-aligned)
Default: no layer. **Do not reproduce in Blender anything the three.js base already provides** (DOF, bloom, dust, vignette, highlights, lighting, effects, shadows, PBR materials). A layer must pass all seven: (1) alignment, (2) mask correctness, (3) no unintended darkening, (4) no flattening, (5) measurable contribution, (6) visual contribution, (7) acceptable render cost; otherwise DROP THE LAYER. `lamp_reflect` remains an optional experimental proof, never a mandatory production stage. A layer is allowed only if: its subject is a polished/glass/wet/metal hero object that is the star; the matte covers at least 1.5 % of the frame per frame (Ricks, measured on the matte); its named objects sit at the subject's focus distance (our known focus issue, §20); it passes before/after, gates A/B/D/E (thresholds untouched: A 0 outside mask, B <= +0.06, D <= 15 s/frame, E <= 0.5 px) and is approved in `review.json`. `lamp_reflect` stays optional and out of the default path. The production command never passes `--accept-layers` by default.

## 11. 2D character system (unchanged)
Characters stay 2D puppet cards; 3D environments, props, effects; no 3D characters.
- **JS that must remain:** `rig.mjs`, `rig_cast.mjs`, `puppets.mjs`, `poses.mjs`, `templates/vector2d_characters/code/*` (cast, outfits, hair, face gear), `motion_styles/library.mjs`. They run in Node + Playwright and produce PNG sequences plus `index.json`.
- **Enters the picture:** three.js shows cards as camera-facing planes at real depth (half self-lit); Blender (when a layer runs) uses the same PNG sequences via `from_lock.card`, as Holdout for masking.
- **Crispness:** full-size rendering, cards never blurred, DOF keeps the subject card crisp, `card_sharpness.json` test. **Matte/occlusion:** owned by three.js; the Blender-card head offset seen in Phase 1 is undiagnosed (UNPROVEN).
- Nothing moves from JS to Blender.

## 12. Creative front half (restored, enforced)
1. **Reference board (D-2, as corrected by the owner): reference is a creative input, not a render-time dependency.**
   - **BEFORE LOCK** the Claude/Ricks creative workflow MAY read the reference video, extracted frames, images, timing, staging, camera movement, composition, lighting, character behaviour, object placement and visual rhythm. The outputs are: `REFERENCE_BOARD` (2-4 frames per beat with frame ids, shot kind, one line each for camera/set/light/acting/VFX, plus the department index), `PICTURE_PLAN`, `LOOK_BIBLE`, camera notes, character notes, asset requirements and timing requirements. Those outputs are written into the plan files (`film.json`, `words.json`) and notes by the creative stage; they are recorded, hashed in `approval.json`, and frozen by the lock.
   - **AFTER LOCK** the renderer never consults the reference video. It renders only from the approved `film.json`, baked camera, baked performance, approved assets, approved look and lock files.
   - The reference then serves as an **answer key** for visual QA, side-by-side comparison, creative review, judge review and post-production verification.
   - Reference frames stay private (Ricks): they are never published and never placed in a delivered video; only the owner's own explainer side-by-side is allowed.
2. **PICTURE_PLAN** (fields, deterministic enough to drive implementation, one row per named thing or action): row id; landing word (caps); seconds; shot kind and size (W/M/C/P/O); characters; actions (doer + thing + result); props and hero-object step; environment/place; camera (framing, movement, rig); staging (depth, foreground object); lighting (light kind, mood); effects and gag with its mechanism; words/captions; reference frame ids; shown (CLOSE / IN SCENE / NOT SHOWN + reason); expected visual outcome (the one-line picture test); markers HOOK/TWIST/SIGNATURE/LAST FRAME. Written fresh per story; no row copied between films.
3. **LOOK_BIBLE:** palette, light per chapter, shadow and contact numbers, grade numbers (saturation 0.40-0.50, brightness 0.42-0.50, darkest 1 % 0.08-0.15), lens, chosen reference frames.
4. **Targets** recorded per production: composition, character, environment, lighting, colour, camera, effects, density.
5. **Character production:** cast chosen per script (CAST_TRAITS), outfit colours from the LOOK_BIBLE palette, views checked (`check_views.mjs`), casting recorded in `CASTING.md`; reuse of an existing character is allowed only if recorded as a decision with its reason (never as a silent substitute).

## 13. Asset library
Registry `library/assets/registry.json` (exists, 2 entries). Required fields per asset: `id`, `category`, `source`, `blend_file`, `glb`, `preview`, `materials` (mat: names), `variants`, `scale` (metres, Z up in plan, Y up in glb), `coordinate_convention`, `anchors` (named points: hand/muzzle/mount), `tags`, `dependencies`, `version`, `sha1`, `license`, `ricks_quality_status` (stand-in / detailed / approved). Build once, reuse many; an approved asset is not regenerated per episode. `tools/assets.py check` enforces the fields; the same file is extended in place (no second asset schema) in R4/R7; the present entries lack `glb`, `sha1`, `anchors`, `ricks_quality_status`. A three.js set module refers to an asset by `id`.

## 14. Storyboard, animatic, judge (reconciliation, D-1)
Ricks has two statements: the storyboard-judge agent (score every panel 0-10, only 8.5+ goes to CB) and CB_RULES §11a (no judge loops and no polish before the one gate; the 8.5 bar "decides when a shot is finished, not when CB first sees it").
**Blueprint rule (D-1, approved with the owner's correction):** (1) **rough-board gate:** picture plan + reference board + rough board + moving hook; ONE cheap *advisory* judge pass by a separate fresh-context viewer (never the author) gives scores and a fix list; no revision loops; (2) **human approval** of the rough gate (the owner); (3) **polished stretch:** ONE formal independent judge (fresh context, never the author or the advisory judge's context carried over) scores each panel, **8.5+ per panel remains the target**; at most **one fix round per version**; no endless judge loops; (4) the judge can never approve its own work; (5) **final human approval remains the owner's** and is recorded in `approval.json`. studio-director still checks side-by-sides and five-details. Purpose: keep Ricks' cheap-rough-whole-film-first philosophy instead of spending hundreds of millions of tokens on repeated still-picture judge loops. Score parts (Story 0-4, Framing 0-2, Staging 0-2, Look 0-2) and caps (Hard Rule 2 caps a panel at 6) are preserved. The 8.5 threshold is not changed; no evidence suggests changing it.

## 15. Compute ownership and GPU claims
Cheap (Claude/CPU): planning, Blender asset construction, three.js storyboard/animatic, contact sheets, QA. Expensive: final base render, heavy Blender simulation, GPU rendering.
Every GPU claim needs evidence for that exact path:
| Path | Evidence | Status |
|---|---|---|
| Ricks three.js GPU, local RTX 2070 SUPER, Windows, Chromium 131, 1080x1920, armor film (43,700 objects) | `templates/threejs_film/GPU_RENDER.md`: 0.55-0.9 s/frame vs 4.7 s software; device printed from WEBGL_debug_renderer_info | Ricks-measured, different hardware/scene/path, NOT ours |
| three.js on Colab T4 | Phase 5/6: Chrome reports SwiftShader; `render_gpu.mjs` stops as designed | FAILED path; CPU fallback 4.33-4.75 s/f |
| three.js on Kaggle T4, user's local GPU | none | UNKNOWN |
| Blender EEVEE on Colab T4 | `experiments/blender_first_ab/evidence_colab/evidence/timing.json` (raw, verified): 5.2.4 LTS, BLENDER_EEVEE, 64 samples, 720x1280, platform place, 175 frames: first 41.896 s, mean 3.387, median 3.331, P90 3.801, steady mean 3.166, total 592.79 s; GPU util mean 78.6 % (P90 98 %), VRAM peak 1835 MiB of 15360; compose CPU 0.891 s/f; lock export 46.9 s; set = 789 three.js-origin objects | MEASURED |
| three.js CPU local 2-core | Phase 7 local 1.83 s/f (460 f), A/B 1.75 s/f (175 f), canyon 1.93 s/f (299 f) | MEASURED |
| three.js CPU Colab | Phase 7 4.35 s/f (median 3.91, P90 5.74, max 6.93, cold 7.3 s); A/B 4.521 / 4.779 / 5.103 (150 / 10 / 15 f) | MEASURED |
| Blender layer Colab | 0.67-0.77 s/f steady, 49.6-51.2 s cold | MEASURED |
**The "2.14 s/frame" EEVEE figure:** no raw file in the repository records it (a search of all JSON/CSV/MD/notebooks finds the string only inside an unrelated list in `references/measure/gates_cine.json`). It came from a separate report that is not in the repo. Status: UNKNOWN. It must never be used as a Western or project baseline; it proves nothing about this scene or path until its raw data is in the repo. Different scenes are never mixed in one comparison.
Default: develop and QA on Colab; render farm Kaggle/local only after a GPU path is proven for that machine by a measured test (R6).

## 16. QA architecture (owner per stage)
| Class | Checks | Owner |
|---|---|---|
| Technical | hashes, missing frames, resolution, frame count, fps, decode, stale inputs, camera, flight, masks, composite, video | `film_plan check`, `layers.py`, `qa_hybrid.py`, `final_video.py` |
| Visual | character readability, composition, light, materials, DOF, effects, density, camera rhythm, hierarchy, reference match | `check_film.py`, `frame_checks` (needs GPU), `cine_look.py`, `density_check.py`, `detail_density.py`, `check_views.mjs`, side-by-side vs the reference board; reference match is a judge/human check (not automated; UNPROVEN) |
| Creative | story, pacing, hook, Ricks style, judge score | storyboard-judge, studio-director, human; proof page |
Add (Ricks, not yet run on our films): 16-frame check, random-frame check, "IT MUST NOT LOOK LIKE" list.

## 17. Sound dependency (from Ricks)
Voice and `words.json` come **before** `film.json` (every anchor is a word time); a silent video still needs `words.json`. Rough sound exists in the animatic; real SFX/ambience/music come from `sound_events.json` **after the visual lock**, beside the final render; the mix never re-times the voice; captions depend on `words.json`; the last frame loops into frame 0 (sound too). Sound is not implemented until a full silent video passes review.

## 18. Gate table (hard gates; none may be skipped)
| # | Gate | Check | Blocks |
|---|---|---|---|
| G1 | Script | `script_stats.py` in bands, first line action, human approves | words/plan |
| G2 | Words | 3.5-4.5 w/s, no long gaps | film.json |
| G3 | Reference board | every beat has >= 2 same-kind frames, department index filled | picture plan, storyboard |
| G4 | Picture plan | every named thing has a row, CLOSE/IN SCENE/NOT SHOWN with reason | film.json |
| G5 | Plan | `film_plan check` 0 FAIL, <= 2 WARN with reasons | storyboard |
| G6 | Characters | `check_views.mjs` PASS, casting recorded | storyboard |
| G7 | Assets/sets | density gates, asset in registry with `glb`, five details per main object | storyboard |
| G8 | Rough gate | storyboard + rough board + hook animatic exist; one judge pass recorded | approval |
| G9 | **Approval** | `approval.json` valid and fresh (§19.4) | lock and every expensive render |
| G10 | Lock | `lock.json` sha1 of film.json, baked plan, asset versions | final render |
| G11 | Layers (optional) | §10 | composite |
| G12 | Final video | decode, frame count == film `end`, resolution, fps, composite hashes | delivery |
| G13 | Film QA | `check_film.py` + `cine_look.py` + 16-frame check, 0 FAIL (content FAILs are reported and classified, never relabelled, thresholds untouched) | delivery |
| G14 | Sound | mix gates, cue within 2 frames, loop click-free | delivery |
| G15 | Delivery | MP4, thumbnail, metadata, proof page, lessons into `library/` | publish |

## 19. approval.json and lock
**`approval.json` (required fields):** `film` (name), `plan_sha1` (film.json), `baked_sha1` (camera/performance/flights/layers), `picture_plan_sha1`, `reference_board_sha1`, `look_bible_sha1`, `asset_versions` (id -> version + sha1), `character_sheets_sha1`, `storyboard_sha1`, `animatic_sha1`, `judge` {reviewer, score per panel, verdict, fix list sha1}, `approvals` {creative, storyboard, characters, assets, camera, look: each true/false with reviewer and ISO timestamp}, `reviewer` (human), `approved_at`.
**Refuse rule:** the final renderer and `--export-lock` refuse to run if `approval.json` is missing, any `*_sha1` differs from the current file, or any approval flag is false (stale approval = no approval).
**Lock freezes:** `film.json`, picture plan, camera, character sequences, asset versions, environment glb, materials, animation, effects, references board hash. After lock, creative changes require unlock and re-approval; layer recipes and composite settings may change without unlock.
**Frame semantics (known bug fix, §20; owner-specified):** for N frames (N = `film.json end`) the valid indices are 0..N-1. `--frames 0-(N-1)` and `--frames all` are the full film; `--frames 0-N` (any b >= N) is an ERROR; `a-b` is inclusive. Any partial range must never report a full-film PASS: it reports "full-film check skipped" as SKIP. Full-film validators verify the exact expected frame set (every index 0..N-1 present, none extra). Regression tests (R1): N=299 with `0-299` fails; `0-298` and `all` pass and run the full-film check; a partial range reports SKIP; a missing or extra frame fails.

## 20. Known bugs and limits
| Item | Class | Status |
|---|---|---|
| `--frames` off-by-one + silent skip of full-film check (observed: `0-299` on `end 299` rendered 300 frames, QA PASS without the film check) | ENGINE BUG | open, must be fixed before production (R1) |
| Camera rhythm FAIL on Western (rests per 10 s 6.54 local / 7.19 Colab vs 2.2-3.8; travel P90 1.1 s vs 2.1-6.3) and canyon (5.03) | CONTENT BUG (shot planning; plan was written as a pipeline exercise); thresholds untouched. Same two gates also FAIL on Ricks' own `film_example` (evidence notes A), so the plan-vs-picture fit constants (`SEEN`, `REST_PX`) are a Ricks-acknowledged unproven item | open |
| Canyon: camera passes through train (frames 125-150), grey beam fills frame | CONTENT BUG + QA blind spot (no camera-vs-geometry check; Ricks has `proj.py` rule, file not on branch) | open |
| `window_glint` focus mismatch (out-of-focus objects vs sharp layer) | QUALITY LIMITATION; rule: layer objects at subject focus distance; no automatic in-focus check | documented |
| `lamp_reflect` faint, visible only in x6 difference | QUALITY LIMITATION; optional | documented |
| three.js GPU in Colab Chrome | UNPROVEN (SwiftShader) | documented |
| Western/canyon three.js sets are toon boxes | CONTENT/ASSET shortfall (not an engine bug) | R4/R5 |
| Blender-built kit geometry never reaches the picture | ARCHITECTURE GAP (missing seam) | R4 |
| Missing creative gates | ARCHITECTURE GAP | R1 |
| Gate-count drift (37 / 41 / 45) | DOCUMENTATION DRIFT | noted in §6 |
| `MANIFEST.md` said three.js is "not our renderer" and Blender is the renderer | DOCUMENTATION DRIFT | **fixed in this change** |
| Card head offset in Blender layers undiagnosed | UNPROVEN | documented |
| `tex`, `look_locked`, 80 view PNGs, `check_motion.mjs`, `rules/dept`, `proj.py` not on the branch | MISSING EVIDENCE/ASSETS (never copied; some absent from the zips) | restore as needed, R3/R4 |

## 21. Anti-drift rules
1. Never replace a Ricks stage unless this blueprint names the replacement. 2. Never remove a Ricks agent without explicit approval (section 24 lists their fate: none removed). 3. Never replace a creative stage with a shortcut; a missing stage is reported missing. 4. Never write large three.js systems where a reusable Blender asset or recipe is the intended solution. 5. Never change architecture on one benchmark or a confounded experiment. 6. Never change QA thresholds to pass. 7. Never classify a creative failure as an engine failure. 8. Never classify an engine failure as content. 9. Never render expensive final frames before approval (G9). 10. Never add architecture for one isolated shot without evidence. 11. Architecture changes require explicit approval. 12. If implementation conflicts with this blueprint, STOP and report. 13. A document that contradicts this blueprint is corrected in the same change. 14. A stage listed as INPUT/REVIEW but never checked is reported as unenforced, not complete. 15. A renderer comparison must use equal-detail assets or declare the confound. 16. A benchmark number is used only for the scene, hardware and path that measured it. 17. Reference material is mandatory creative input before lock and an answer key for QA afterwards; it is never a render-time dependency (the renderer does not consult it).
**Hybrid vs Blender-first (explicit):** the A/B was confounded (Route B rendered a lock whose geometry is three.js toon boxes, 789 objects, not equal-detail Blender assets). It does NOT show that Blender-first lost. The hybrid stays the default because it is Ricks' own newest architecture and has the proven back half; Blender-first stays a documented experimental fallback; no further A/B until the asset seam exists and equal-detail assets can be compared; no deletion of three.js; no new renderer; no rebuilding of the Ricks three.js look.

## 22. Decisions (all resolved by the owner, 2026-11-23)
- **D-1 judge: APPROVED with the owner's correction** (section 14): one cheap advisory judge pass at the rough-board gate, one formal independent judge on the polished stretch, 8.5+ per panel target, max one fix round per version, no judge loops, the judge never approves its own work, final approval is the owner's.
- **D-2 reference: APPROVED as corrected** (section 12.1): "Reference material is mandatory creative input before lock and remains available as an answer key for QA; it is not a render-time dependency." The earlier draft ("pipeline never reads the reference video") was too broad and is withdrawn everywhere (section 30).
- **D-3 asset seam: APPROVED with the ten requirements** of section 8: Blender asset -> GLB -> three.js loader -> three.js set (by asset id) -> storyboard/animatic -> approval -> lock -> final base. Implementation is R4 only, on the owner's "GO R4".
- Also locked: hybrid default; Blender layers optional (seven conditions, section 10); camera and timing ownership (section 2a); 2D characters; 720x1280 at 30 fps; incremental roadmap.

## 23. Change control (classes)
A bug fix · B documentation · C implementation detail · D performance optimisation · E architecture change · F creative rule change · G Ricks rule removal or replacement. **E, F and G need explicit approval.** A content change never becomes an architecture change silently. Every change records: class, reason, evidence, affected files, blueprint section, tests, visual impact, approval status. This list supersedes the A-G list used in the earlier audit. A rendering problem never authorises changing the creative workflow; a poor reference recreation never authorises replacing Ricks.

## 24. The 16 agents (read from the actual files; none removed)
| Agent | Kind | Ricks role (inputs -> outputs) | Disposition |
|---|---|---|---|
| studio-director | approval/QA | final judge, never builds; enforces Rule 1/2; proof page; reads all `crew/*_check.md` | preserved, explicit (independent of builders) |
| storyboard-judge | QA | scores panels 0-10 (Story 4, Framing 2, Staging 2, Look 2), 8.5 bar, fix list; fresh context | preserved, explicit (§14) |
| writer | creative | script, beats, voice lines, words, CAST_TRAITS, PICTURE_PLAN (with lead) | preserved |
| rick-researcher | creative/research | reference board + department index + camera_track | preserved, restored (G3) |
| camera-director | creative+technical | camera idea (5 candidates), 3 hero moments, stations -> film.json, plan check, storyboard | preserved; validator = `film_plan` |
| character-artist | creative | casting from locked 150-cast, outfits from scene palette, `check_views` | preserved, restored (G6) |
| animator | creative/technical | acts, motion library, `check_motion.mjs` (not on branch), animatic | preserved as stage; check file to restore |
| set-builder | creative/asset | dense set per place, DRESSING.md, density gates | adapted: recipe + asset -> glb (D-3), or dense coded module |
| background-painter | creative/asset | sky, far layers, haze | merged into the set stage; role kept |
| props-hero | creative/asset | hero object first, alone, `props/*.glb`, BlenderKit | adapted: Blender asset workshop -> registry |
| 3d-designer | asset | real models/materials | adapted: asset workshop (Blender); layers only |
| lighting-director | creative/technical | moods, LOOK_BIBLE light, contact shadow numbers, `cine_look` | preserved; three.js owns light, Blender keeps coded light |
| vfx-artist | creative | fx/kicks on words, FX.md | preserved; Blender fx recipes only for approved layers |
| look-finisher | execution | Blender look passes | adapted: optional layer stage only (§10) |
| editor-compositor | execution/QA | joins, captions, final grade, `check_film` | preserved: FFmpeg stage |
| sound-designer | execution | cues, mix | preserved, deferred (§17) |
Lead/director = Claude main thread plus the human owner. Agents with an automated counterpart stay explicit agents when they make creative or independent-judgement decisions (writer, researcher, camera-director, character-artist, set-builder, props-hero, lighting, vfx, judge, studio-director) and become pipeline stages when mechanical (animator acts compile, editor-compositor, look-finisher layers, sound-designer).
Ricks token rules (T1-T9) are preserved as operating rules: read only your slice, one build or one fix round then end with STATE.md, numbers before pictures, one command per cycle, short reports, small model for mechanical work, a fresh lead session per phase, nothing built twice, measure every film.

## 25. Ownership
| Concern | Owner |
|---|---|
| Story, script, picture plan, look bible, reference board | Claude (writer, researcher, studio-director) + human approval |
| Characters | character-artist stage; Ricks puppet kit renders |
| Assets | Blender workshop (once) -> glb -> registry |
| Camera | camera-director writes film.json; `film_plan` bake -> `camera_baked.json` is the single result for three.js and Blender; `cine.py` rigs usable only by feeding the bake (§25 note) |
| Timing | `words.json` + `film.json` -> baked timing; every downstream tool consumes it |
| three.js | final base, cards, DOF/bloom/dust/vignette, 2D fx, storyboard/animatic |
| Blender | assets; optional approved layer |
| Rendering | Colab / Kaggle / local (proven path only) |
| Composite, edit, captions | FFmpeg / editor-compositor |
| Sound | sound-designer stage (after visual lock) |
| QA | gates in §16, judge, human |
| Approval | human owner via `approval.json` |
| Asset library | registry + `tools/assets.py` |
`cine.py` (257 l): rigs (`chase`, `mount`, `orbit`, `catch`, `static`, `push`, paths `line/spline/loop/ballistic/mix/object_path`) and `Shot.eval` are pure math on `mathutils.Vector`; `Shot.bake` keys a Blender camera (bpy). It was not rewritten by us; nothing calls it. Usable in the plan bake only via a deterministic evaluation that yields `camera_baked` rows; `mathutils` is not installed locally (a standalone package may exist; availability and exactness vs Blender: UNKNOWN). Implementation detail for R2/R5, only if a story needs a moving-object camera; `follow` and stations cover the rest.

## 26. Deprecation list (nothing deleted now)
Fallback-only: Route B (`experiments/blender_first_ab`), `lamp_reflect`. History/evidence only: `fulltest/` Pass A stack (own intent compiler, shotmath, `blender_full.py`), `slice01/`, `phase1/phase1b/phase1c` (note `phase1b/compose_1b.py` is imported by `tools/layers.py`). May be superseded later: duplicate gate counts in older docs. Unrelated scratch never committed: `views_golden/_last_sheet.png`, `_last_run/`.

## 27. Do-not-do list (for every future agent)
Do not build another renderer, framework, planning schema or scene-description format. Do not write a new per-film three.js set from boxes when an approved asset or recipe exists. Do not render before G9. Do not call a render proof of quality. Do not change a QA threshold. Do not remove a Ricks agent or rule. Do not use a reference as a numeric input. Do not treat one benchmark as architecture. Do not hide a content failure as an engine failure. Do not implement sound before an approved silent video. Do not use the unrelated 2.14 s/frame figure. Do not touch `main`.

## 28. Unknown / unproven (intentionally documented)
Whether Ricks' kit loads glb props (no loader vendored); Blender-to-glb round trip speed and `mat:` fidelity in three.js (R4 spike); three.js GPU on Colab/Kaggle/local GPU; mathutils availability for `cine` evaluation; TTS and Fish key; independent judge behaviour in practice; automated reference matching (not planned); 1080p+; asset reuse across episodes; the missing Ricks files (`tex`, `look_locked`, `check_motion.mjs`, `proj.py`, `rules/dept`, `episodes/`); whether `lamp_reflect` met Ricks' 1.5 % matte rule (not measured); the origin of the 2.14 s/frame figure.

## 29. Roadmap (one order; changed from the hypothesis only where evidence required)
Change from the hypothesis: the `--frames` fix and `approval.json` come first because every later render depends on them; the Colab/Kaggle phase waits for the first production test.

| Phase | Objective | Inputs -> outputs | Files | Tests / acceptance | Expensive ops | Renders | Approval |
|---|---|---|---|---|---|---|---|
| **R0** Blueprint lock (this task) | blueprint + doc reconciliation | audit -> this file, MANIFEST fix, pointers | `docs/*`, `MANIFEST.md` | owner approves D-1..D-3 | none | 0 | yes (D-1..3) |
| **R1** Creative gates + approval + frame fix (only these; starts on "GO R1") | enforce G1-G9; fix frame semantics with regression tests | `refs/`, PICTURE_PLAN, LOOK_BIBLE, `approval.json` -> pipeline refuses without them | `tools/pipeline.py` (+ one validator), `tools/qa_hybrid.py`, `render.mjs` frame parse | missing board stops the run; N=299 `0-299` fails; stale approval refused | none | 0 | no |
| **R2** Storyboard / animatic / judge | cheap review package | film.json -> storyboard, contact sheet, hook animatic, judge sheet, camera-vs-geometry report | `render.mjs --storyboard` (existing), one report script | canyon f125-150 clipping flagged; judge pass recorded | none (CPU minutes) | CPU hook only | yes (rough gate) |
| **R3** Character production | story characters | CAST_TRAITS -> CASTING.md, sheets, views | puppet kit, `check_views.mjs` (+ restore missing view PNGs if needed) | engineer distinct and passes views | none | 0 | yes |
| **R4** Blender -> GLB -> three.js seam (D-3 approved; starts on "GO R4") | detailed assets in the picture | recipe/Blender -> glb + registry -> three.js loader | new `GLTFLoader` vendor + set loader, registry schema, export script | 10-frame CPU base, objects/detail vs toon set, s/frame measured per scene, `mat:` fidelity | Blender build on Colab (once) | 10-30 CPU frames | yes |
| **R5** First reference-driven production | prove the chain on ONE small shot (proposal: the 3-5 s opening hook of the railroad reference, which already has words; not the Western, not the full canyon) | reference -> board -> plan -> character -> asset -> storyboard -> judge -> approval -> lock -> final | `episodes/<name>/` | beside-reference review by the owner; all G1-G13 pass; failures classified by §23 | 1 final base render (<= 150 frames) | 1 | yes |
| **R6** Render orchestration (Colab/Kaggle/local) | render only approved ranges, measured GPU paths | lock -> frames, outputs to Drive | notebook, `pipeline.py` | 15-frame range then film; every GPU claim has a printed device and timing | final render | 1 per approved version | yes |
| **R7** Asset library | register approved assets | R5/R4 assets -> registry with glb/sha1/anchors | `library/assets/*` | a new film uses a registered place with no rewrite | none | 0 | no |
| **R8** Sound | cues -> mix | `sound_events.json`, SFX library | audio stage | mix gates, cue within 2 frames, loop click-free | none | 0 | yes |
| **R9** Captions, final QA, delivery | finish | video -> MP4, thumbnail, metadata, proof page, lessons | `final_video.py`, QA | G12-G15 | none | 0 | yes |
After R5 passes, a larger episode (the canyon, or a new story) is allowed. Not in R1-R9: sound before R8, advanced Blender enhancement effects, automatic DOF/in-focus detection, any new GPU renderer, endless repair of the Western example.

## 30. Consistency pass (2026-11-23, documentation only)
Searched the repository (excluding the Ricks reference files, which are quoted sources) for: "not our renderer", "Blender is the final renderer", "pipeline never reads the reference video", "Blender is mandatory", "full-frame Blender is the default", duplicate planning schemas, stale architecture claims. Found and resolved: `MANIFEST.md` (renderer ownership; fixed in 53c4c88); `docs/RICKS_HYBRID_ARCHITECTURE_SPEC.md` §9 item 5 (reference rule; amended); `fulltest/README.md`, `fulltest/PLAN_AND_AUDIT.md` line 9, `fulltest/DIRECTOR_PLAYBOOK.md` (reference "never read" wording and the `intent_passA.json` / `compile_intent.py` planning path, a duplicate of `film.json`; marked HISTORICAL/superseded with a banner, files otherwise untouched); `docs/IMPLEMENTATION.md` (pointer to this blueprint). No implementation code was changed. The Ricks files' own internal older statements (WORKFLOW step 9 Blender look pass, agent briefs for 3d-designer and look-finisher, STYLE_BIBLE ink-on-world, SCORECARD ink 60 %) are Ricks sources, left intact, and are overridden by section 3 here per Ricks' own "newest rule wins".
