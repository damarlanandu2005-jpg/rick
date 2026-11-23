# LOOK BIBLE: THE HAT TOSS (minimum needed by reference_board.json; existing Ricks conventions, no new style system)
## Story world
One noon Western street (set western_street, recipe western_noon). One connected place; the camera only changes distance and height.
## Palette (from the Rick reference board b1-b3)
Cool saturated blue sky with white clouds against warm orange sand and red/brown shop fronts. The ONE accent: the gambler's black top hat with its red band and the gold coin. Saturation and brightness stay in the CB_RULES 6b bands.
## Environment treatment
Painted flat-shaded wood fronts, packed sand ground, telegraph poles; set as built by sets/western_street.js; the Blender barrel (registry prop_saloon_barrel) sits at the gambler's elbow in the warm wood colours.
## Character treatment
The approved 2D puppet card, drawn by the existing card system; hat and face must read at 720x1280; no re-drawing; his shadow falls on the sand with the card shading rules.
## Material treatment
Library names only: wood_grain, painted_metal_chipped, plaster, cloth; the barrel uses mat: names (wood_grain, painted_metal_chipped.<hex>); the coin is the flight sphere, colour #f2c230.
## Light per beat
| Beat / words | Time of day | Key | Fill / bounce | Practicals | Night tint |
|---|---|---|---|---|---|
| 1-7 all | noon, clear | hard sun from the upper left, high, warm white | sky blue fill from above-right, warm sand bounce | none | none |
## Shadows
Cast shadow hard and short (noon), contact shadow dark and tight under the boots; the barrel casts a matching short shadow.
## Camera
24 mm throughout; low wide (0.55 m) for the hook, chest height (1.2 m) for the flip, tilt up for the throw, close push on the hat for the payoff. Camera idea: "the look up": the camera never leaves the man except to follow the coin.
## Air and motion of the world
Clear air, a faint haze at the far end of the street, small dust motes in the sun; no wind motion except a loose tumbleweed rolling in the far distance at most.
## Contrast, depth, effects
Depth from the street's vanishing point and the sky; strongest contrast: the black hat against blue sky in beats 5-7. Effects: a glint on the coin, a tiny dust kick on the landing, nothing else.
## Chosen Rick frames
b1_a / b1_b (wide street, lone figure), b2_a / b2_b (medium, hat brim), b3_a / b3_b (object in the sky, close). Frames only set the LEVEL, nothing is copied.
