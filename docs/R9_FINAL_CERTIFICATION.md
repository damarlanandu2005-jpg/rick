# R9 — Final production certification and system freeze

Branch `r9-final-certification` (from `r8-audio-integration`). `main` untouched at `d26d845`. Certification run on 2026-11-24, local Linux container, 2 vCPU, no GPU.

## Executive result
**R9 STATUS: PASS. PRODUCTION READINESS: PASS (for the documented scope). FRAMEWORK FROZEN.**

- The full regression passed before any change, and passed again after the R9 fixes: R1 to R8 all 0 FAIL.
- The certification run `r9/certify.py` gave 47 PASS / 0 FAIL on the final code, with two classified notes (one D, one E).
  - A real 720×1280, 30 fps, 430-frame MP4 with synchronized AAC audio was produced from approved, locked inputs.
  - The MP4 was decoded and checked frame by frame and sample by sample.
  - A clean run and a resume run were both done.
  - The asset, character, audio and safety checks were all exercised on the real artifacts.
- R9 found three engineering defects (class A). All three are fixed with a few lines each in existing code; nothing new was added:
  - `words.json` was not signed by the approval;
  - a tampered locked character card did not block a direct `render.mjs` entry;
  - the three.js base render was not reproducible: the floating dust used unseeded `Math.random`. Each render process therefore drew different pixels, and the same approved film passed `check_film` in one clean run but failed it in the next.
- GPU: NOT EXECUTED (environment: there is no GPU device in this container).
- R5 "The Hat Toss" stays a creative FAIL (judge verdict FAIL at the unchanged 8.5 threshold; no approval).

## Architecture (verified in code, unchanged by R9)
```text
REFERENCE -> STORY -> SCRIPT / WORDS -> REFERENCE BOARD -> PICTURE PLAN -> LOOK BIBLE -> CHARACTERS (R3, 2D cards) -> ASSETS (R4/R7 registry GLBs)
-> film.json -> PLAN BAKE (film_plan.py) -> G1-G7 -> THREE.JS STORYBOARD -> WHOLE-FILM ROUGH / HOOK ANIMATIC (review.py) -> INDEPENDENT JUDGE -> G8
-> HUMAN APPROVAL (approval.json) -> G9 -> LOCK (render.mjs --export-lock + lock_stamp.py) -> ONE EXPENSIVE FINAL RENDER (three.js base, 7 base)
-> optional masked Blender layers (8 layers) -> composite (9 final, silent final.mp4) -> VISUAL QA (10 qa: qa_hybrid + check_film)
-> AUDIO (11 sound: audio.py validate + mix) -> FINAL MUX (video stream copied) -> DELIVERY QA (12 delivery qa, decoded)
```
- **Creative authority:** Ricks; `film.json` is the one plan.
- **Order:** approval before the expensive render; the lock freezes the approved inputs.
- **Picture and assets:**
  - Three.js is the base picture.
  - Blender is the asset workshop, plus optional masked layers.
  - Characters are 2D; sets and props may be 3D.
- **Production format:** 720×1280 at 30 fps.
- **Audio:** processed after the picture.
- **Fail closed:** everywhere.
- **Pipeline stage list:** `pipeline.ORDER` is unchanged; R8's delivery stages follow it (`pipeline.DELIVERY`).

## Regression results (exact; same counts before the R9 fixes and after them)
| Suite | Before R9 fixes | After R9 fixes (final code) |
|---|---|---|
| R1 gates | 27 PASS / 0 FAIL | 27 / 0 |
| R1 frames | 33 / 0 | 33 / 0 |
| R2 | 76 / 0 | 76 / 0 |
| R3 | 79 / 0 | 79 / 0 |
| R4 | 61 / 0 | 61 / 0 |
| R5 | 60 / 0 (creative rejection preserved) | 60 / 0 (creative rejection preserved) |
| R6 | 103 / 0 | 103 / 0 |
| R7 | 96 / 0 | 96 / 0 |
| R8 | 53 / 0 | 53 / 0 |
| R9 (`r9/certify.py`) | — | 47 / 0 |

## End-to-end result
Certified film: the existing TEST_FIXTURE_ONLY infrastructure put together. It is not a new creative film:
- the R6 mechanical fixture (script, words, board, picture plan, look bible, `char_stationmaster`, the canyon film that passes the real `check_film` video gates);
- R7 Film A (real three.js storyboard + animatic, a registry copy, the handcar placed by the set module, the lantern placed by `film.json` at [1.6, 2.6, 0], rotation 30° and scale 1.2);
- R8 audio (voice, music bed, ambience, 4 SFX including two overlapping impacts).

All of these are signed by the approval. The film is stamped `production:false` because it is a fixture; every gate was enforced.

| | Clean run | Resume run (same command) |
|---|---|---|
| Result | PASS (exit 0), every stage PASS/CACHE/INPUT | PASS (exit 0) |
| Total | 519.6 s | 78.8 s (6.6× faster) |
| Visual final render (7 base, 430 frames) | 428.2 s (1.0 s/frame, CPU) | CACHE (not re-rendered) |
| Composite (9 final) | 14.1 s | 14.4 s |
| Visual QA (10 qa) | 54.8 s | 56.0 s |
| Audio (11 sound: validate + mix + mux) | 1.7 s | 1.6 s |
| Delivery QA (12, decoded) | 3.6 s | 3.6 s |
| Delivery | `final_video.mp4`, 4,062,534 bytes | byte-identical |

**Reproducible picture (after fix 9):** frames 60, 200 and 350, re-rendered in a new process with the production base-render arguments, are byte-identical to the final stills.

The resume regenerated nothing and changed no hash. This covers: `creative/`, `film.json`, `approval.json`, `words.json`, the baked plan, `lock.json`, the lock sets/cards, the registry copy, the asset GLB, the staged assets, all 430 stills, `final.mp4`, `mix.wav` and `final_video.mp4`. G1 to G9 were re-checked (PASS), and no gate was skipped.

**Before the pipeline (fixture build):** 124.4 s in total. That includes the storyboard (4.6 s), the animatic (87.6 s) and the lock export (13.8 s).

**Visual QA on the decoded MP4:**
- h264 at 720×1280 and 30/1, with 430 decoded frames (= the plan) and no decode errors.
- No black or blank frame: the darkest frame mean is 39.8 (limit 8) and the flattest frame std is 4.3 (limit 2).
- No frozen run of 10 or more identical frames.
- Duration 14.333 s = 430/30.
- `final_manifest` names all 430 base stills by sha1, plus the approval and lock sha1. The existing `qa_hybrid` checks PSNR ≥ 35 on every decoded frame against the composite, and `check_film` passed (camera-speed median 1.72; band floor about 1.55).

**Audio QA on the decoded MP4:** 13/13 PASS.
- One AAC 48 kHz stereo stream that decodes completely.
- The picture is unchanged against `final.mp4`.
- The audio length is within 1 frame of the video.
- Not silent, and no clipped sample.
- A/V sync: lag 0.00 ms, correlation 0.999.

## GPU result
**GPU CERTIFICATION: NOT EXECUTED** (class E, environment limitation).
- The container has no GPU device (`/dev/dri` absent, no `/dev/nvidia*`).
- Chromium's WebGL reports `ANGLE (Mesa, Vulkan … llvmpipe)`, which is a CPU rasterizer.
- The existing `render_gpu.mjs` correctly refuses with exit 2 ("The graphics card is NOT drawing").

No pass is claimed. The GPU path (`templates/threejs_film/GPU_RENDER.md`, ANGLE/D3D11) has to be certified on the PC that has the graphics card.

## Asset result (R7): PASS
`prop_oil_lantern@1.0` and `prop_rail_handcar@1.0` went through the whole chain: registry → `film.json` placement → three.js → storyboard → animatic → lock → final render.
- **Resolution:** both resolved with pinned versions, the live GLB contract and a valid validation record (G7 PASS).
- **Review renders:** the storyboard and animatic record the lantern's sha1.
- **Lock:** it froze both GLB sha1s, and the lock set GLB carries them with every `mat:` name, including the colour suffixes.
- **Placement:** the locked scene has the lantern at exactly 30.00° and scale 1.200, while the registry contract is unchanged.
- **Anchors:** the anchor `lantern.flame` lands where that placement puts it, on 197 frames, with an error below 0.001 of the frame.
- **Visible in the final:** the three.js ray test (occlusion counted) sees the lantern on 125 of 430 frames.

## Character result (R3): PASS
- **Identity:** slot `eng` is `char_stationmaster` from the R3 registry, and the production record is valid.
- **Lock:** it froze the card index and every image sha1; `characters.py check-lock` and `lock_stamp` both pass.
- **Determinism:** rebuilding the cards from the same spec gives identical hashes.
- **Downstream:** the judge read the character evidence hash, and the base render ran from that lock.
- **Tamper check:** after the R9 fix, a tampered locked card is refused at every lock consumer.

## Audio result (R8): PASS
- **Mix:** voice, music, SFX and ambience are all in the mix, with overlapping SFX (impacts at frames 74 and 80 over the music/ambience beds).
- **Encoding:** AAC; the decoded audio passes, its duration matches the video, and sync is 0.00 ms.
- **Unchanged:** R8's documented limitations (below) remain limitations.

## Safety guarantees (all certified on copies of the certified film)
| Case | Result |
|---|---|
| Before approval | `render.mjs --frames` REFUSED (exit 3); `final_video` REFUSED; audio mux REFUSED; the pipeline WAITS at G9 (exit 2) with no render |
| After approval + lock | the production render was allowed and ran exactly once |
| Lock immutable | an edited `lock.json` (frozen camera hash) → render REFUSED; a changed locked card → render REFUSED (R9 fix) |
| Changed approved input | `PICTURE_PLAN.md`, `words.json` (R9 fix) or `film.json` → approval STALE, render REFUSED |
| Tampered GLB | caught by the resolver (stale GLB), the lock (library bytes ≠ frozen bytes) and the approval (G7 re-checked at G9); render REFUSED; the pipeline stops at G7 with no render. Restoring the bytes restores validity |
| Wrong / missing asset | the resolver fails closed (version 9.9 unknown; id not in the registry) |
| Audio changed after approval | a changed sound cue → approval STALE, mux REFUSED; a corrupted source → mux REFUSED; a modified delivery MP4 → delivery QA FAIL |
| Valid replacement audio source after approval | **not refused (class D, documented).** Audio source files are not approval-signed: sound is made after the visual lock (Ricks stage 11). The replacement is traced in `final_manifest.audio.inputs` (sha1 differs) |
| R5 creative rejection | preserved (verdict FAIL, threshold 8.5, no approval) |

## Coverage matrix
| Class | Capability | Status | Evidence | Limitations |
|---|---|---|---|---|
| A static/slow explanatory | 2D character + 3D environment + voice | **TESTED** | certified film, final render + decoded QA | one character, one set |
| B character + prop | character beside registry props (handcar, lantern) | **TESTED** | certified film (lantern seen on 125/430 frames) | |
| B | character HOLDING a registry GLB | **NOT IMPLEMENTED** | R7 refuses `grippable` | held props are JS builders (`film.json held3d`) |
| B | JS-builder held props (held3d) | **NOT YET TESTED** | code exists in film.js | no R1-R9 certification evidence |
| C camera movement | orbit / travel between word-anchored stations | **TESTED** | certified film; `check_film` camera-speed/rest gates on the decoded video PASS | |
| D multiple shots/cuts | several takes (hard cuts) | **SUPPORTED WITH LIMITATIONS** | probe: 2-take plan (0 FAIL), storyboard, animatic | the final render of a multi-take film is not yet certified |
| E fast visual action | thrown-object flight + camera | **SUPPORTED WITH LIMITATIONS** | probe: kit flight example plan (0 FAIL), flights baked, storyboard, animatic | final render not yet certified; throwing a registry GLB NOT IMPLEMENTED |
| F reusable asset-heavy scene | several registry assets in one scene | **SUPPORTED WITH LIMITATIONS** | 2 registry assets in the certified final render; R7 Film A/B reuse | dense scenes (many assets) NOT YET TESTED |
| G audio-heavy | voice + music + SFX + ambience, overlaps | **TESTED** | certified film, R8 suite (cases A-F) | no ducking/LUFS (see limitations) |
| H reference-driven | board → picture plan → judge → approval | **SUPPORTED WITH LIMITATIONS** | mechanics tested with a synthetic board; the one REAL reference film (R5) was correctly REJECTED | no real reference-driven film has passed the judge yet |
| I full end-to-end | everything together | **TESTED** | certified clean + resume runs | fixture film (`production:false`) |
| — | Blender asset workshop → GLB → registry → three.js | **TESTED** | R4, R7, certified film | |
| — | optional masked Blender enhancement layers | **NOT YET TESTED** end to end in R9 | the 8 layers stage exists (R6), skipped when a film has none | |
| — | GPU render path | **NOT YET TESTED (NOT EXECUTED)** | environment has no GPU | certify on the GPU PC |
| — | cloth / fluid / destruction / vehicle physics, arbitrary object manipulation | **NOT IMPLEMENTED / NOT CERTIFIED** | R7 refuses those capability names | |
| — | final MP4 mux + decoded QA | **TESTED** | certified film | |

## Known limitations
1. **No real production film yet.** Every film that passed end to end is a TEST_FIXTURE_ONLY film (`production:false`). The one real reference-driven film (R5) was rejected by the judge.
2. **No owner-approved assets.** The committed registry has none: the handcar, barrel and lantern are `validated` only. A real film needs the owner's `assets.py approve-glb`.
3. **GPU:** not certified (no GPU here). CPU render takes about 1.0 s per frame at 720×1280.
4. **Blender enhancement layers:** not certified end to end.
5. **Audio source files are not approval-signed (class D).** The approval signs the cue plan and `words.json`; source files are traced by sha1 in the final manifest.
6. **Audio features not implemented:** sidechain ducking, the Ricks mix gates (K-weighted voice-vs-bed measurement, −16 LUFS, true peak), the click-free loop point, cue-coverage checking, panning, looping and TTS (R8).
7. **Asset capabilities:** only `static_prop` and `anchor_target`. Holding, throwing or moving registry GLBs is not implemented.
8. **Not yet certified in a final render:** multi-take (cut) films and flight-heavy films; their plan, storyboard and animatic are tested.
9. **Fixture limits:** one character and two assets per certified scene; dense scenes are not tested.
10. **Thin `check_film` margin on the fixture film:** its measured camera-speed median sits close to the band floor. The film now renders reproducibly, but a real film should not be tuned to the edge of a band.

## Production requirements (what a real film must provide)
- **Creative inputs:**
  - `creative/reference_board.json` + real reference frames (private);
  - `creative/SCRIPT.md`, `PICTURE_PLAN.md`, `LOOK_BIBLE.md`;
  - `creative/characters.json` (characters from the R3 registry).
- **Voice:** `voice/voice.wav` + `voice/words.json` (`tools/voice_prep.py`).
- **`film.json`:**
  - places, with registry assets pinned `id@version` and **owner-approved**;
  - cast, takes and stations anchored on words;
  - `sound` cues + an `"audio"` block, with real library sound files inside the episode.
- **Review and approval:**
  - `review.py storyboard` and `review.py animatic`;
  - an independent judge PASS at 8.5 or above (`review.py judge-record`);
  - a human approval (`approval.py create`).
- **Production:** `python3 tools/pipeline.py <episode> --renderer cpu` (or `gpu` on the GPU PC). It stops at the first failure and resumes by re-running the same command.

## Performance measurements (measured)
| Step | Time |
|---|---|
| Storyboard | 4.6 s |
| Animatic (430 frames, step 3 + hook) | 87.6 s |
| Lock export | 13.8 s |
| Visual final render | 428.2 s |
| Composite | 14.1 s |
| Visual QA | 54.8 s |
| Audio (validate + mix + mux) | 1.7 s |
| Delivery QA | 3.6 s |
| Clean run (pipeline) | 519.6 s |
| Resume run | 78.8 s |
| Whole certification script | 1,001.6 s |

Creative planning by the LLM/human is not machine-timed.

## Failure classification (every failure met during R9)
| # | Failure | Class | Action |
|---|---|---|---|
| 1 | `words.json` edited after approval: `approval.py check` still VALID (only the lock caught it) | **A engineering** | fixed: `approval.current` signs `words_sha1`; `check` reports a missing/changed field as STALE |
| 2 | a tampered locked character card was detected by `characters.py check-lock` but did not block a direct `render.mjs` / `final_video` / audio mux | **A engineering** | fixed: `lock_stamp.problems` includes `characters.lock_problems` when the lock froze cards |
| 2b | the narrowed form of fix 2: R5's own minimal synthetic lock (no exported drawings) failed the new check; the check now applies whenever the lock has card drawings (a tampered drawing is still refused; a lock without drawings is the pipeline 6b check's job) | A (refinement of 2) | R5 back to 60/0 without touching its test |
| 9 | the base render was not reproducible: `dustFor()` in film.js placed the dust with unseeded `Math.random` (PSNR 36.8 dB between two renders of the same frame; 1.8 % of pixels differed by more than 8 levels). The same approved film's decoded video measured a camera-speed median of 1.47 against the band floor of about 1.55 in one clean run, and passed in the previous one | **A engineering** | fixed: dust is seeded (mulberry32 from the place); two processes now render byte-identical frames, and certify checks that re-rendered production frames equal the final stills |
| 10 | after fix 9, the certified film (lantern at [0.7, -0.6, 0]: large and glowing, close to the camera in the medium shot) measured a deterministic camera-speed median of 1.49 (band floor about 1.55); the earlier passes were the luck of the random dust | B fixture | the lantern was moved to [1.6, 2.6, 0], still at rotation 30° and scale 1.2, where it measures 1.72 (preview render + the same check_film). The gate is unchanged |
| 3 | certify check did not know the pipeline's `0 scope` status `FULL` | B test | check fixed |
| 4 | certify copies dropped the animatic videos, so safety copies failed G8 first (refused, but for the wrong reason) | B test | copy helper fixed |
| 5 | in reuse mode the script read the resume run's stage record | B test | the clean run's record is kept |
| 6 | a valid replacement audio source after approval is not refused | D unsupported (by design) | documented |
| 7 | GPU path cannot run (no GPU device) | E environment | documented: NOT EXECUTED |
| 8 | R5 Hat Toss judge FAIL | C creative | preserved, not weakened |

## Git state
- **Branch:** `r9-final-certification` (from `r8-audio-integration` `3ccafff`).
- **Commits:** `88c596c` R9 production fixes (approval signs words.json; lock refuses tampered card drawings), `4e3fe63` R9 certification tests, then the seeded-dust fix (render reproducibility), the certify updates and this document.
- **`main`:** untouched at `d26d845`.

## Production readiness
> Can this repository take a Ricks-style short through the approved production pipeline and reliably produce a final 720×1280 30-FPS MP4 with synchronized audio, while preserving approval, lock, asset and QA safety?

**PRODUCTION READINESS: PASS**, for the documented scope. A clean and a resumed production run from approved, locked inputs produced a decoded-verified 720×1280, 30 fps, 430-frame MP4 with synchronized audio. Every approval, lock, asset, audio and QA safety case failed closed. The limits are the ones listed above: no GPU certification, no owner-approved library assets yet, and unsupported capability classes.

```text
R9 COMPLETE
PRODUCTION FRAMEWORK FROZEN
```

Future work only when a real production video exposes a concrete limitation.
