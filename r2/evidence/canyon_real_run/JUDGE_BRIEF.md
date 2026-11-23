# Judge brief: CANYON RAIL: first 10 s of a railroad short, recreated through the hybrid pipeline (Phase 8 second-script test; the script is read from a reference short's captions, not fact-checked) (version 1)
Run in a FRESH context (a new agent that has not seen the build): Ricks `storyboard-judge` (panels) then `studio-director` (film-level verdict). Do not invent a quality framework; use ricks_reference/agents/storyboard-judge.md and rules/dept/*.md.
Evidence (read these, score the PICTURES): storyboard `creative/STORYBOARD.json` (sha1 223bc40f506a992aed36102bfd753f8b809e7013) with panel PNGs creative -> out/storyboard_panels; whole-film rough `out/animatic.mp4`; hook `out/animatic_hook.mp4` (animatic sha1 cbabfbfa48d59c60eced938c7dc0fbdae81a2e16). Also SCRIPT.md, PICTURE_PLAN.md, LOOK_BIBLE.md, reference_board.json, out/plan/plan_report.md.
Builder contexts (you must NOT be one of them): ['creator-session'].
Write result.json: {"judge": {"id": "...", "context_id": "<your own fresh context id>", "kind": "fresh-context", "agents": ["storyboard-judge","studio-director"]},
 "evidence_read": {"storyboard_sha1": "223bc40f506a992aed36102bfd753f8b809e7013", "animatic_sha1": "cbabfbfa48d59c60eced938c7dc0fbdae81a2e16"},
 "panels": {"s01_start": {...}, "s01_end": {...}, ...},   // one entry per required panel id: {"score": 0-10, "rationale": "...", "fix": "one concrete fix"}
 "film_level": {"verdict": "PASS|FAIL", "notes": "..."}, "studio_director": {"verdict": "PASS|BACK", "note": "..."}}
Required panel ids: s01_start, s01_end, s02_start, s02_end, s03_start, s03_end, s04_start, s04_end. Target: 8.5+ on EVERY required panel. Then run: python3 tools/review.py judge-record <ep> result.json (PASS/FAIL is computed, not declared). You never write approval.json.
