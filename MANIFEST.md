# Branch `ricks-2d-core`: what was copied from the three RicksClips V1.1 zips

Nothing here was rewritten. Files were copied unchanged, with their original relative paths, so the
imports keep working (checked: the puppet modules, the motion library and the Python tools load).
The three original zips are still on `main` as the untouched source.

**Architecture authority: `docs/PRODUCTION_BLUEPRINT_LOCKED.md`.** This file only records where files came
from. Its original branch-creation note (2026-11-19) said "3D environments, lighting, camera, physics and
rendering in Blender (EEVEE)" and called three.js "not our renderer"; that was superseded (Spec v2, then the
blueprint) and is corrected here: **three.js is the final base renderer, Blender is the asset workshop and
optional masked-layer renderer, 2D Ricks puppets are the only characters, no 3D characters for now.**

## ACTIVE (code and assets we use as they are)

| Path | What it is |
|---|---|
| `templates/vector2d_characters/` | The 2D puppet kit: `code/` (rig, 150-character cast, 13 body forms, faces, mouths, outfits), `sheets_png/` (15 cast sheets), `faces_png/`, `views_golden/` (front, 3/4, side, back views) |
| `templates/motion_styles/` | Move library (about 45 actions, `library.mjs` `pick()`) |
| `templates/pieces/` | Proven moves and effects, each with "when it fits" |
| `templates/threejs_film/` | Kept only for `puppets.mjs` and `poses.mjs` (puppet state to card drawing) and the plan baker / card exporter. Run `npm install` in this folder. (Branch-creation note, superseded: it is now the final base renderer, see the blueprint) |
| `templates/blender_look/` | Reusable Blender parts only: `from_lock.py` (puppet cards as PNG-sequence planes, camera keys), `materials.py`, `lights.py`, `look.py`, `cards.py`, `card_edge_shadow.py`, `render.py`, `grade.py`, `scatter.py`, `gpu_waiter.py`, `face_fix.py` |
| `templates/blender_cine/` | Deterministic baked camera rigs (`cine.py`) |
| `templates/film_example/` | A `film.json` that passes the plan gates (shows the spec format) |
| `templates/PICTURE_PLAN.md`, `LOOK_BIBLE_template.md`, `SCRIPT_example.md` | Planning formats |
| `templates/audio/` | Audio templates (kept for now; the synthesis part may be dropped later) |
| `templates/scripts/` | `short_qa.py`, `sbs_sheet.py` (QA sheets) |
| `tools/` | `film_plan.py`, `check_film.py`, `check_episode.py`, `check_views.mjs`, `frame_checks/`, `measure/`, `token_report.py`, `fish_tts.py`, `voice_prep.py`, `blenderkit_tool.py` |
| `references/measure/` | Reference target numbers the checks compare against |
| `library/` | 20 pitfalls and the solutions; to become pre-flight checks |

## REFERENCE ONLY (read to distil; nothing loads these)

`ricks_reference/`: `CB_RULES.md`, `SKILL.md`, `WORKFLOW.md`, `CINEMATOGRAPHY.md`, `DENSITY_RULES.md`,
`agents/` (the 16 agent files), the style bible, the scorecard and the pipeline audit.

## Deliberately NOT copied

- Episode-specific code: `aircraft.py`, `build_density_v3.py`, `lock2*.py`, the `paint_*` and `*_v3` files, the airfield textures and cards, `examples/lightning-spear/`.
- The three.js test artifacts (`_pbr_test/`), the frame-check proof images and backups, `rules/dept/` (derived copies of the rule book), `references/reports/`, the Remotion `bridge/` folder, installer and PC-specific scripts, `__pycache__`.

## Known limits (from the Ricks audit)

Cast characters are front view only except about a dozen with all four views; the puppet arm cannot reach
above the head; held items do not follow gestures; blinks do not show on meme faces; the Blender transfer was
only proven as a bare rebuild. The first vertical slice must test exactly these.
