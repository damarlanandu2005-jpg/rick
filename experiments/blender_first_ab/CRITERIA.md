# Blender-first A/B: criteria fixed BEFORE any result (committed before the first run)

**Question.** Can Blender become the primary 3D picture renderer while Ricks/JavaScript keeps what it already owns?
This is not "can Blender replace everything". The decision rests on human / art-direction quality first. Performance and engineering cost are separate evidence. Pixel similarity does not decide anything.

**Routes** (same `film.json`, lock, camera, character-card sequences, assets, timing; 720x1280, 30 fps)
- **A, current hybrid:** three.js base (3D set, cards, its own post: DOF, bloom, dust, vignette; JS 2D effects and captions drawn in the same pass) + the existing Blender `lamp_reflect` layer (frames 201-210 only) -> composite.
- **B, Blender-first:** Blender renders the set, the 3D character cards, props, occlusion, shadows (existing `from_lock.py` + `look.py`, preset of the place), then `grade.py` (bloom, vignette, grade), then the JS **overlay** (`render.mjs --overlay`: captions and the 2D effects only) laid over. No new renderer, no new layers, no DOF matching, no focus check.

**Ranges.** 0-149 (a normal shot), 201-210 (the lamp layer frames), 316-330 (the coin flight and the camera chase).

## Must preserve (the judge scores each: B better / same / worse / not comparable, per range)
1. Ricks character presentation: characters not unintentionally blurred, outline crisp.
2. Camera, framing, composition.
3. Lighting quality and intentional lighting direction.
4. Materials and important highlights.
5. Depth-of-field behaviour (characters crisp, far set soft).
6. Motion and flight readability (the coin, the chase).
7. The 2D effects Ricks expects (glints, flashes, captions).
8. The overall "finished coded-frame" look.

## Recorded separately, never traded off silently
- Effect matrix (`effects_matrix.md`): bloom, dust, vignette, DOF, glints, flashes, bolts, captions, held props, reflections, shadows, materials, sky/light; for each, who owns it in A and in B, and what the judge saw.
- Character-card sharpness and filtering (measured, plus the Blender filter settings that touch them).
- Timing: Route B on this exact scene on the T4 (cold start, first frame, mean, median, P90, total, GPU utilisation, VRAM); Route A's three.js base measured on Colab CPU and on a local 2-CPU machine, reported separately (never one universal baseline); the existing 2.14 s/frame benchmark is not used.
- Engineering cost: lines/files of NEW Route-B code only (not `from_lock.py`, `look.py`, `grade.py`, `materials.py`, which already exist).

## Method rules
- The contact sheets are blind: routes are labelled X and Y, assignment shuffled per range with a seed; the key is written to a separate file that the judge does not open until after scoring.
- Nothing in the existing hybrid pipeline is modified or deleted by this experiment (all new files live in `experiments/blender_first_ab/`).
- Route B is run as it exists (preset lighting, library materials, Blender DOF focus on the subject, motion blur OFF because Ricks says characters are never blurred). Any gap is recorded as a gap, not tuned away.

## Decision table
| Result | Decision |
|---|---|
| Blender quality >= hybrid and clearly simpler/faster | move toward Blender-first |
| Blender noticeably worse | keep hybrid |
| Blender better in places but missing effects | hybrid stays the production path; move effects selectively |
| Inconclusive | one more controlled shot before any architecture change |
