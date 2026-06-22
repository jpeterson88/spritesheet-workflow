# Ghost Dash East — Spritesheet Generation Prompt

## Inputs

- **Image 1 — identity anchor:** `sprites/anchor.png`
  Preserve the approved ghost’s exact identity, proportions, facial features, arm lines, white-to-light-gray body shading, black outline, and four-point lower silhouette.
- **Image 2 — directional pose reference:** `sprites/dash-east.png`
  Use this to establish that the ghost is dashing east (screen-right). Preserve the subtle east-facing placement of the face and arms. This is a directional reference, not a frame to copy repeatedly.
- **Image 3 — gameplay scale reference:** `reference.png`
  Use only to understand the ghost’s approximate in-game scale. Do not reproduce the room or any environment elements.

## Output specification

Create one reusable, non-looping **16-frame eastward dash animation spritesheet** for a 2D isometric-perspective game.

- Canvas: **2048 × 2048 px**
- Layout: **4 columns × 4 rows**
- Cell size: **512 × 512 px**
- Frame order: left to right, then top to bottom
- Use all 16 cells, with exactly one complete ghost in each cell
- No gutters, margins, labels, borders, grid lines, numbers, or guides
- Every pixel outside the character must be exact solid **#00FF00 chroma green**

The game engine supplies all world-space translation. Keep the ghost anchored to the same visual center and baseline in every cell; animate deformation only.

## Subject and direction

The subject is the same friendly, free-floating cartoon ghost shown in the identity anchor—not a redesign or a different ghost.

The ghost travels **east, toward screen-right**. Communicate direction through forward lean, horizontal stretch, asymmetric compression, and controlled silhouette smear. Keep the face and arms subtly biased toward screen-right throughout. Do not rotate the character into a side profile and do not change the camera angle.

## Timing and frame progression

The dash begins immediately. There is **no anticipation, wind-up, idle frame, braking, recovery, or return-to-idle pose** in this sheet. Frame 1 must already read as active high-speed movement, and frame 16 must still be in active travel.

Use this progression:

1. **Frame 1:** Immediate launch pose; strong forward lean and moderate horizontal stretch. Already clearly dashing.
2. **Frame 2:** Increase horizontal stretch; compress the trailing left side of the body.
3. **Frame 3:** Near-maximum speed pose; stronger eastward silhouette pull and slight motion smear.
4. **Frame 4:** Maximum horizontal extension; narrowest body height, with readable face and arms.
5. **Frame 5:** Partial elastic recoil while still traveling at full speed; do not approach idle proportions.
6. **Frame 6:** Secondary speed pulse; stretch eastward again with a slightly different lower-hem wave.
7. **Frame 7:** Strong sustained dash pose; forward half elongated and trailing half compressed.
8. **Frame 8:** Brief squash within the active dash, wider and shorter but still leaning east.
9. **Frame 9:** Re-extension from the active squash; clear rightward force.
10. **Frame 10:** Maximum-speed smear pose, distinct from frame 4 but equally forceful.
11. **Frame 11:** Controlled recoil; retain obvious eastward lean and speed.
12. **Frame 12:** Another sustained stretch with variation in the four lower ghost points.
13. **Frame 13:** Compact active-travel pose; no braking or upright idle posture.
14. **Frame 14:** Final strong extension toward screen-right.
15. **Frame 15:** Slight elastic recoil while maintaining full directional momentum.
16. **Frame 16:** Active sustained-dash pose suitable for transitioning into engine-controlled movement or another dash segment; do not recover to idle.

Across the sequence, create fluid elastic variation rather than repeating identical poses. The body may squash, stretch, lean, and form a modest attached motion smear, but the ghost must remain recognizable in every frame.

## Visual style

- High-resolution, clean 2D cartoon raster art matching the supplied sprites
- Smooth antialiased black contour lines
- Soft white-to-light-gray body shading matching the anchor
- Minimal black oval eyes, small curved smile, and thin curved arm lines
- Preserve the simple, charming, friendly expression
- Preserve the ghost’s broad domed head and four-point lower silhouette
- Keep line weight, shading direction, and rendering quality consistent across all frames
- Keep the complete deformed silhouette comfortably inside each 512 × 512 cell

## Motion constraints

- Squash and stretch are encouraged
- Controlled, shape-based motion smear is allowed only when it remains attached to the body silhouette
- Keep eyes, mouth, arms, outline, and lower points coherent under deformation
- The face may compress or stretch slightly with the head, but must not slide independently or change expression
- Vary the lower hem naturally to support speed, without adding extra permanent points
- Maintain consistent character scale and volume; deformation should feel elastic rather than like resizing

## Hard constraints

- No anticipation or recovery frames
- No idle or neutral standing frame
- No world-space movement or positional drift between cells
- No trailing ectoplasm, wisps, particles, smoke, sparks, glow, aura, speed lines, detached afterimages, or environmental effects
- No cast shadow, ground plane, floor, room, props, text, watermark, or UI
- No extra limbs, altered facial features, costume, accessories, or color changes
- No sprite overlap across cell boundaries
- No cropped character parts
- No visible grid
- No perspective or camera change
- No vertical, diagonal, or westward dash
- No pixel-art treatment, chunky pixels, painterly brushwork, airbrushing, or newly invented texture

Engine-side systems will provide translation, trails, particles, shaders, lighting effects, camera effects, and other dash VFX.
