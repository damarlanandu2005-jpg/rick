# Reference shot plan (ANSWER KEY, analysed from the reference video; NOT an input to the pipeline)
Reference: "Why the Second Draw Always Wins", 56.2 s, 720x1280, 30 fps. Analysed 0-35 s from 1 fps contact sheets, no audio.
Times are approximate (+-0.5 s). Dissolves/continuous camera mean cuts are not hard cuts.

Cast: RED = gunman (red fringed shirt, black hat). CALM = cream hat, mustache, straw in mouth, teal shirt, brown vest, holster. KID = small bystander, green backpack, beer mug. RIDERS = 3 riders on horses (dusk).
Locations: L1 Western street, noon (blue sky, clouds, sand, wood buildings, red barn "FEED & LIVERY"). L2 same street, golden dusk (long shadows, haze, DOF).

## Pass A: 0-16 s (standing/walking only, noon street, no fall)
| # | t (s) | shot | camera | staging / action | effects |
|---|---|---|---|---|---|
| 1 | 0.0-1.0 | medium, RED left | static, slight low | RED aims big revolver at camera, gritted teeth | gun glint |
| 2 | 1.0-2.0 | wide street POV, low | fast track-in on ground | bullet flies toward camera | bullet + motion streak |
| 3 | 2.0-3.0 | medium-wide, CALM centre far | static | CALM stands, bullet foreground left | bullet |
| 4 | 3.0-4.0 | extreme close, CALM hip/holster | static | bullet passes the holster | bullet |
| 5 | 4.0-5.0 | low angle, CALM head+holster | slow tilt | CALM chews straw, bullet lower left | |
| 6 | 5.0-6.0 | extreme wide, CALM tiny at distance | static | street vanishes to horizon, clouds | |
| 7 | 6.0-7.0 | medium-wide, RED left sweating, CALM far right | static | RED shifts weight, CALM waits | sweat drop |
| 8 | 7.0-8.0 | low wide, CALM far centre | static | tumbleweed rolls, RED edge foreground | tumbleweed |
| 9 | 8.0-9.5 | dissolve to close, CALM hands/belt | slow push | hands at sides | dissolve |
| 10 | 9.5-12.0 | medium, CALM full, red barn behind | slow dolly in | CALM stands, jaw works the straw | |
| 11 | 12.0-14.0 | medium, CALM | static | CALM talks, still | |
Pass A needs: 2 characters (sheet05 wild-west cast exists), idle/stand, angry/scared emotes (exist), one noon street, bullet, tumbleweed, sweat drop.

## Pass B: 14-35 s (adds, beyond Pass A)
| # | t (s) | shot | action | note |
|---|---|---|---|---|
| 12 | 14-15 | extreme close, gun hand | RED's gun spins out, gold flame, pebbles | VFX (gold flame) |
| 13 | 15-17 | close/medium RED mid-air | RED lifted in gold flame, shocked | VFX |
| 14 | 17-20 | RED falls and lies face-down, dust | fall + lie poses (act_bigfall/fall/act_lie exist) | lying pose |
| 15 | 20 | close, gun on ground | | prop |
| 16 | 21-24 | CALM walks past porch posts with KID, BEER 5c sign | walk_front exists | new set pieces |
| 17 | 24-26 | KID enters saloon swing doors | | doors |
| 18 | 26-30 | DUSK: 3 RIDERS on horses, dust, long shadows | act_ride exists, horse assets TBD | L2, horses |
| 19 | 30-31 | bodies lying in street | | |
| 20 | 31-35 | two men talk before PHOTOGRAPHS shop, DOF blur | gestures | L2, DOF |
Sitting: none in 0-35 s. 37 s onward = saloon table + telegraph desk (excluded).

## Known risks
1. Gold-flame aura, bullet streak, dust: effects, no existing Ricks module confirmed yet.
2. Horses: act_ride exists, a separate horse asset not yet confirmed.
3. Many extreme close-ups: cards are flat 2D, so very large scale needs high-res puppet PNGs.
