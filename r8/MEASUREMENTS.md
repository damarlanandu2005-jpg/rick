# R8 measurements (local CPU, 2 vCPU, ffmpeg 6.1.1; measured, not estimated)
Unit suite (r8/test_audio.py, canyon example copy, 299 frames = 9.97 s, synthetic TEST final.mp4): 53 PASS / 0 FAIL, 43 s total.
- Audio preparation (generate the deterministic fixture set): 0.079 s
- Validate + mix + mux per case (6 cases A-F): 0.70-1.01 s (the `audio.py mux` process incl. Python start)
- Delivery QA per case (full decode of video + audio, md5 of the picture, cross-correlation): 2.4-2.7 s
- Bare `audio.py mix` of 3 events: 0.58 s wall
End to end on the R6 production fixture (r8/e2e_production.py, clean run, 430 frames = 14.33 s, 7 audio events: voice, music bed, ambience, 4 SFX incl. 2 overlapping):
- fixture build (bake, characters, review artifacts, judge, approval): 15.8 s; fixture audio 0.065 s
- 7 base (the one expensive three.js render, 430 frames): 397.8 s
- 9 final (composite + silent final.mp4): 14.2 s; 10 qa (picture QA): 52.0 s
- 11 sound (validate + mix + mux): 1.07 s
- 12 delivery qa (decoded): 3.41 s
- whole pipeline: 483.4 s; audio is 0.9 % of it (4.5 s vs 397.8 s of visual render)
- delivery: 4,028,764 bytes, 430 h264 frames 720x1280 30/1 (picture md5 == final.mp4), AAC 48 kHz stereo 14.336 s (+128 samples of AAC padding), A/V lag 0.00 ms, correlation 0.999, peak -7.6 dBFS, RMS -20.0 dBFS
First E2E attempt (kept as evidence): the fixture's 12 s music/ambience were shorter than the 14.33 s film; stage 11 sound FAILED CLOSED ("shorter than the requested region (no silent looping or padding)"), no delivery was written; after the fixture fix a `--resume` re-ran only the audio (render CACHE).
