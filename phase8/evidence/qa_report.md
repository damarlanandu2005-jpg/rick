# Hybrid QA: FAIL (1)

- **PASS** 1 PLAN | film_plan check: 0 FAIL | RESULT: 0 FAIL, 5 WARN of 41 gates 
- **PASS** 1 PLAN | baked file camera_baked.json |  
- **PASS** 1 PLAN | baked file performance_baked.json |  
- **PASS** 1 PLAN | baked file sound_events.json |  
- **PASS** 2 THREEJS | base stills: present, 720x1280, not blank | 299 frames 
- **PASS** 2 THREEJS | lock fresh (camera/performance/flights sha1 match the plan files) |  
- **SKIP** 2 THREEJS | flight gates |  (film has no flights)
- **PASS** 4 COMPOSITE | final frames == base + layer x alpha from the CURRENT inputs (hash-checked) | 299 frames 
- **PASS** 4 COMPOSITE | outside every layer's named mask the final frame equals the base | changed px 0, max diff 0 
- **PASS** 5 VIDEO | ffprobe: 720x1280, 299 frames, 30 fps | [{"width": 720, "height": 1280, "r_frame_rate": "30/1", "nb_read_frames": "299"}] 
- **PASS** 5 VIDEO | silent for now (no audio stream) |  
- **PASS** 5 VIDEO | decoded video frames == composite PNGs (PSNR >= 35 dB) | min 38.0 dB over frames [0, 149, 298] 
- **FAIL** 5 VIDEO | check_film.py on the final video | RESULT: 1 FAIL, 4 WARN of 21 gates -> /tmp/canyon4/ep/out/qa/film_check/film_check.md 
- **SKIP** 5 VIDEO | frame_checks/check.mjs (head cut, body side, face covered, feet) |  (needs the GPU render path; run with --frame-checks on a GPU machine)