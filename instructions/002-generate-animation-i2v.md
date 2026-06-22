# Generate a 2D Animation with Image-to-Video

## Objective

Generate a short image-to-video clip from one approved character anchor, extract a clean contiguous animation interval, and save an exact number of ordered PNG frames for the existing background-removal and normalization pipeline.

This workflow is intended for high-resolution 2D game animation. It does not ask an image model to draw an entire spritesheet. The video model generates temporal motion; deterministic local tools recover the frames.

Default project use:

```text
Character: friendly floating ghost
Action: eastward dash
Animation type: non-looping active travel
Selected frames: 16
Runtime frame rate: 12 FPS
Input anchor: anchors/dash-east.png
Background: flat #00FF00 chroma green
```

## Pipeline position

```text
Approved anchor image
        ↓
Image-to-video generation
        ↓
Source-video validation
        ↓
Extract all source frames
        ↓
Select one contiguous motion interval
        ↓
Evenly sample the requested frame count
        ↓
Remove Background
        ↓
Normalize Images
        ↓
Game-ready atlas and preview
```

## Required inputs

Ask the user to provide or confirm:

- `ANCHOR_IMAGE`: one approved directional character image
- `ACTION`: animation action, such as `dash`, `float`, `curse`, or `possess`
- `DIRECTION`: screen-space direction
- `ANIMATION_TYPE`: `looping` or `non-looping`
- `TARGET_FRAME_COUNT`: number of final selected frames
- `PLAYBACK_FPS`: intended game playback rate
- `VIDEO_PROVIDER`: available image-to-video model or workflow
- `VIDEO_OUTPUT`: path where the generated video will be saved
- `OUTPUT_DIR`: directory for selected PNG frames
- `FRAME_PREFIX`: output filename prefix

Defaults for the current east dash:

```text
ANCHOR_IMAGE = anchors/dash-east.png
ACTION = dash
DIRECTION = east / screen-right
ANIMATION_TYPE = non-looping
TARGET_FRAME_COUNT = 16
PLAYBACK_FPS = 12
VIDEO_OUTPUT = i2v-output/dash-east-source.mp4
OUTPUT_DIR = i2v-output/dash-east-selected
FRAME_PREFIX = dash-east
```

Do not start generation until an image-to-video provider or callable workflow is available. Do not silently substitute ordinary image generation.

## Critical input rule

Pass exactly one visual input to the image-to-video model: the approved directional anchor.

Do not pass:

- a spritesheet
- a pose board
- a grid
- a guide canvas
- a gameplay screenshot
- multiple character references

Additional visual inputs can be blended into the generated clip and damage character identity, background uniformity, or framing.

## Generation principles

- Keep the character in place. The game engine supplies world-space translation.
- Keep the camera fixed.
- Preserve one direction and one body orientation throughout.
- Preserve character identity, rendering style, proportions, palette, face, and silhouette.
- Use a flat chroma background when the provider can preserve one reliably.
- Generate motion only; do not generate engine-side VFX.
- Prefer the shortest practical clip, usually around 4 seconds.
- Prefer 24 or 30 source FPS so there are enough frames to choose from.
- Generate one action per clip.
- Preserve the original aspect ratio and framing.

## East-dash prompt

Use this prompt for the current ghost:

```text
Animate this single friendly cartoon ghost performing an immediate eastward
dash for a 2D isometric-perspective game.

The ghost must face generally toward the viewer while remaining subtly biased
toward east, screen-right, for the entire clip. Preserve the exact identity,
front-facing body orientation, proportions, white-to-light-gray shading,
smooth black outline, two black oval eyes, small curved smile, thin curved arm
lines, and four-point lower silhouette from the input image.

The dash starts immediately. There is no anticipation, wind-up, idle pause,
braking, recovery, or return to neutral. The full useful motion is active
high-speed travel.

Keep the character locked to the same position in the frame. The game engine
will provide translation. Communicate speed only through controlled forward
lean, horizontal squash and stretch, asymmetric compression, elastic body
motion, and modest motion smears that remain attached to the body.

Keep both eyes, the smile, and both arm lines visible. Keep the character
recognizable in every frame. Preserve apparent volume. Do not rotate into a
side profile, three-quarter body view, or different camera angle.

Keep the camera completely fixed and centered. Keep framing and scale
unchanged. Keep the complete character visible with generous padding.

Use a perfectly flat solid #00FF00 chroma-green background with no floor,
room, horizon, perspective grid, texture, lighting variation, cast shadow,
reflection, or environment.

One character only. No props, labels, arrows, text, watermark, extra limbs,
costume changes, detached afterimages, ectoplasm, wisps, particles, smoke,
sparks, glow, aura, speed lines, impacts, camera movement, zoom, shake,
world-space translation, vertical travel, diagonal travel, westward travel,
turning, or scene change.
```

## Generic prompt template

For another animation, adapt this template without weakening identity and camera constraints:

```text
Animate this single character performing {ACTION} for a 2D
isometric-perspective game.

The character must maintain {DIRECTION_DESCRIPTION} for the entire clip.
Preserve the exact identity, body orientation, proportions, palette, face,
costume, rendering style, and silhouette from the input image.

Animation timing:
{TIMING_DESCRIPTION}

Motion:
{MOTION_DESCRIPTION}

Keep the character locked to the same position in the frame. The game engine
supplies world-space translation. Keep the camera completely fixed and
centered. Keep framing and scale unchanged. Keep the complete character visible
with generous padding.

Keep the same flat chroma background throughout. Do not create a floor, room,
horizon, outdoor scene, perspective grid, shadow plane, reflection, or
environment.

One character only. No props, text, labels, arrows, watermark, extra
characters, camera movement, zoom, shake, turn, direction change, scene change,
or engine-side visual effects.
```

## Provider settings

Use the closest available equivalents:

```text
Mode: image-to-video
Duration: shortest practical duration, preferably about 4 seconds
Resolution: at least 512×512; prefer 1024×1024 when affordable
Aspect ratio: match the anchor image
Camera motion: off / fixed
Prompt adherence: high
Image or identity adherence: high
Motion strength: moderate
Loop generation: off for dash and other one-shot actions
Seed: record it when the provider exposes one
```

Do not assume every provider exposes these names. Record the actual model and settings used.

## Generation acceptance gate

Do not extract final frames from a clip unless:

- exactly one character is present
- identity remains recognizable
- the character does not turn or change direction
- the camera remains fixed
- framing and scale remain reasonably stable
- no body part is clipped
- the background remains removable
- the action contains one usable contiguous motion interval
- no unwanted scene, prop, shadow plane, text, or VFX appears

Reject and reroll clips with severe identity drift, camera movement, clipping, direction changes, or no usable contiguous interval.

## Local tool requirements

Frame extraction uses `ffmpeg` and `ffprobe`.

Check first:

```bash
ffmpeg -version
ffprobe -version
```

If either command is unavailable, ask the user for permission to install FFmpeg. On macOS with Homebrew:

```bash
brew install ffmpeg
```

Do not install system software without approval.

## Inspect the source video

Run:

```bash
ffprobe -v error \
  -select_streams v:0 \
  -show_entries stream=width,height,r_frame_rate,avg_frame_rate,nb_frames,duration \
  -of default=noprint_wrappers=1 \
  "i2v-output/dash-east-source.mp4"
```

Record:

- source width and height
- source frame rate
- duration
- reported frame count, when available

## Extract every source frame

Preserve the video and extract lossless PNG frames:

```bash
mkdir -p "i2v-output/dash-east-all-frames"

ffmpeg -i "i2v-output/dash-east-source.mp4" \
  -vsync 0 \
  "i2v-output/dash-east-all-frames/source-%05d.png"
```

Do not resize, crop, remove the background, or alter timing during this stage.

## Create a source contact sheet

Create a compact visual index for selecting the useful interval:

```bash
ffmpeg -i "i2v-output/dash-east-source.mp4" \
  -vf "fps=6,scale=256:-1,tile=6x0:padding=4:margin=4" \
  -frames:v 1 \
  "i2v-output/dash-east-source-contact-sheet.png"
```

If the resulting sheet is too large or too sparse, adjust only the preview `fps` and tile columns. Do not alter the source video.

## Select the motion interval

### Non-looping animation

For a dash or other one-shot action:

1. Find the first frame where the requested action is clearly active.
2. Find the final frame before the character brakes, recovers, changes action, drifts badly, turns, or loses identity.
3. Use one contiguous interval between those two frames.
4. The interval must contain at least `TARGET_FRAME_COUNT` source frames.
5. Do not combine unrelated sections of the clip.

For the east dash, frame 1 of the selected sequence must already show active travel and the final selected frame must still show active travel.

### Looping animation

For idle, float, or walk:

1. Find a readable starting pose.
2. Continue until the same phase and pose recurs.
3. Use the interval from the first occurrence up to, but not including, the duplicate closing pose.
4. Confirm the last selected frame transitions cleanly into the first.

## Evenly sample the selected interval

Set:

```text
START_FRAME = first source-frame number in the accepted interval
END_FRAME = last source-frame number in the accepted interval, inclusive
TARGET_FRAME_COUNT = requested number of final frames
```

The interval must satisfy:

```text
END_FRAME - START_FRAME + 1 >= TARGET_FRAME_COUNT
```

Use Python to choose deterministic, evenly spaced source frames and copy them without resampling:

```python
from pathlib import Path
import shutil

ALL_FRAMES_DIR = Path("i2v-output/dash-east-all-frames")
OUTPUT_DIR = Path("i2v-output/dash-east-selected")
FRAME_PREFIX = "dash-east"

START_FRAME = 1
END_FRAME = 48
TARGET_FRAME_COUNT = 16
ALLOW_OVERWRITE = False

if START_FRAME < 1:
    raise ValueError("START_FRAME must be at least 1.")

if END_FRAME < START_FRAME:
    raise ValueError("END_FRAME must be greater than or equal to START_FRAME.")

interval_count = END_FRAME - START_FRAME + 1
if interval_count < TARGET_FRAME_COUNT:
    raise ValueError(
        f"Selected interval has {interval_count} frames but "
        f"{TARGET_FRAME_COUNT} are required."
    )

source_indices = [
    round(
        START_FRAME
        + index * (END_FRAME - START_FRAME) / (TARGET_FRAME_COUNT - 1)
    )
    for index in range(TARGET_FRAME_COUNT)
]

if len(set(source_indices)) != TARGET_FRAME_COUNT:
    raise ValueError("Sampling produced duplicate source frames.")

sources = [
    ALL_FRAMES_DIR / f"source-{source_index:05d}.png"
    for source_index in source_indices
]

missing = [path for path in sources if not path.is_file()]
if missing:
    raise FileNotFoundError(f"Missing source frame: {missing[0]}")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
outputs = [
    OUTPUT_DIR / f"{FRAME_PREFIX}-{index:03d}.png"
    for index in range(TARGET_FRAME_COUNT)
]

existing = [path for path in outputs if path.exists()]
if existing and not ALLOW_OVERWRITE:
    raise FileExistsError(f"Refusing to overwrite: {existing[0]}")

for source, output in zip(sources, outputs):
    shutil.copy2(source, output)
    print(f"{source.name} -> {output.name}")

print(f"Selected source indices: {source_indices}")
print(f"Frames written: {len(outputs)}")
print(f"Output: {OUTPUT_DIR}")
```

When `TARGET_FRAME_COUNT` is `1`, copy the single selected frame directly instead of using the formula.

## Create the selected-frame preview

Build a GIF from the selected frames at the intended playback rate:

```bash
ffmpeg \
  -framerate 12 \
  -i "i2v-output/dash-east-selected/dash-east-%03d.png" \
  -vf "split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" \
  -loop 0 \
  "i2v-output/dash-east-selected-preview.gif"
```

This GIF is for review only. PNG files remain the production source.

## Selected-frame validation

Before proceeding:

1. Confirm the selected frame count is exact.
2. Confirm every selected frame has identical dimensions.
3. Confirm filenames run from `000` without gaps.
4. Inspect the GIF at `PLAYBACK_FPS`.
5. Confirm the motion reads as the requested action.
6. Confirm no frame is duplicated accidentally.
7. Confirm character identity remains acceptable.
8. Confirm no camera movement, scale jump, turn, or clipping occurs.
9. Confirm the background can be removed.
10. For non-looping actions, confirm no anticipation or recovery was included unless requested.
11. For looping actions, confirm the last-to-first transition is clean.

If validation fails, first choose a better interval from the same video. Reroll the video only when no usable interval exists.

## Continue through the existing pipeline

After frame selection:

1. Run `Remove Background` on `OUTPUT_DIR`.
2. Save transparent frames into a new directory.
3. Run `Normalize Images` on the transparent directory.
4. Review the normalized contact sheet and GIF.
5. Integrate only after normalization validation passes.

Do not build the final atlas from unnormalized video frames.

## Completion report

Report:

- provider and model
- prompt used
- generation settings and seed, when available
- anchor image
- source-video path
- source dimensions, FPS, duration, and frame count
- accepted source-frame interval
- selected source-frame indices
- target frame count
- playback FPS
- selected-frame directory
- source contact-sheet path
- selected GIF path
- any identity, camera, background, or motion warnings

## Limitations

- Image-to-video improves temporal motion but does not guarantee exact character identity.
- Video compression may contaminate chroma colors and make simple keying less reliable.
- Some models introduce camera motion even when explicitly prohibited.
- Even sampling preserves timing uniformly; hand-picked timing may look better for highly stylized actions.
- Alpha removal and normalization remain mandatory.
- For this ghost dash, full alpha-bound centering may react to long attached smears. Review body stability during normalization.

## Source adaptation

This workflow adapts the image-to-video and frame-picking method described in:

https://github.com/chongdashu/ai-game-spritesheets/blob/main/prompts/05-walk-cycle-i2v.md

The original method targets looping walk cycles. This version supports both loops and non-looping actions and defaults to the project’s 16-frame eastward ghost dash.
