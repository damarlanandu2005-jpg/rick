# Director playbook: script text -> intent spec

Claude (the director) writes ONLY words in `intent_<video>.json`. `compile_intent.py` turns them into numbers (rules in its `RULES` dict), `validate_plan.py` checks every shot, then Blender renders. Never put coordinates in an intent; if a shot looks wrong, fix the RULES or the vocabulary, not one video.

Per shot: `id, sec, note, size, subject, focus, angle, side, lens, move, amount, lead, cast[], fx[]`
- size: ewide | wide | full | medium | cu | ecu. With `subject` the camera frames that character; without, it is a staged wide shot.
- focus (with subject): face | chest | belt | feet. angle: low | eye | high. side: left | center | right. lens: wide | normal | tele.
- move: static | push | pull | tilt_up, amount small | medium. lead: left | right (room to aim into).
- cast[]: `{id, at: left|center|right, dist: near|mid|far|vfar, move: <existing Ricks move key>, style}`; moves in use: idle, emo_scared, aim_gun, emo_angry.
- fx[]: `bullet` (path across | toward), `tumbleweed`. Unknown types are dropped with a note.
- top level: name, place (preset), cast{id:{spec,height_m}}, transitions[{between,type:dissolve,sec}], grade (day).
Missing from the kit for now (say so in the plan, do not fake): sitting/crouch, dust, flame, horses, dusk.
