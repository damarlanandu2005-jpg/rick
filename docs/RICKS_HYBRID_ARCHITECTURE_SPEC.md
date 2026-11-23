# RICKS + THREE.JS + BLENDER HYBRID — PRODUCTION SPECIFICATION (v2, after the forensic pass)
> **Subordinate to `docs/PRODUCTION_BLUEPRINT_LOCKED.md`.** v2 is kept as the reasoning record. Corrections since v2: (1) the three.js-final-base / Blender-masked-layers split is Ricks' own newest rule (CB_RULES §3, §11a), not only our decision; (2) §9 item 5 (reference board) is amended by blueprint D-2; (3) §11/§13 flight and lock text stands; (4) the creative front half and the Blender-asset-to-glb-to-three.js seam are required, not optional.

Date 2026-11-21. Branch `ricks-2d-core`. Specification only: no code, no validators, no resolver, no render, no Pass A fix.

**v2 status.** Rewritten from `docs/RICKS_EVIDENCE_NOTES.md` (sections A–M) after the director's decision: **three.js = final base picture; Blender = masked enhancement layers; Ricks stays the creative and quality baseline; no full-frame Blender replacement.** Sections 1–5 describe Ricks as it is and are unchanged except where marked. Wherever sections 1–5 mention a Blender executor, sockets, Blender-built sets or whole-frame Blender, sections 6 onward govern. The v1 text is in git history (commit 59e9b17).

## 0. How this was produced, and its limits
Read in full: `WORKFLOW.md`, `FILE_GUIDE.md`, `templates/PICTURE_PLAN.md`, `film_plan.py` header, `film_example/film.json` keys, `threejs_film/README.md`, `CINEMATOGRAPHY.md` headings and shot table, `DENSITY_RULES.md` headings, the SKILL.md stage and crew tables, and CB_RULES sections 6 and 11 plus the Camera director and Sound brief bodies.
Read as a skim (first ~200 characters of every rule line): CB_RULES sections 3, 4, 5, 7, 8, 9, 10, and the "What you own / Inputs / Outputs / Gate" block of all 16 agent briefs.
Not read line by line: the remaining ~20,000 words of CB_RULES detail, the 20 pitfall notes (titles only), `blender_look` code, `cine.py` code, `templates/audio` code beyond headers, every individual pieces file.
Everything below that says "Ricks proves/claims" is Ricks' own record. I have not re-run it in our environment. "CB" in Ricks files is the Ricks project owner; I treat his rules as the methodology.
Conflicts found inside Ricks and how v2 settles them (newest rule wins): STYLE_BIBLE ink on world vs CB_RULES ink on characters only → characters only. STYLE_BIBLE captions vs standing silent rule → silent for now, caption spec kept for later. CB_RULES section 11 "Blender optional" and the newest "Blender = only the layers it does better" → adopted; whole-frame Blender is not the default. film.js comment "Blender does the real DOF" is older than the newest rule and is superseded.

## 1. Ricks production philosophy (from the source, in its own priorities)
1. **Quality bar is measured against a reference channel** (Rule No. 1) and "nothing generic" (Hard Rule No. 2): five specific details per main object, compared side by side with a reference frame of the same shot kind.
2. **Solve it on paper before it is built** (11d): about 14 of 23 notes on the armor film were "the thing the voice names is not shown". Almost all were knowable before any frame existed.
3. **Plan once, bake once, play everywhere**: one file (`film.json`) holds camera, acting, effects, light moods, sound cues, all tied to word times. Tools bake it into per-frame data that every renderer reads, so camera, position and timing cannot drift between stages.
4. **Numbers before pictures** (T3): anything a script can measure is measured; a person looks only when a number fails or for a final look.
5. **The story decides, never a template.** Pieces and plans are technique, not content; no row is copied between films.
6. **Order of confidence**: cheap rough whole film first (the one gate), polish only what was approved, lock layout, then look, then render, then sound and grade last.
7. **Lessons flow back into rules and libraries** so the next film starts higher. Every CB note is checked against the plan: was the row there? If not, the plan format gets the line.
8. **Measured cost**: the armor film (63.5 s) cost 1.66 billion tokens, 41 helpers, 22.7 working hours; 97 % of tokens were re-reading; about 750 M went into still-picture judge loops that were later rejected on seeing motion. The lean pipeline (section 11) targets 450 M and 12 h.
9. **Camera, cutting and effects are tied to the voice** (cut within 2 frames of a word, every narrated verb is seen, effects land 0–3 frames before the word).

## 2. Complete Ricks pipeline (SKILL.md stage table + CB_RULES section 11)
| # | Stage | Made by | Gate |
|---|---|---|---|
| 1 | Topic, facts, 3 pitches (places and lights named) | lead + writer | CB picks |
| 2 | Script with seconds and beats | writer | `script_stats.py`; CB approves |
| 3 | Voice + `words.json` | writer + lead | pace 3.5–4.5 words/s |
| 4 | Reference board (2–4 reference frames per beat) | rick-researcher | hard gate |
| 4b | PICTURE_PLAN (a row per named thing) | writer + lead | approved with the rough board |
| 5 | Shot blueprint and camera: `film.json` | camera-director (+ character-artist, animator) | `film_plan.py check` 0 FAIL, ≤2 WARN |
| 6 | Simple sets + props + storyboard: START and END picture for every camera move | props-hero, set-builder, background-painter, character-artist, animator, vfx-artist, lighting-director | judge 8.5+ per panel (retired as a pre-gate loop by section 11), CB sees every scene |
| 7 | Whole film rough in three.js with voice, captions, rough sound | lead + animator, vfx, lighting; editor cuts | `check_film.py` 0 FAIL; sound-off test; CB watches |
| 8 | LOCK (`--export-lock`): sets .glb, card PNGs, camera, performance | lead | no layout/camera/timing change after |
| 9 | Look pass per place in Blender (materials, light, air, dressing, effects only) | 3d-designer, look-finisher, lighting-director | `check_episode`, `cine_look` 0 FAIL |
| 10 | Final render | look-finisher | `check_film`, `cine_look` on the mp4 |
| 11 | Sound from `sound_events.json` | sound-designer | mix gates |
| 12 | Captions, QA, delivery | editor-compositor, studio-director | `short_qa`, proof page |
Named alternative order ("full Blender world", FULL WORKFLOW steps 5–7): Stage A build the whole scene in Python in the finished toon look (30+ kinds, 600+ objects), Stage B convert to the main look. That option is already inside Ricks and is the structural match for "Blender is our scene environment".
Section 11's lean order: story and voice → PICTURE_PLAN → ONE GATE (whole film rough + hook moving) → build out by stretch → CB notes in batches → sound → grade → delivery. Plus the 7 build steps per place (shot plan, build, camera check, environment overhaul, post, shading, frame check by a separate checker) and the proven stretch method (section 10: one place per stretch, a move written for every act, things that fly go somewhere and hit, line-check sheets, nobody cut by the frame edge).

## 3. Every production stage and its purpose
| Stage | Purpose (why it exists) | Input → Output | Kind |
|---|---|---|---|
| Story | A true, mock-and-twist story with places and light kinds named early | topic → 3 pitches | creative reasoning |
| Script | Rick pattern: action hook, ≤14-word hook, "You see" pivot at ~67 %, ironic last line, loop | pitch → SCRIPT.md + beats | creative |
| Voice | Time anchor for everything (`T(word,n)`) | script → words.json | tooling |
| Reference board | Parity floor; shows what to take (staging, framing, timing) | beats → board | research (we exclude: see section 8) |
| Picture plan | Make every named noun/verb visible, decide CLOSE/IN SCENE/NOT SHOWN with a reason | script+words → table | planning |
| Camera idea | One bold camera concept per film, three hero moments, flow plan | script → `camera_idea` | creative |
| Stations/takes | Concrete camera rests and travels on word anchors | idea → film.json takes | planning + engineering |
| Cast | Right character, costume, size, traits that read the role | traits → `cast`, CASTING.md | selection |
| Acts | Pose, face, view, prop-in-hand on each word | words → `acts` | acting |
| Sets/props | Real-parts world, hero object first, density | plan → sets, props | asset generation |
| Light/moods | Light clock follows the story | beats → `moods`, LOOK_BIBLE | design |
| FX | Effects on the word with build/pop/settle | key words → `fx`, `kicks` | design |
| Rough film | Cheap proof the whole thing works in time | film.json → animatic | execution |
| Lock | Freeze layout so look work cannot drift | rough → lock files | execution |
| Look | Materials, light, air, dressing | lock → .blend looks | asset + execution |
| Final render | Frames | .blend → mp4 | execution |
| Sound | SFX on every action, ambience, music, mix | cues → mix.wav | asset + execution |
| Edit/grade/captions | Joins, matching grade, loop | all → cut | execution |
| QA | Measured gates, 16-frame check, proof page | everything → PASS | validation |

## 4. Every Ricks artifact and what it contains
- `SCRIPT.md` (lines+seconds, beats, per beat: places, time of day, hero-object step, doer+thing+result, one effect on the key word); `CAST_TRAITS.md`; `voice/voice.wav`, `words.json` (word times).
- `refs/REFERENCE_BOARD.md` + department index; `camera_track.json` for match shots.
- `PICTURE_PLAN.md`: #, landing word in caps, seconds, what we see, shown (CLOSE/IN SCENE/NOT SHOWN + why), feeling, effect/gag, piece + what changes; marks HOOK, TWIST, SIGNATURE, LAST FRAME rows.
- `LOOK_BIBLE.md`: palette, light per chapter, contact-shadow numbers, grade numbers, lens, chosen reference frames. Owned by the lead; read by all.
- **`film.json`**: `title, fps, size, words, camera_idea{name,why,signature}, cast, places, props, takes[stations{at,lead,pos,aim,lens,subject,framing,shows,hold,travel,drift}], kicks, acts[who,at,pos,view,dir,pose,face,prop,hand], sentences[text,words,subject,nouns], fx, moods, sound`. Times are frame | [word,n,offset] | {s}.
- `out/plan/`: `plan_report.md/.json` (every gate with value/target/status), `camera_baked.json` (per frame pos/aim/roll/lens/state), `performance_baked.json` (per character run-length states), `sound_events.json`, `visibility.json`.
- `CAMERA_NOTE.md` (≤150 words, five candidates scored, kept WARNs with reasons), `crew/*_check.md` per department (side-by-side sheet, five details, gate numbers, PASS/open), `STATE.md` (≤60 lines handover), proof page.
- `sets/<place>.js`, `_DRESSING.md` (stand-in → real model, material, micro-motion, air life), `_bg.js`/`_BG.md`; `props/*.glb` + `PROPS.md`; `cast/CASTING.md`; `fx/FX.md`.
- Storyboard (`storyboard.html/png`), animatic mp4, `out/lock/` (`sets/*.glb`, `cards/<who>/s0001.png…` + `index.json`, `lock.json` with sha1).
- `look/look_<place>.py`, `_MATERIALS.md`, `edit/cut_<v>.mp4`, `joins.md`, `grade.json`, `sound/cues.md`, `mix.wav` and stems, `YOUTUBE.md`, `token_report`, `assets_log.md`.

## 5. Every agent/role: responsibility, knowledge, artifact, and what it becomes in our system
Rule I applied: a role stays an *agent* only if its job needs independent, fresh-context judgement. Otherwise its job is classed as director workflow instruction (skill), library, validator, or Blender tool. I did not decide by headcount.

| Role (Ricks) | Actual production responsibility | Knowledge/rules it contributes | Artifact it creates | Becomes |
|---|---|---|---|---|
| writer | Script with action hook, beats, mood tags, light plan, hero-object steps, cast traits | Section 1, 2 first lines, 6b build steps, light clock | SCRIPT.md, CAST_TRAITS, voice request | **Director workflow** (skill: script formula + `script_stats` validator) |
| rick-researcher | Reference board per beat; camera tracking of reference | Section 0, 6 follow his move, 6b bands | REFERENCE_BOARD, camera_track | **Library + validator**: the measured bands (`gates_film.json`, `cine_look`); per-video board dropped (see section 8) |
| camera-director | One camera idea, three hero moments, stations, rigs | CINEMATOGRAPHY, section 6, laws list | film.json camera, CAMERA_NOTE | **Director workflow** (skill) + `film_plan` validator + `cine.py` rig library |
| set-builder | Each place as one connected dense world; dressing list; micro motion and air life | Section 3, 5, 8; DENSITY_RULES | sets, DRESSING.md | **Director workflow** (decides what) + **set recipe library** + density validator |
| background-painter | Sky, far layers, haze, depth layers | Section 3 depth/haze numbers | `_bg`, BG.md | **Part of set recipe** (sky/haze preset in the recipe) + validator (3 depth layers) |
| props-hero | Hero object first; held props; build steps | Section 3 premium detail; BlenderKit | props .glb, PROPS.md | **Asset library; held props use Ricks `held3d` grip/anchor and `hand_at`, no sockets** + director decisions per story |
| character-artist | Cast, costume, colours from the scene palette, traits, crowds | Section 4 (v12 template, 500 outfits, hair, hats, face gear) | cast entries, CASTING.md | **Director workflow** + the locked `vector2d_characters` library + `check_views` validator |
| animator | Acts: studio motion, planted feet, hands end on objects, face on the word | Section 5, STUDIO_MOTION, motion library | `acts`, moves | **Director workflow** + `motion_styles` library + `check_motion` validator |
| vfx-artist | Effect on its word with build/pop/settle; world-changing effects; kicks | Sections 5, 6, 6b | `fx`, `kicks`, FX.md, Blender recipes | **Director workflow** + **pieces library** + Blender effect recipes (needs build) |
| lighting-director | One key, hard shadows, contact shadow, light clock, colour bands | Sections 3, 5, 6b | `moods`, LOOK_BIBLE light part | **Director workflow** + light/grade presets + `cine_look`/`grade_metrics` validators |
| 3d-designer | Real models and materials, texture detail, wear, bevels | Section 3, material checklist | place .blend, MATERIALS.md | **Blender tool** (materials library + texture tiles) + director decisions |
| look-finisher | Rebuild from lock; four passes; render; look gates | Section 3 stage 2, 6b four passes, section 8 | look scripts, frames | **Blender tool** (executor) |
| editor-compositor | Joins, pacing on the word, captions, final grade, loop | Section 6 joins, 7 | cut, joins.md, grade.json | **FFmpeg tool** + `check_film` validator |
| sound-designer | SFX on every action, ambience, music theme, mix | Sections 6 (+ music theme), mix gates | cues.md, mix.wav | **Sound tool** (`templates/audio`) + cue schema; asset inputs required |
| storyboard-judge | Independent panel scoring, film-level checks, reads pictures the tool cannot | Four-part score, film checks | panel scores, fix list | **Independent reviewer** (the one role whose value is being a separate fresh viewer); run once per gate, not in loops (section 11) |
| studio-director | Final PASS before any approval; Rule 1 and Hard Rule 2; proof page | Rule 1/2, section 7 | proof page | **Independent reviewer** + QA report script; folded with the judge into one fresh-context review role |
| (lead) | Owns `film.json` and LOOK_BIBLE; keeps the look one | everything | decisions | **The director** (you + me) |
STRETCH_BUILDER_BRIEF.txt is a build brief, not a role: it becomes the "one place/act group per stretch" execution mode.

## 6. Ricks mechanism → our system (corrected mapping)
Format: responsibility → Ricks artifact that does it → what we do. "Same" = used unchanged.

| Responsibility | Ricks artifact (evidence) | In the hybrid |
|---|---|---|
| story, script, beats | pitch rules, writer formula, `script_stats` | same |
| words / time anchor | `words.json`, `T(word,n)` | same |
| picture plan | `templates/PICTURE_PLAN.md` | same (no new "entity/socket" column; named things use `props`, anchors, `held3d`, `hand_at` as in Ricks) |
| plan table | `film.json` | same; the only plan schema |
| bake + gates | `tools/film_plan.py` → `camera_baked.json`, `performance_baked.json`, `sound_events.json`, 41 gates | same |
| camera | stations/takes, `follow`, kicks in the bake; `cine.py` rigs (disconnected today) | one baked result; see section 12 |
| characters, views, faces, motion | cast, castkit, motion library, `puppets.mjs`, card PNG sequences | same |
| sets and dressing | `templates/threejs_film/sets/<place>.js` (`build`, `update`, `anchors`) | same; sets are authored in three.js |
| base picture | `film.js` (`render.mjs --storyboard/--animatic/--frames`) incl. light, PBR path, card shade, held3d, highlights, 2D fx, bolt, post (DOF, bloom, dust, vignette) | **final base picture** |
| lock | `render.mjs --export-lock` → `out/lock/` | the immutable boundary; see section 11 |
| Blender | `blender_look/from_lock.py`, `materials.py`, `lights.py`, `scatter.py`, `cine.py` | masked enhancement layers from the lock camera only |
| composite | not found in the package; rule says "composited over the coded frame" | FFmpeg/compositor step (a requirement, see section 19) |
| sound | `sound_events.json` (baked); `templates/audio` | see section 15 |
| QA | `film_plan check`, `frame_checks`, `check_views`, `check_film`, 15 `tools/measure` tools | same, run on the three.js base and on each composited layer |
| lessons | lessons file + library updates | same |

## 7. What stays exactly the same
Everything Ricks owns: script formula; `words.json`; PICTURE_PLAN; `film.json` grammar; `film_plan.py` bake and its 41 gates; camera ideas, stations, `follow`, kicks, cut and arrival rules; cast, outfits, motion library; cards-in-3D principle; three.js sets and the whole three.js look (light, PBR path, post); highlights; held3d; fx timing in `film.json`; lock hash guard; density, material, light and grade numbers; the measured gates and their bands; lessons-into-library; effects, cuts and expressions land on words. Characters get no blur and no ink on the world.

## 8. FINAL ARCHITECTURE — RICKS + THREE.JS + BLENDER HYBRID

```
STORY → SCRIPT/WORDS → PICTURE PLAN → film.json → camera/performance bake → LOCK
      → three.js final base → Blender masked enhancement layers → composite
      → sound / edit / (captions later) → QA → final Shorts MP4
```

### A. Creative layer
Decided by the director and LLM roles: story, script, the one camera idea, three hero moments, picture-plan rows (each named thing CLOSE / IN SCENE / NOT SHOWN with a reason), look choice (palette, light per chapter), which effects the story needs and which Blender layers are worth trying. Output: SCRIPT, beats, PICTURE_PLAN, LOOK notes, CAMERA_NOTE. Nothing here touches coordinates.

### B. Planning layer
`film.json` (cast, places, takes/stations, acts, fx, moods, highlights, props, held3d, hand_at, sound) tied to `words.json`. `film_plan.py` bakes `camera_baked.json`, `performance_baked.json`, `sound_events.json` and runs the gates. Flights (section 13) are declared here, so flight timing is part of the plan before the lock. All "where / when / how big" values originate here or in a set module's anchors, never in a Blender script.

### C. Lock layer
Frozen after the plan passes its gates and the one gate (rough film plus the hook moving) is approved. Contents and rules: section 11. After the lock, layout, camera and timing cannot change; a change means re-plan, re-bake, re-lock.

### D. Three.js final-base layer
Owns the picture of every frame: sets, character cards and their shading, light and shadows, PBR materials for metal/gold/glass, relief, sky, trees, held props, highlights, 2D effect recipes, the lightning bolt, particles, the preview/final post chain (DOF with characters crisp, bloom/halation, dust motes, grain, vignette), transitions, frame timing. Runs on the baked plan only ("owns NO camera maths").

### E. Blender enhancement layer
Owns only masked layers that Blender does better and that clearly improve the base after a before/after: metal reflections that move with the camera, bounce light, lit smoke and haze, light through paper or snow, glints, motion blur on fast fx (never on characters). Each layer renders from the lock camera with a mask and alpha. Not owned by Blender: the base picture, characters, camera authorship, timing, effects the base already does well.

### F. Composite layer
Blender layers (RGBA, same size, same frame numbers, same camera) are combined over the three.js base frames in a compositing step (FFmpeg overlay or a compositor). Rules from Ricks: a layer that makes the frame darker or flatter is dropped; light and brightness stay as finished in the base. The composite step does not exist in the package and is a minimum-new-machinery item.

### G. Sound / edit layer
Sound events come from the baked plan; edit joins and cut-on-word come from baked cut data and FFmpeg. Silent for now by directive; captions later. See section 15.

### H. QA layer
Plan gates → three.js frame checks and film checks on the base → the before/after sheet for each Blender layer (base vs composite, every 0.5 s) → pixel measures on the composite → one independent visual judge per gate. Section 16.

### I. Final output
One vertical Shorts MP4 (frame size and fps follow `camera_baked.json`; Ricks proof shots used 1440×2560), plus the QA report and the lessons update.

### Ownership table (exactly one owner each)
| Responsibility | Owner |
|---|---|
| Story, script, picture plan | Ricks creative workflow (director + LLM) |
| Word times | `words.json` |
| All timing | `film.json` / baked plan |
| Flight timetable (leave, hit, from, to) | `film.json` (plan), before lock |
| Character performance | Ricks cast + motion library |
| Character pixels (cards) | Ricks card pipeline run by three.js |
| Base camera (the only camera result) | `camera_baked.json` from the bake |
| Camera authoring (stations, follow, and later rigs) | plan side, inside the bake |
| Sets, dressing, light, base materials | three.js set modules and `film.js` |
| Base effects (flash, dust, impact, bolt, highlights) | three.js |
| Base picture | three.js |
| Lock | `render.mjs --export-lock` |
| Enhancement layers | Blender via `from_lock` |
| Composite | compositor/FFmpeg step |
| Sound events | baked plan; mixing by the sound pipeline |
| Final QA | Ricks gates + independent judge |

**Design problems flagged (two owners today):**
1. Camera: the bake writes `camera_baked.json`, while `cine.Shot.bake()` writes its own Blender keyframes. One must feed the other (section 12).
2. Effect timing: `film.json fx` times a 2D drawing in three.js and has no Blender counterpart; a Blender layer must read the same entry, not carry its own timing.
3. Light: three.js light per place and `blender_look/lights.py` presets are two light descriptions; Blender layers use the lock's per-place `lights` (unconsumed in the package today) and must not add a second key.
4. Flight: today a flight is a set-module timetable (`fly_and_hit`) in three.js and a `cine` object path in Blender; section 13.

## 9. What changes relative to Ricks as shipped
1. Blender is added after the lock as masked layers; Ricks' own newest rule, not a new idea.
2. The one-camera rule is made explicit (section 12).
3. The flight bridge and the composite step are added (sections 13, 19).
4. Audio is separated into reusable and film-specific parts (section 15).
5. Reference board: Ricks asks 2–4 frames per beat and makes it a hard gate. **Amended by blueprint D-2 (2026-11-23): reference material is mandatory creative input before lock and an answer key for QA afterwards; it is not a render-time dependency.** (The earlier wording here, "the pipeline never reads the reference video", is withdrawn.) Measured bands (`gates_film.json`) and approved stills remain quality targets.
6. Render machine is Colab T4 for Blender layers; the three.js base on CPU SwiftShader runs ~1 s/frame at half size here (measured), GPU speed unmeasured.
7. Silent video and no captions for now.

## 10. What is not carried over
Remotion/`rick-shorts/src`, Windows/OneDrive/PC-link plumbing, RunPod and RTX 2070 notes, `toon.ts` legacy, Bridge-film audio timeline/music/cues, episode-specific scripts except as examples, STYLE_BIBLE ink-on-world. **Not removed:** three.js sets, `film.js`, the lock export and its glb path, `render_gpu.mjs` (v1 wrongly removed these).

## 11. Lock
- **Meaning (code):** the hand-off snapshot written by `--export-lock`: set `.glb` at frame 0 with `mat:` names and base colours, per-frame `motion/<place>.json` for moving set nodes, card PNG sequences with `index.json`, per-place `lights`, `highlights.json`, `instances.json`, `overlay`, and the sha1 of `camera_baked.json` and `performance_baked.json`.
- **Immutable after lock:** layout, camera, timing, performance, effect times. The sha1 guard makes `from_lock` refuse a changed plan.
- **Consumed by `from_lock` in the supplied package:** sha1, cards, fps, baked camera frames, the glb. **Unconsumed in supplied package:** `lights`, `motion`, `highlights`, `instances`, `overlay`. They may have been used by episode look scripts we do not have; they are not declared dead.
- **Known loss at the lock** (Ricks' "never weaker" list): held props, canvas-painted faces, sky details, objects hidden at frame 0, instanced part colours, vertex-painted ground, painted word planes. In the hybrid this matters only where a Blender layer needs that object (for example a mask or a reflection); the base picture keeps them because it never goes through the glb.
- **Before the lock:** flight descriptions, effect times, camera intent. **After:** Blender layer recipes and composite settings only.

## 12. Camera ownership
- **One authoritative result:** `camera_baked.json` (fields: f, kick, take, place, backdrop, station, state, cut, pos, aim, up, roll, lens, fov_v, subject, framing, shows). three.js, the gates, `frame_checks` and `from_lock` all read it.
- **Today's evidence:** the bake already authors one dynamic camera, `follow` (a character's baked position added to pos and aim; executed test). `cine.py` (paths, rigs, `Shot.eval`, `Shot.bake`) is not called by anything and is not linked to `film.json`.
- **Target (conceptual, from the director):** camera intent/rig → `Shot.eval(frame)` → `camera_baked` → lock → `from_lock` → one Blender camera. `Shot.bake()` keyframing the Blender camera directly is not used in production, so it cannot compete.
- **Not decided (evidence does not settle it):** where the rig call lives inside the bake; how `cine`'s quaternion kick/roll is reduced to the plan's roll plus aim-z; whether `up` is consumed.
- Owner of any camera change: the plan side only.

## 13. Moving objects and flights (requirement, not designed)
- **Evidence:** `fly_and_hit.js` is a timetable of leave and hit frames, from (a real muzzle or hand point) and to (where it sticks), applied by the set module; `film.js` anchors may be functions of the frame; `cine.py` has `object_path`, `ballistic_path`, `mix_path`; `follow` is characters only.
- **Decision (Option B, confirmed):** the object's timing lives in the plan before the lock because it fixes object position, camera, hit frame and effect time; three.js proves it cheaply; any Blender enhancement of the flight (glint, trail light, motion blur) reads the same data.
- **Requirement:** one small shared flight description read by the plan, the set module and Blender. Its shape is not designed here. It must use Ricks' hand/muzzle/anchor points (no sockets) and must not become a second planning schema.

## 14. Effects
| Class | Items | Status |
|---|---|---|
| **Proven in three.js** (code) | impact (clank/knock/stamp/kick: 5-frame flash, ring, sparks, dust), steam/dust/puff/smoke/whistle with counted bursts, glint with one anamorphic streak, grinding sparks, sound rings, sweat/drop/ink, paper, highlights (object tint + additive glow), lamp bloom, `kicks` (7 frames, alternating sign, in the bake), lightning bolt (`fx_bolt.mjs`, 3D with flash lights), post (DOF, bloom, dust, vignette), `time_pass`, `highlight_part`, `burst_of_living_things` (names seen in pieces; proofs not run: `episodes/` missing) |
| **Blender enhancement candidates** (rules, not yet implemented) | metal reflections, bounce light, lit smoke/haze, light through paper or snow, glints, motion blur on fast fx. Blender already has helpers for sky, sun, practical, air, mist, cloud, moon; they are lights and volumes, not effect recipes |
| **Genuinely missing** | any Blender effect recipe; projectile trail (not found anywhere); the Blender mask/alpha export; the composite; a flight-linked effect timing |
Rules: effect timing stays in `film.json fx`; the 2D three.js version is the timing proof; Blender replaces or adds to it only as a layer that passed before/after; an effect that is the star of the story is proven alone first (CB_RULES hero-effect rule).

## 15. Audio
- **Reusable:** `dsp.py` (filters, loudness meter, limiter), `instruments.py`, `sfx_gen.py` (synthesis).
- **Film-specific, not reusable as a system:** `timeline.py` (mirrors a Remotion `story.ts`), `music.py` (one composed march), `sfx.py` (cue list), `mix.py` (wired to that timeline's duration).
- **Missing:** any reader of `sound_events.json`; the sample library index and folders.
- Silent for now; when sound starts, it is built from `sound_events.json` + the reusable DSP, and the old film-specific files are examples only.

## 16. QA
- **Plan:** `script_stats`, `film_plan check` (41 gates).
- **Frame (three.js base):** `frame_checks` (needs `--software` on CPU), `check_views`, `density_check`, `detail_density`.
- **Film:** `check_film`, `film_motion`, `cam_track`, `cine_look`, `grade_metrics`, `check_episode`.
- **Layer:** before/after sheet against the base every 0.5 s for each Blender layer; keep only if it adds, never darker or flatter; characters never blurred.
- **Composite:** the same pixel measures on the final MP4; line-check sheet per PICTURE_PLAN row; sound-off test later.
- **Judge:** one independent visual judge per gate; failures fix the plan row, library or recipe, never a per-shot coordinate.
- Plan checks + frame checks + film checks + independent judgement (Ricks' philosophy) unchanged.

## 17. Final rendering
three.js base frames (`--frames`) → Blender layer frames from the lock camera (EEVEE, Colab T4) → composite → FFmpeg encode, grade guards, loop check → sound later → QA → MP4. Slowest frame first. Measured: three.js animatic ~1 s/frame half size on CPU here; Blender Pass A round 214 s on T4 (different scene). Layer cost on T4: not measured.

## 18. DO NOT BUILD
New camera engine; new Blender executor (`from_lock` exists); new character renderer; replacement three.js look system; complete Blender copy of Ricks effects or materials; sockets (use hand/muzzle/anchor); manual per-shot Python as the normal workflow; a second planning schema beside `film.json`; duplicate validators where a Ricks tool exists; Blender-only planning or preview loops; reference-video reading inside the pipeline.

## 19. MINIMUM NEW MACHINERY (only what the evidence shows missing)
1. **Flight bridge:** one shared flight description before the lock (requirement; not designed).
2. **Camera link:** film.json camera intent/rig evaluated inside the bake through `Shot.eval` (only if a story needs a moving-object camera; `follow` and stations cover the rest).
3. **Blender layer export:** masked RGBA layer frames from `from_lock`, with the mask source defined per layer.
4. **Composite step:** layers over base, with before/after sheet output.
5. **Effect recipes in Blender:** only for layers that pass a proof; projectile trail light is the first known gap.
6. **Reader for the lock fields a layer needs** (`lights`, `motion`, possibly `highlights`), only when a layer needs one.
7. **Missing data/files:** `tex`, `look_locked`, view PNGs, `episodes/` proofs, `rules/dept`, sample folders.
Everything else is Ricks as shipped.

## 20. Implementation order
- **PHASE 0 — evidence/spec freeze:** this document and the evidence notes; no code.
- **PHASE 1 — minimal hybrid proof:** one tiny shot (not a video): `film_example` frames from three.js, lock, one Blender layer through `from_lock`, composite, before/after sheet. Proves the seam and measures T4 layer cost.
- **PHASE 2 — moving-object flight bridge:** design the shared flight description and the camera link; prove on one projectile shot in three.js, then Blender.
- **PHASE 3 — Blender enhancement layers:** add layers one at a time (metal reflection, bounce, lit smoke, glint, motion blur), each with its before/after.
- **PHASE 4 — automated QA:** before/after sheet generation, composite measures, line-check sheet.
- **PHASE 5 — Western / our channel integration:** only after Phases 1–4; the Western is the first content, using Ricks cast and our `kit/` as dressing input to three.js sets.
- **PHASE 6 — production automation:** Colab runner, usage/time meter, sound.
Do not jump to Phase 5.

## 21. What is proven (evidence notes)
Plan bake and gates; `follow`; three.js storyboard, animatic, visibility, lock; `from_lock` rebuild of camera, cards, set, materials; measure tools; Colab T4 round (214 s, Pass A). Not re-run: pieces proofs (`episodes/` absent), audio, `cine.py` (no bpy locally).

## 22. Remaining unknowns
- Whether a Blender layer from the lock camera registers pixel-exactly over the three.js frame (field of view, aspect, card pivots).
- Layer cost on Colab T4 and three.js frame time on GPU.
- Which lock fields any layer needs; how a mask is produced for each.
- How the rig evaluation sits in the bake and how kick/roll map.
- Flight description shape.
- Contents of the missing episode look scripts, `episodes/`, `tex`, `look_locked`, sample folders.
- `pip install bpy` is not permitted locally; Blender runs only on Colab.

## 23. Reference example (flow only; illustrative, unmeasured)
Short "The Barber Who Cut the Queue", 12 s:
1. Script and beats; 2. voice → `words.json`; 3. PICTURE_PLAN rows with the named things (razor, queue, FREE sign); 4. `film.json` (camera idea, cast, places, takes on word anchors, acts, fx, moods, sound) → `film_plan check` → baked files; 5. three.js sets and hero chair, density gate; 6. three.js storyboard then animatic, the one gate; 7. lock; 8. three.js final base frames; 9. one Blender layer (for example warm lamp bounce on the chair metal) from the lock camera, before/after against the base, kept or dropped; 10. composite; 11. QA gates; 12. approval; 13. encode; sound later.
