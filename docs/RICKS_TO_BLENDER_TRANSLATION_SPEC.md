# RICKS → BLENDER PRODUCTION TRANSLATION SPECIFICATION

Date 2026-11-21. Branch `ricks-2d-core`. Specification only: no code, no validators, no resolver, no render, no Pass A fix.

## 0. How this was produced, and its limits
Read in full: `WORKFLOW.md`, `FILE_GUIDE.md`, `templates/PICTURE_PLAN.md`, `film_plan.py` header, `film_example/film.json` keys, `threejs_film/README.md`, `CINEMATOGRAPHY.md` headings and shot table, `DENSITY_RULES.md` headings, the SKILL.md stage and crew tables, and CB_RULES sections 6 and 11 plus the Camera director and Sound brief bodies.
Read as a skim (first ~200 characters of every rule line): CB_RULES sections 3, 4, 5, 7, 8, 9, 10, and the "What you own / Inputs / Outputs / Gate" block of all 16 agent briefs.
Not read line by line: the remaining ~20,000 words of CB_RULES detail, the 20 pitfall notes (titles only), `blender_look` code, `cine.py` code, `templates/audio` code beyond headers, every individual pieces file.
Everything below that says "Ricks proves/claims" is Ricks' own record. I have not re-run it in our environment. "CB" in Ricks files is the Ricks project owner; I treat his rules as the methodology.
Conflict I found inside Ricks (flag, not decided): the newest rule wins inside CB_RULES. STYLE_BIBLE (older) says ink outlines on 3D geometry; CB_RULES says no ink on the world, ink on characters only. STYLE_BIBLE says captions; your standing rule is silent for now. CB_RULES section 11 says a Blender layer is optional (it cost ~80 M tokens and 6 h) while your product decision is that Blender is the environment. Section 8 below resolves each of these explicitly so nothing is lost silently.

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
| props-hero | Hero object first; held props; build steps | Section 3 premium detail; BlenderKit | props .glb, PROPS.md | **Asset library with sockets** + director decisions per story |
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
Parallel agents (one per place, sound beside render) are an execution option driven by cost and by there being one GPU, not a creative necessity.

## 6. Ricks → Blender mapping (the requested checklist)
Format: Ricks mechanism → Blender equivalent → reuse → preserve → change → drop.

| Item | Ricks mechanism | Blender equivalent | Reuse | Must preserve | Changes in Blender | Drop |
|---|---|---|---|---|---|---|
| story | pitch 3, facts | same, director | direct | true story, mocker, twist, places+lights named | none | none |
| script | writer formula, `script_stats` | same | direct | hook, pivot ~67 %, loop, mood tags | none | none |
| beats | beat list with seconds | same | direct | hero moments (hook/turn/payoff) | none | none |
| picture plan | PICTURE_PLAN.md rows | same | direct (template exists) | one row per named thing, CLOSE/IN SCENE/NOT SHOWN with reason, feeling, effect, piece | add "entities/sockets" column (what persists across shots) | none |
| cinematography | camera_idea, stations, rigs, laws | film.json takes baked to camera, executed by `cine.py` rigs in Blender | direct (`film_plan.py`, `cine.py` are pure Python/Blender) | one idea, 3 hero moments, rest/travel rhythm, arrival 5 frames before word, no teleport | camera comes from `camera_baked.json` inside Blender, not three.js | three.js camera preview |
| shot planning | film.json + check | same | direct | 37–42 gates | none | none |
| character selection | `cast:<name>`, 150 characters, outfit lib | same | direct | v12 template, 3 sizes, signature detail | none | none |
| character views | front/3-4/side/back PNG states | card images from the same package | direct | one view per character, view follows camera | cards are exported per state and placed in Blender | none |
| expressions | step face changes on the word, head pop | `acts[].face` → card image swap on the frame | direct | change ON the word, one frame, calm start | frame-accurate swap in Blender timeline | none |
| body forms | 3 sizes + presets | same | direct | identity preserved, performance varies | none | none |
| animation/moves | motion library A/B/C, studio timing, drawn new each frame | same; Node draws PNG sequences; Blender plays them | direct | notice-anticipate-strike-settle-dead still; planted feet; hands end on objects | contact anchors must be expressed in Blender space (card hand/foot offsets from `cards/meta.json`) | none |
| props | hero first, real parts, held at the hand | Blender models + sockets on the character cards | partly (hero models via Blender/BlenderKit; held props via hand offset) | real parts, story lettering, marks | built in Blender per story | `aircraft.py` specifics |
| environment | three.js set + DRESSING list → Blender dressing | Blender set recipe built per story (Stage A / B of "full Blender world") | **new implementation** (our `kit/` is a first content instance) | 5–8 places, one connected world, hero first, density gates, five details, no empty sky/end of world | sets live in Blender; three.js set code not used | `sets/*.js`, three.js lock export |
| composition | framing letters W/M/C/P/O, head 45 % height, caption band, foreground big thing | shot-size → camera solver using frame math from the baked plan | direct rules, **new** solver for Blender | heads out of 58–76 % band, nothing cut | none | none |
| camera | stations + rigs | `cine.py` | direct | see cinematography | none | none |
| lighting | one key, hard shadows, contact shadow, light clock | `lights.py` + presets + world sky in Blender | partly (code exists) | key you can see, long shadows, contact patch, face white, light per chapter | light is designed in Blender, not "kept from the coded frame" (section 8) | "coded vs Blender pair" |
| materials | `materials.py` library + `tex` tiles + 3d-designer checklist | same, needs `tex` copied | direct | roughness variation, wear, bevels, lettering | none | none |
| VFX | pieces + fx entries; flat sprites in three.js, real light/smoke in Blender | Blender effect recipes: emission cards, volume, particles, compositor glare | **new implementation** for Blender | effect on the word, build/pop/settle, real light, SFX cue | per piece a Blender recipe | three.js sprite versions |
| density | 30+ kinds, 600+ objects, clusters, 3 place details, 2 moving things | recipe gate + `density_check` + scatter | direct | all numbers | measured on Blender frames | none |
| visual rhythm | rests ~3 per 10 s, 3–6 long journeys, camera moving ~68–100 % | plan gates | direct | numbers | none | none |
| sound | `sound_events.json`, audio engine, library samples, mix -14/-15 LUFS | same engine; cues come from baked plan | direct engine; **inputs missing** (sample folders) | SFX per action, ambience, music theme, loop | none | synthetic stand-ins when library exists |
| editing | joins by move or 6–14 frame blend, cut on the word | FFmpeg xfade + baked cut times | direct | rules | none | none |
| transitions | next scene seen inside an object, whip, blend | cine.py hand-off + FFmpeg blend | direct | "no teleport" | none | none |
| QA | `check_film`, `check_episode`, `cine_look`, `frame_checks`, 16-frame, line-check sheet | same tools on Blender frames | mostly direct | numbers first | run on EEVEE outputs | judge loops before the gate |
| gates | list in section 18 | same | direct | all that protect quality | none | stale ones (`old-gates-punish-no-ink`) |
| final rendering | EEVEE 64 samples 1440×2560 local RTX 2070 | EEVEE on Colab T4 | adapt | slowest frame first | resolution/samples set by time budget | RunPod/local GPU notes |
| post | grade by light kind, guards for reds/faces | `grade.py` + FFmpeg | direct | guards | none | none |

## 7. What stays exactly the same
Script formula; words.json anchoring; PICTURE_PLAN; film.json schema and `film_plan.py` baking and gates; camera ideas, hero moments, rest/travel laws; cast package, views, outfits, motion library and its checks; the cards-in-3D principle (flat 2D puppets in a real 3D world); density, material, light and grade rules and numbers; sound rules and mix gates; the numbers-before-pictures and fresh-helper-per-round token rules; lessons-into-library; the rule that effects, cuts and expressions land on words.

## 8. What changes for Blender
1. **Scene authoring moves from three.js sets to Blender sets** (Ricks' own "full Blender world" order). Layout, camera and timing are still decided in `film.json` and baked; Blender reads the baked files directly (they are pure Python by design).
2. **No coded frame to "keep" light from**: the rule "light is finished in the coded storyboard and Blender keeps it" has no meaning. Its intent (light never weaker, stable, readable, face white) is preserved by the Rick-measured bands in `grade_metrics`/`cine_look` and by a light preset chosen per chapter from LOOK_BIBLE.
3. **Preview/animatic**: Ricks plays the whole film in three.js in minutes. Blender equivalent is a low-resolution EEVEE (or Workbench) animatic and START/END stills of each station, rendered on Colab (I measured ~50 s for a 14 s preview). This is a real behavioural difference and the biggest cost question.
4. **Visibility/projection checks** (`--visibility`, `proj.py`) are projection maths: in Blender they use camera projection of real objects and named anchors, so they can also test bullets, sockets and paths.
5. **Effects** become real Blender light/volume/particle recipes instead of 2D sprites over three.js.
6. **Render machine** is Colab T4, not a local RTX 2070 Super or RunPod; time and sample budgets change; measured cost report replaces tokens-only reporting.
7. **"Blender is optional" (section 11)** versus your decision that Blender is the environment: preserved by treating its cost warning (80 M tokens, 6 h; only where it earns its place) as a budget gate with the usage meter, not as a ban.
8. **Captions** off for now by your rule; the caption spec stays for later.
9. **Reference board**: Ricks requires 2–4 reference frames per beat. Your rule says the reference video is an answer key that the pipeline never reads. Preserved intent: quality targets come from the already measured bands (`gates_film.json`, `look_locked` approved stills), not from per-video frames.

## 9. What is removed because it is technology-specific
`rick-shorts/src` and Remotion bridge; three.js set code and `render_gpu.mjs` / GPU_RENDER; `--export-lock` glb path for sets (cards path stays); Windows/OneDrive/PC-link/`%USERPROFILE%` plumbing; "every thread links the PC"; RunPod notes; RTX 2070 specifics; `toon.ts` legacy; episode-specific code (Bridge sound timeline, armor grade scripts, Po-2 aircraft model) except as worked examples; `_pbr_test`; the older STYLE_BIBLE statements superseded by CB_RULES (ink on world). Not removed: all rules that those pieces enforced. Judge loops on still pictures as a pre-gate loop are already retired by Ricks section 11.

## 10. What new Blender implementation is required (needs, not code)
1. Executor that reads `camera_baked`, `performance_baked`, `sound_events` and places cards and cameras (`from_lock` does part of this for locked three.js sets; its card path is reusable).
2. Set builder from recipes (Stage A density + Stage B materials) in Blender, per place, with hero object first.
3. Sockets/anchors on characters and props so paths and effects bind to named points.
4. Effect recipes per piece (muzzle flash, impact, dust, glint, smoke trail, ground crack).
5. Blender-side visibility/projection report and the line-check sheet (frames at each PICTURE_PLAN row).
6. Low-res animatic and start/end station stills.
7. Colab runner with usage meter (exists).
8. Missing files copied to the branch: `blender_look/tex`, `look_locked`, 80 views, `frame_checks`, `rules/dept`.

## 11. Character pipeline
Cast selection from the 150-cast / bible sizes / 500 outfits / 74 hairs / 34 hats / face gear → `film.json cast` with outfit colours taken from the scene palette → four locked views → per-act pose, face, view, prop in hand drawn by Node into PNG states (drawn new every frame) → cards at real height with hand/foot offsets → Blender cards (self-lit face white, edge shadow, own-colour floor, shadow pass, contact patch). Checks: `check_views`, signature detail, 16-frame check, silhouette test.

## 12. Environment pipeline
Hero object first → set recipe for each of 5–8 places (one connected world, same landmarks from other sides) → density gate (30+ kinds, 600+ objects, clusters, five specific details per object, two moving things per shot) → micro motion and air life → sky and haze depth layers (≥3 layers) → story lettering → materials from library + `tex` → light preset per chapter. Checks: `density_check`, `detail_density`, no camera station inside geometry, no open side.

## 13. Camera/cinematography pipeline
Camera idea (five candidates scored) → three hero moments → flow plan → stations/takes in `film.json` → `film_plan check` → baked camera → Blender cameras via `cine.py` rigs (chase, mount, orbit, catch, push, static, hand-off with blend 14–30 frames) → motion blur on travels only → measured with `film_motion` and `cine_look`. Projectile rule: object path plus chase or mount camera; impact 0–3 frames before the word; flash ≤2 frames; track ~30 % of frames.

## 14. Animation/action pipeline
Action chosen from motion library by action+feeling+energy+character → `acts` anchored to word frames → drawn by Node → Blender plays PNG sequences; things that go in/on/at something fly there and hit; hand ends on object; planted feet; no teleport/morph; one action or one feeling per beat. Checks: `check_motion` (0 twos, 0 linear, settles), line-check sheet.

## 15. Lighting/material pipeline
LOOK_BIBLE per film (palette, light per chapter, contact shadow, grade) → light preset (`lights.py`: night, morning, midday, golden, interior) → key light, hard shadows, practical lights, haze → materials from library (roughness variation, wear, bevels, lettering) → grade last with guards. Checks: `cine_look`, `grade_metrics` (saturation 0.40–0.50, mean brightness 0.42–0.50, darkest 1 % 0.08–0.15), feet zoom.

## 16. VFX pipeline
Per key word: effect design (wind-up, hit frame, glow, kick, settle) from the pieces library → `fx`/`kicks` in film.json with SFX name → Blender recipe (emission, volume smoke, particles, compositor glare) → checked at speed and frame by frame, at 360 px width, beside a reference.

## 17. Sound/editing pipeline
`sound_events.json` from word anchors → library samples first (then synthetic only if none) → music theme stated/changed/returned → mix under voice (duck ~13 dB, measured gaps, -14/-15 LUFS, true peak) → editor joins (move or 6–14 frame blend, cut on the word) → final grade → captions later → loop check.

## 18. QA and quality gates
Plan: `script_stats`, `film_plan check`. Preflight (new): pitfall checks, scene sanity. Frame: `frame_checks` (head cut, set between camera and face, feet floating), `density_check`, `detail_density`, `look_3d`/`cine_look`, `grade_metrics`. Film: `check_film`, `film_motion`, `check_episode`. Cross-checks: line-check sheet per PICTURE_PLAN row, 16-frame check, random-frame check, sound-off test. Human gates: the one gate (rough film + hook moving), look approval (one still per place + one clip), final. Independent reviewer once per gate. `short_qa`, proof page, token/usage report.

## 19. Rendering pipeline
Lock plan → slowest frame of each place first → render all frames in parallel chunks, one GPU job at a time → FFmpeg encode → `check_film` and `cine_look` on mp4. Our machine: EEVEE on Colab T4 (measured 214 s for the 14 s Pass A test round; 11–12 min final quality is an estimate).

## 20. Final end-to-end architecture (summary)
script → words.json → PICTURE_PLAN → film.json (+ LOOK_BIBLE, cast, places, props, acts, fx, moods, sound) → `film_plan check` → baked plan → [Node: cards] + [Blender: sets, props, lights, cameras, effects from recipes and libraries] → low-res animatic + station stills → numeric gates → independent review → approval → final EEVEE render → FFmpeg → sound → grade/loop/QA → delivery → lessons back into libraries.

## 21. What we already have and have proven
Proven here: Ricks puppets as cards in Blender with multi-character cards; a Western set recipe (48 kinds, 884 objects, density gate met on Colab round 5); per-shot camera framing by my own maths; dissolves and Ricks grade on Colab; usage meter and timing (214 s round); plan compile+validate chain (my own, not the Ricks one).
On the branch from Ricks (claimed proven by Ricks, not re-run by me): `rig.mjs`, castkit, sheet05, moves, `film_plan.py`, `cine.py`, pieces + proofs, look package, audio engine, `fish_tts.py`, pitfall library, picture-plan template, 419 of 851 files.

## 22. What is actually missing
`tex`, `look_locked`, 80 view PNGs, `frame_checks`, `rules/dept` not on the branch; sockets/anchors; Blender effect recipes; Blender animatic and station stills; Blender visibility/projection report; line-check sheet; film.json-driven Blender executor (we ran my own intent format); picture plan and CAMERA_NOTE for any film; SFX sample folder and music folder; Fish key or alternative voice route; local `bpy` (permission) for no-Colab checks; per-place LOOK_BIBLE.

## 23. What should be built first (order by dependency, not by size)
1. Copy missing Ricks assets (data, no code).
2. Run Ricks' own tools unchanged on `film_example/film.json` (`film_plan check`) and the pieces proofs, to confirm they work in our environment.
3. Executor that reads `film.json`/baked plan into Blender (cards + `cine.py` cameras), proven on the Ricks example film before any Western.
4. Sockets for the cast and a Blender recipe for one projectile piece (the reason Pass A failed).
5. Blender animatic/station stills and the line-check sheet.
6. Set recipe from the existing `kit/` as the first content instance.
7. Sound last, once the sample folder exists.

## 24. What should NOT be built
A new plan format (use `film.json`); new camera maths (use `cine.py` and `film_plan`); another validator where a Ricks tool exists; per-video tuning scripts; a second scene backend authored in parallel; fluid sims; custom sound timelines per film; a crew-of-agents harness; reference-reading inside the pipeline; anything not first traced against a Ricks file (T8: nothing built twice).

---

# End-to-end example (illustrative values, not measured, not Pass A)
Short: "The Barber Who Cut the Queue" (12 s, 3 voiced lines). Purpose: show how information flows; numbers are examples.

**1. Script + beats** (`SCRIPT.md`): L1 "A BARBER shaved one man and the whole town LINED up." (0–3.6 s, hook, mood amused) · L2 "He gave every HAIRCUT for free, and the line got LONGER." (3.6–8 s) · L3 "You see, the free cut was the ADVERTISING." (8–12 s, twist, loop to frame 0).
**2. Voice** → `words.json`: `barber` 0.5 s, `lined` 2.9 s, `haircut` 4.4 s, `longer` 7.0 s, `advertising` 11.0 s.
**3. PICTURE_PLAN.md** rows (excerpt): #1 HOOK "BARBER" 0.5 s: barber with razor and one customer, IN SCENE wide, the town's size is the joke; #2 "LINED up" 2.9 s: whole street queue behind the chair, IN SCENE; #3 "HAIRCUT" 4.4 s: scissors snip, CLOSE (it is the claim), effect: hair clippings fly (piece `fly_and_hit` adapted); #5 TWIST "ADVERTISING" 11.0 s: sign painted "FREE" seen from the street. Entity column: `razor`, `queue`, `FREE sign`.
**4. film.json**: `camera_idea` "The queue is the path" (camera tracks along the queue); `cast` barber (standard size, apron), customer, 4 queue extras; `places` shop, street; `takes` stations on word anchors (`barber` at 0 lead 5, `lined` ...), `acts` (barber `snip` move on `haircut`, face `smug`), `fx` (clippings on `haircut`), `moods` (warm morning → golden at twist), `sound` (snip, crowd murmur). `film_plan check`: 0 FAIL, one WARN kept with a reason in `CAMERA_NOTE.md`. Output: baked camera, performance, sound events.
**5. Assets**: cast from Ricks package; hero object (barber chair, real parts); set recipe "main street, morning" with density gate; sky/haze preset; `FREE` sign lettering for this story; materials from library + tiles.
**6. Blender scene**: executor reads baked files: places sets, imports cards, creates cameras from `cine.py` rigs, attaches the `snip` effect to a socket on the scissors, applies the golden light preset at the twist.
**7. Animation**: Node draws card PNGs for each act; Blender plays them on the baked frames; face swaps on `barber`, `haircut`.
**8. Camera**: chase rig along the queue between words 2 and 3; rest on the barber's face at `haircut`; push-in to hands; arrival 5 frames before each word.
**9. Lighting**: morning key, long shadows, contact patches, warm lamp in shop; golden at twist; face white.
**10. Preview**: low-res animatic + start/end stills per station on Colab; line-check sheet (a strip per PICTURE_PLAN row).
**11. QA**: plan gates (done), frame checks (head cut, feet, geometry between lens and face), density, `cine_look`, grade bands, every row visible on its word, usage meter. Independent reviewer reads the plan against the script and one small sheet. Failures fix the library, recipe or plan row, not a shot coordinate.
**12. Approval** by you (the one gate).
**13. Final render**: EEVEE slowest frame first, then all, chunked; FFmpeg joins, grade, loop check; sound mixed to -14 LUFS from sound events; deliver with the lessons file updated.
