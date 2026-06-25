# Generate an Animation Spritesheet from Anchor Images

## Objective

Generate one animation spritesheet from the user's anchor images and request.
The result must contain a deliberate, readable animation—not a collection of
loosely related poses.

Present the generated sheet for review and iterate until the user explicitly
approves it. Do not slice an unapproved sheet.

Follow the repository-wide workflow and file locations in `README.md`.

## 1. Interpret the request

Determine:

- `ANIMATION_NAME`: filesystem-safe name such as `dash-east`
- `SUBJECT`: the character or object being animated
- `ACTION`: the requested animation
- `DIRECTION`: screen-space or world-space direction, when applicable
- `ANIMATION_TYPE`: looping or non-looping
- `FRAME_COUNT`
- `COLUMNS` and `ROWS`
- `CELL_WIDTH` and `CELL_HEIGHT`
- `BACKGROUND_COLOR`: default `#00FF00`
- `ANCHOR_IMAGES`: all supplied reference images

Ask only for information that cannot be inferred safely from the request,
anchors, or project files.

The grid must contain exactly `FRAME_COUNT` cells:

```text
COLUMNS × ROWS = FRAME_COUNT
```

## 2. Assign a role to every reference image

Describe each supplied image by function before writing the generation prompt.
Common roles are:

- **Identity anchor:** authoritative character identity, proportions, facial
  features, palette, line work, shading, and silhouette.
- **Directional pose anchor:** establishes facing, body bias, or action
  direction. It is not a frame to duplicate throughout the sheet.
- **Style anchor:** establishes rendering medium, detail, texture, and line
  quality without replacing the identity anchor.
- **Scale reference:** establishes approximate gameplay scale only. Do not
  reproduce its environment, props, lighting, or UI.

One image may serve more than one role when appropriate. Never treat every
reference as equally authoritative, and never invent references the user did
not provide. Treat identity as authoritative, pose as secondary, style as
medium/detail only, and scale as gameplay size only. If those roles conflict,
preserve the higher-priority reference.

State exactly what to preserve and what not to copy from each image.

Example:

```text
Image 1 — identity anchor: anchors/character.png
Preserve the character's exact proportions, face, palette, outline, shading,
and defining silhouette.

Image 2 — directional pose anchor: anchors/dash-east.png
Use this only to establish an eastward body bias and face placement. Do not
repeat this exact pose in every frame.
```

## 3. Define the output specification

The prompt must explicitly state:

- total canvas dimensions
- column and row count
- cell dimensions
- frame count
- frame order: left to right, then top to bottom
- exactly one complete subject in every cell
- no gutters, margins, labels, numbers, borders, grid lines, or guides
- exact background color outside the subject
- stable camera, scale, body anchor, and baseline
- whether the engine supplies world-space translation

Calculate:

```text
canvas width  = COLUMNS × CELL_WIDTH
canvas height = ROWS × CELL_HEIGHT
```

Do not request dimensions that conflict with the grid.

When the game engine supplies movement, tell the generator to keep the subject
in the same cell-relative position and animate pose or deformation only.

For chroma-key spritesheets, avoid green-matted edges. If a sheet is assembled
locally from transparent or generated elements, compose the subject on real
alpha first, then write the chroma background only into fully transparent
pixels. Semi-transparent edge pixels must keep subject-colored RGB values, not
RGB blended with `#00FF00`. This keeps later background removal from leaving a
green halo.

## 4. Describe the subject, action, and direction

Write a concrete animation direction section that answers:

- Who or what is being animated?
- What must remain identical to the identity anchor?
- Which way is the subject facing or moving?
- How should direction read in the silhouette and pose?
- What camera or perspective must remain fixed?
- Which visual signals are allowed to communicate the action?

Prefer physical descriptions over vague adjectives. For example:

```text
Communicate eastward speed through forward lean, horizontal stretch,
asymmetric compression, and a modest attached silhouette smear.
```

Avoid relying only on phrases such as “dynamic,” “energetic,” or “cinematic.”

## 5. Design the timing and frame progression

Specify the animation's temporal contract before generation.

For a non-looping action, define:

- the state of frame 1
- acceleration or escalation
- peak action
- recoil, sustain, or ending state
- whether anticipation and recovery are included or forbidden

For a loop, define:

- entry pose
- major motion phases
- return path
- how the final frame transitions back to frame 1
- whether duplicate hold frames are intentional

Use a numbered frame-by-frame progression when the exact poses matter. With a
larger frame count, coherent ranges may be used only if each range has a clear
purpose.

Example structure:

```text
1. Frame 1: The action is already active; moderate forward lean and stretch.
2. Frame 2: Increase stretch and compress the trailing side.
3. Frame 3: Approach the peak pose with stronger directional force.
4. Frame 4: Reach maximum extension while keeping the face readable.
5. Frame 5: Recoil without returning to idle.
...
16. Frame 16: End in an active pose suitable for the intended transition.
```

Require meaningful variation between frames. Repeated near-identical poses do
not constitute an animation.

## 6. Specify visual style

Translate the visual evidence in the anchors into explicit requirements:

- rendering medium and resolution
- outline color, weight, and smoothness
- palette and shading behavior
- facial features and expression
- defining anatomy or silhouette
- texture and detail level
- consistency requirements across frames
- safe padding inside every cell

Do not replace reference-specific observations with generic style labels.

## 7. Specify motion constraints

State what deformation and motion language are allowed. Depending on the
request, this may include:

- squash and stretch
- lean and compression
- secondary motion
- controlled attached smears
- expression changes
- silhouette variation
- volume preservation

Also state what must remain coherent, such as eyes, mouth, limbs, costume,
outline, or permanent silhouette features.

Distinguish intentional deformation from accidental resizing. Unless requested,
the subject should retain a consistent overall scale and volume.

## 8. Write hard constraints

End the prompt with an explicit negative constraint list. Include all
request-specific prohibitions and these baseline atlas constraints:

- no subject overlap across cell boundaries
- no cropped body parts
- no empty or extra cells
- no visible grid, labels, text, numbers, or watermark
- no camera or perspective changes
- no positional drift when movement is engine-controlled
- no extra limbs, changed identity, or unrequested accessories
- no altered facial structure, palette, outline language, costume geometry, or
  rendering medium drift
- no scenery, floor, props, UI, or environmental elements
- no cast shadow unless requested
- no detached particles, trails, afterimages, or VFX unless requested
- no unrequested rendering-style changes
- no accepting a sheet that meaningfully drifts from the approved anchor
  images; regenerate instead

Name direction-specific mistakes explicitly, such as “no westward, vertical,
or diagonal motion” for an eastward action.

If engine-side systems provide trails, particles, shaders, lighting, or camera
effects, say so and prohibit the image model from baking them into the sheet.

## 9. Assemble the generation prompt

Use this section order:

```text
# <Subject> <Action> — Spritesheet Generation Prompt

## Inputs
<Each reference image, its role, what to preserve, and what not to copy>

## Output specification
<Canvas, grid, cell size, order, background, anchoring, translation contract>

## Subject and direction
<Identity, facing, movement, perspective, and physical action description>

## Timing and frame progression
<Numbered frames or clearly defined temporal phases>

## Visual style
<Reference-specific rendering requirements>

## Motion constraints
<Allowed deformation and features that must remain coherent>

## Hard constraints
<Explicit prohibited outcomes>
```

Before generation, check that the prompt is internally consistent and that
every important user requirement appears in at least one section.

## 10. Generate and validate the candidate

Generate the sheet using all required anchor images.

Save the current candidate as:

```text
work/<animation-name>/001-generated/<animation-name>-spritesheet.png
```

Validate:

1. Canvas dimensions match the output specification.
2. The sheet has the exact requested grid and frame count.
3. Every cell contains exactly one complete subject.
4. Frame order and motion progression are readable.
5. Character identity and style remain consistent.
6. Camera, scale, anchor, and baseline are stable.
7. No subject crosses a cell boundary.
8. The background is uniformly removable.
9. Semi-transparent subject edges are not matted against the chroma color.
10. No forbidden text, guides, scenery, VFX, or artifacts appear.

When the source uses a chroma background, preview or audit a cleanup simulation
on a dark background before approval. If visible chroma-colored pixels remain
on the subject after simulated key removal, reject and regenerate or reassemble
the sheet before passing it downstream.

Reject and regenerate a malformed sheet rather than passing it downstream.

## 11. User review

Present the candidate spritesheet and ask whether the user approves it or wants
changes.

If changes are requested:

1. Translate the feedback into precise prompt changes.
2. Preserve all requirements the user did not change.
3. Regenerate the candidate.
4. Replace the rejected candidate rather than creating a versioned folder.
5. Present the new sheet for review.

Continue until the user explicitly approves the sheet. Once approved, proceed
with step 003 according to `README.md`.
