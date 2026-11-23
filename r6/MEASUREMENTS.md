# R6 measurements (local CPU, 2 vCPU, no GPU)
Clean run of `r6/test_orchestrator.py`: 103 PASS / 0 FAIL, ~23 min total (includes one real 430-frame render).
- Fixture build (synthetic TEST_FIXTURE_ONLY, bake + CH.build + artifacts + judge + approval): 18.4 s
- Pipeline before approval (waits at G9, exit 2, no lock/stills/render): 1.3 s
- Full production pipeline on the fixture (G1-G9, lock, 430-frame base render at 720x1280 ~1.8 s/frame, composite, MP4, all-frame QA incl. check_film): 834.1 s
- Resume (re-run the same command, cache hits): 69.0 s
- Named test mode, partial 0-2 (production:false, PARTIAL): 22.6 s
- Rejected Hat Toss: stops at the first gate, 0 expensive renders: 1.2 s
Regressions after the R6 edits: R5 60 PASS (41 s), R4 61 (38 s), R3 79 (52 s), R2 76 (49 s), R1 gates 27 (29 s), R1 frames 33 (<1 s); 0 FAIL in all.
Fixture film: 55 words, 430 frames, lens 28 mm; the real check_film (video camera speed/rest bands) passes unchanged.
