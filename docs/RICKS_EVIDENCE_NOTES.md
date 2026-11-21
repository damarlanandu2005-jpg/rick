# Ricks evidence notes (2026-11-21)
Method: Ricks tools run UNCHANGED, on a scratch copy of `templates/film_example` in /tmp (nothing in the repo modified). Machine: 2 CPU cores, no GPU, Node 22, Python 3.13, ffmpeg 6.1.1, Playwright Chromium on SwiftShader (CPU WebGL). No Blender here. Everything below is MEASURED unless marked READ (read in code, not run) or NOT TESTED.

## A. What ran, and what it showed
| Ricks component | Command | Result | Time |
|---|---|---|---|
| Plan baking + gates | `tools/film_plan.py check film.json` | 0 FAIL, 1 WARN of 41 gates; wrote camera_baked, performance_baked, sound_events, plan_report | 0.23 s |
| Storyboard (START/END of every station, caption on) | `render.mjs film.json --storyboard` | 10 stations, 20 panels, real puppets in a real 3D toon platform; camera, move, word strip per panel | 18.6 s |
| Visibility | `--visibility` | ran, wrote visibility.json | 1.5 s |
| Lock export | `--export-lock` | out/lock: sets/platform.glb, cards (3 characters), lock.json (with sha1), instances, highlights, motion; 13 MB | 31 s |
| Animatic (460 frames, half size, silent) | `--animatic` | mp4 produced | 7 min 57 s = 1,035 ms/frame on 2 CPUs (a 60 s film would be about 31 min) |
| Film gates on the animatic | `tools/check_film.py animatic.mp4 --film film.json` | **2 FAIL of 21**: rests per 10 s 5.88 (target 2.2–3.8), travel p90 1.13 s (target 2.1–6.3). Plan check passed the same film; cause not investigated | 6.3 s |
| Frame checks | `tools/frame_checks/check.mjs film.json --software` | 1 FAIL, 1 WARN, 77 PASS: lady's head cut by the top edge at f151–162 (visible in the storyboard, panel 4) and kid cut by the right edge for 3 frames | 4.3 s |
| Character view guard | `tools/check_views.mjs` | PASS (4 characters × 4 views); some SKIPs for episode sheets not delivered | 4.3 s |
| Pieces code | `import fx/fly_and_hit.js`, `timetable([single f100])` | runs: leave 100, hit 105 | instant |
| Audio engine | `import dsp, sfx_gen, instruments` | imports; NOT run end to end |
| Pieces proofs | `prove.mjs`, `prove_fx.mjs` | **cannot run**: they compare against original armor-film episode files (`episodes/armor-no-holes/...`) which are not in any of the three zips |

## B. Findings that change the picture
1. **The Blender executor already exists.** `templates/blender_look/from_lock.py` (READ): builds the camera from `camera_baked.json` one key per frame (vertical fov, DOF focus on the subject's card), places one card plane per character with the drawing swapped per frame from `index.json`, imports the locked set `.glb` and swaps every `mat:<tag>` material for the library material of that name, computes `keep_clear` discs for dressing, and refuses to run if the plan changed after the lock (sha1). Our Pass A used only a fragment (`from_lock.card`). My spec's "new executor required" (section 10 item 1) was wrong.
2. **Attachment is solved by hand points, not new sockets.** `pieces/fx/fly_and_hit.js` (READ): "from = the muzzle point in a real hand, on the frame the hand fires; to = where it sticks"; a timetable gives leave and hit frames; the piece is "technique as numbers, no three.js", applied by the set module. `cards/meta.json` hand offsets exist. So "sockets" were my invention.
3. **Set authoring in Ricks is a small three.js module per place** (`sets/platform.js` is 50 lines for the demo) tagged with `mat:` names that Blender converts. Blender then adds materials, light, air and dressing (`scatter` with keep-clear). Our `kit/` (set recipe + scatter + density gate) therefore fits as the Blender dressing stage on top of a simple locked layout, not as a replacement for the layout stage.
4. **The cheap loop works here with no GPU**: planning (0.2 s), storyboard (19 s), visibility (1.5 s), frame checks (4 s), lock (31 s). Only the full animatic is slow here (about 1 s/frame).
5. **The checkers find real defects.** frame_checks caught a cut head in Ricks' own demo in 4 s. check_film disagrees with plan check on two numbers: the gates are not interchangeable and the example is not clean.
6. **Pitfall notes (4 read)** are concrete pre-flight tests that Ricks mostly already bakes into the plan or the checkers (e.g. keys mean *arrive* with `lead` 5 frames; horizontal fov in 9:16 is narrow, stage in depth; stale camera near/far; body inside furniture = `body_in_mesh` check).
7. **Blender 5.x compatibility (READ, not run):** `from_lock.py` already handles layered actions (4.4+/5.x) with a `fcurves` fallback and uses `surface_render_method` with a fallback. `cine.py` guards `action.fcurves` with `hasattr`, so on 5.x the interpolation-fix block is silently skipped (effect on easing unknown until run in Blender). `blender_look` ran on Colab 5.2.4 in our rounds (look, grade, lights, scatter, from_lock.card). `cine.py` has not run in our Blender.
8. **Effects**: `film.json` `fx` play as placeholder rings in three.js; the real effect is look-pass work in Blender from `FX.md` recipes. Blender effect recipes remain a genuine gap; timing numbers come from the pieces.

## C. Missing from the three zips (therefore not on the branch)
`episodes/` entirely (armor film, goldrush, roller coaster… sets, cast sheets, build scripts); `templates/motion_styles/check_motion.mjs`; `rules/dept/*`; `library/blenderkit/`; plus previously noted `blender_look/tex`, `references/look_locked`, 80 view PNGs. Consequence: the pieces' proofs and several rules' "worked examples" cannot be re-checked.

## D. Still NOT inspected
About 20,000 words of CB_RULES (sections 3–10 only skimmed), the other 16 pitfall notes, `materials.py`/`lights.py`/`grade.py`/`scatter.py` internals, `cine.py` beyond its header and bake code, `camera_pieces.json`, `film_page.html`/`film.js` internals, the audio timeline/mix code, `LOOK_BIBLE_template.md`, SCORECARD, how Ricks wrote a real three.js set beyond the 50-line demo, what GPU rendering would give on Colab T4.

## E. Spec sections these findings contradict (not yet rewritten)
Section 8 item 1 and Section 9 (three.js removed), Section 10 item 1 (executor), item 3 (sockets), Section 23 (build order), Section 8 item 2 (coded-light rule).
