# Normalize Animation Frames

## Objective

Convert background-removed animation frames into stable, game-ready assets with:

- one fixed canvas size
- one consistent horizontal anchor
- one consistent baseline
- one animation-wide scale relative to an approved character reference
- preserved frame order and intentional pose deformation
- a rebuilt atlas, contact sheet, and animated preview

Normalization must remove accidental image-generation drift without erasing intentional squash, stretch, recoil, or motion smears.

When invoked from the spritesheet pipeline, this is the second user review
checkpoint. Iterate in this same stage until the normalized frames and GIF are
approved, then continue to step 006.

## Required normalization sequence

Before promoting an animation into game assets:

1. Split or recover frames using measured foreground/alpha bounds. Do not trust
   nominal grid borders when artwork crosses a cell boundary.
2. Remove the background and create a real alpha channel.
3. Compare the recovered alpha bounds against this character's approved or
   completed sheets.
4. Normalize the animation-wide visible-body scale and the stable baseline
   inside each runtime cell.
5. Preserve the requested atlas dimensions, frame count, and frame order.
6. Create a contact sheet and GIF preview at the real runtime frame size.

Do not normalize files that only appear transparent against a colored
background.

## Required inputs

Ask the user to provide or confirm:

- `SOURCE_SHEET`: original spritesheet when frames still need recovery
- `INPUT_DIR`: folder containing ordered transparent PNG frames when recovery
  and background removal are already complete
- `OUTPUT_DIR`: folder for normalized frames; default
  `work/<animation-name>/005-normalized/frames`
- `REFERENCE_IMAGE` or `REFERENCE_DIR`: approved/completed character asset used
  to establish scale and anchor conventions
- `CANVAS_WIDTH`: runtime frame width
- `CANVAS_HEIGHT`: runtime frame height
- `ANCHOR_MODE`: `alpha-center`, `body-landmark`, or a supplied pivot
- `TARGET_ANCHOR_X`: horizontal body/pivot anchor on the output canvas
- `TARGET_BOTTOM_Y`: bottom anchor or foot baseline on the output canvas
- `COLUMNS`: number of atlas columns
- `ROWS`: number of atlas rows
- `FRAME_PREFIX`: ordered frame filename prefix
- `FPS`: preview GIF playback rate
- `ALPHA_THRESHOLD`: minimum alpha treated as visible; default `8`

Recommended defaults when the user has not specified anchor positions:

```text
TARGET_ANCHOR_X = CANVAS_WIDTH / 2
TARGET_BOTTOM_Y = CANVAS_HEIGHT - 8% of CANVAS_HEIGHT
ALPHA_THRESHOLD = 8
FPS = 12
```

For a floating character, `TARGET_BOTTOM_Y` means the bottom-most visible point of the character, not a physical foot.

Do not guess canvas dimensions, atlas layout, or the approved scale reference when they cannot be discovered from project files.

## Core rules

- Preserve all input files.
- Process frames in deterministic filename order.
- Require real RGBA transparency.
- Recover complete subjects from the source sheet before normalizing. If a
  subject crosses a nominal cell edge, use connected-component or alpha-bound
  recovery rather than clipping it at the grid border.
- Compute bounds from alpha, not RGB color or the nominal source cell.
- Remove tiny disconnected components unless they are approved detached VFX.
- Use one scale factor for the entire animation.
- Never independently scale every frame to the same height.
- Preserve intentional relative size changes caused by squash, stretch, or smears.
- Align every normalized frame to the same stable horizontal body/pivot anchor
  and visible `bottom_y`.
- Never stretch width and height independently.
- Never crop visible subject pixels silently.
- Stop if the normalized subject cannot fit the target canvas.
- Do not overwrite existing outputs unless the user explicitly permits it.
- Preserve frame count and animation order.
- Rebuild the atlas using the requested grid without resampling normalized frames.
- Store the contact sheet and GIF in
  `work/<animation-name>/005-normalized/`.
- Reuse this directory for every correction. Do not create `pass-*`,
  `corrected`, or `v2` directories.

## Why one animation-wide scale factor matters

AI-generated animations often return at the wrong overall scale, but frames inside an animation may intentionally change height and width.

Incorrect:

```text
Scale every frame until its visible height is identical.
```

That destroys squash-and-stretch animation.

Correct:

```text
Measure a representative animation height.
Compare it with the approved reference height.
Calculate one scale factor.
Apply that same factor to every frame.
```

Use the median visible height of the animation as its representative height. Median is less sensitive to extreme smear or squash frames than maximum or minimum height.

## Procedure

### 1. Verify Python and Pillow

```bash
python3 --version
```

Check for Pillow:

```bash
if python3 -c "import PIL" 2>/dev/null; then
  echo "Pillow is already installed."
else
  echo "Pillow is not installed; installing it now."
  python3 -m pip install Pillow
fi
```

Verify:

```bash
python3 -c "import PIL; print(f'Pillow {PIL.__version__} is ready')"
```

If the environment prevents installation, create and activate a local virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install Pillow
```

### 2. Recover complete frames when needed

If `SOURCE_SHEET` is provided:

1. Build a foreground mask from alpha or the known chroma color.
2. Find connected foreground components across the complete sheet.
3. Require the number of major components to match the expected frame count.
4. Assign components to atlas order by their original row and column positions.
5. Crop each complete component with safe padding.
6. Exclude neighboring components and tiny detached artifacts.

Do not slice at nominal grid borders when a component crosses them.

### 3. Remove and validate the background

Use a soft alpha matte and color despill when the source has antialiased edges.
A hard exact-color deletion is insufficient when green or magenta contaminates
the character outline.

Validate that:

- corners are transparent
- the subject has opaque and partially transparent edge pixels
- no chroma-colored fringe remains on visible pixels
- no neighboring frame fragments remain

### 4. Validate source frames

Before changing anything:

- confirm the input folder exists
- collect only ordered PNG frames matching `FRAME_PREFIX`
- confirm the expected frame count equals `COLUMNS × ROWS`
- confirm every image has an alpha channel
- confirm every frame contains visible pixels above `ALPHA_THRESHOLD`
- confirm output paths will not overwrite existing files

Treat pixels with alpha greater than `ALPHA_THRESHOLD` as foreground.

### 5. Measure alpha bounds and stable landmarks

For each frame, measure:

```text
left
top
right
bottom
visible_width
visible_height
center_x
bottom_y
```

Use an exclusive right and bottom bound:

```text
visible_width  = right - left
visible_height = bottom - top
center_x       = (left + right) / 2
bottom_y       = bottom
```

Record these measurements before normalization so drift can be reported.

Also measure the configured stable landmark:

- `alpha-center`: center of the full visible alpha bounds
- `body-landmark`: a repeatable feature such as eye midpoint, head center, torso
  center, or another stable body region
- supplied pivot: authored pivot coordinates or metadata

Use `alpha-center` only when the silhouette is reasonably symmetric. For a dash
with an asymmetric trailing smear, use `body-landmark` or an authored pivot so
the smear does not move the perceived character center.

### 6. Determine the animation-wide scale

Measure the approved `REFERENCE_IMAGE` or completed `REFERENCE_DIR` using the
same alpha threshold and the same landmark convention.

Calculate:

```text
animation_median_height = median(all input visible heights)
scale = reference_visible_height / animation_median_height
```

If the animation is already approved at its current scale, use:

```text
scale = 1.0
```

Ask the user before applying a surprisingly large correction. Treat a scale outside `0.75–1.25` as suspicious unless the source is known to require it.

Apply the same scale to every frame with high-quality Lanczos resampling.

### 7. Re-measure and place each frame

After scaling each complete RGBA frame:

1. Find its new alpha bounding box.
2. Crop to that alpha bounding box.
3. Create a fresh transparent output canvas.
4. Paste the cropped foreground so:

   ```text
   stable body/pivot anchor X = TARGET_ANCHOR_X
   foreground bottom Y = TARGET_BOTTOM_Y
   ```

Placement:

```text
paste_x = round(TARGET_ANCHOR_X - local_anchor_x)
paste_y = round(TARGET_BOTTOM_Y - visible_height)
```

Use the foreground image as its own alpha mask when pasting.

If `paste_x`, `paste_y`, or the opposite edges fall outside the target canvas, stop and report the affected frame. Do not crop it automatically.

### 8. Preserve animation intent

The fixed anchor removes accidental translation but does not guarantee that every animation should use the same type of anchor.

Default for symmetric animations:

```text
horizontal anchor = alpha-bounds center
vertical anchor   = bottom-most visible alpha pixel
```

For directional smears, alpha-center alignment can make the solid body appear
to move forward. Use an approved body landmark or pivot instead. For the ghost,
the midpoint between the two eyes is a useful horizontal landmark when both
eyes remain stable and visible.

### 9. Save normalized frames

Save normalized frames as RGBA PNG files:

```text
FRAME_PREFIX-000.png
FRAME_PREFIX-001.png
FRAME_PREFIX-002.png
...
```

Keep the original frame number and order.

### 10. Rebuild the atlas

Create a transparent atlas:

```text
atlas_width  = COLUMNS × CANVAS_WIDTH
atlas_height = ROWS × CANVAS_HEIGHT
```

Paste normalized frames left to right, then top to bottom. Do not resize frames during atlas construction.

If the frame count does not equal `COLUMNS × ROWS`, stop unless the user explicitly wants unused transparent cells.

### 11. Create validation previews

Create:

- a contact sheet showing all normalized frames in order
- a looping GIF preview at the real normalized frame size

GIF duration:

```text
duration_ms = round(1000 / FPS)
```

The GIF is for inspection only. PNG frames and the PNG atlas remain the production assets.

## User review and iteration

After creating the normalized frames and preview:

1. Present the GIF and, when useful, the contact sheet.
2. Ask the user whether the animation is approved or what should change.
3. Keep iterating in `005-normalized` until the user approves it.
4. The user may remove unwanted frames, request frame reordering, adjust
   anchors, clean borders, fix chroma bleed, or repair clipped/bleeding frames.
5. After every change, rebuild the GIF from the current normalized frame set.
6. Do not keep superseded GIFs, reports, atlases, or discarded frames in
   alternate folders. If temporary backup is needed during an edit, keep it
   inside the current workspace and delete it before presenting the revision.
7. Do not run step 006 until the user explicitly approves the current GIF.

Once approved, run `instructions/006-finalize-animation-assets.md`
automatically.

## Reference implementation

Use this script as a starting point. Replace the configuration values before running it.

```python
from pathlib import Path
from statistics import median
from PIL import Image, ImageDraw

INPUT_DIR = Path("path/to/transparent/frames")
OUTPUT_DIR = Path("path/to/normalized/frames")
REFERENCE_IMAGE = Path("path/to/approved-reference.png")
FRAME_PREFIX = "dash-east"

CANVAS_WIDTH = 314
CANVAS_HEIGHT = 314
ANCHOR_MODE = "alpha-center"
TARGET_ANCHOR_X = CANVAS_WIDTH / 2
TARGET_BOTTOM_Y = CANVAS_HEIGHT - 20

COLUMNS = 4
ROWS = 4
FPS = 12
ALPHA_THRESHOLD = 8
ALLOW_OVERWRITE = False

ATLAS_PATH = OUTPUT_DIR.parent / f"{FRAME_PREFIX}-normalized-atlas.png"
CONTACT_SHEET_PATH = OUTPUT_DIR.parent / f"{FRAME_PREFIX}-contact-sheet.png"
GIF_PATH = OUTPUT_DIR.parent / f"{FRAME_PREFIX}-preview.gif"


def alpha_bbox(image):
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    mask = alpha.point(lambda value: 255 if value > ALPHA_THRESHOLD else 0)
    return mask.getbbox()


def require_foreground(image, label):
    box = alpha_bbox(image)
    if box is None:
        raise ValueError(f"No visible foreground found in {label}")
    return box


def dimensions(box):
    left, top, right, bottom = box
    return right - left, bottom - top


def body_landmark_x(image, box):
    """
    Return the landmark's X coordinate in the complete image.

    Implement this for the character when ANCHOR_MODE is "body-landmark".
    Examples include eye midpoint, head center, torso center, or an authored
    pivot. Do not derive it from a trailing smear.
    """
    raise NotImplementedError(
        "Implement body_landmark_x for this character before continuing."
    )


def local_anchor_x(image, box):
    left, top, right, bottom = box

    if ANCHOR_MODE == "alpha-center":
        return (right - left) / 2

    if ANCHOR_MODE == "body-landmark":
        return body_landmark_x(image, box) - left

    raise ValueError(f"Unsupported ANCHOR_MODE: {ANCHOR_MODE}")


if not INPUT_DIR.is_dir():
    raise NotADirectoryError(f"Input directory not found: {INPUT_DIR}")

if not REFERENCE_IMAGE.is_file():
    raise FileNotFoundError(f"Reference image not found: {REFERENCE_IMAGE}")

if COLUMNS <= 0 or ROWS <= 0:
    raise ValueError("COLUMNS and ROWS must be positive.")

if CANVAS_WIDTH <= 0 or CANVAS_HEIGHT <= 0:
    raise ValueError("Canvas dimensions must be positive.")

sources = sorted(INPUT_DIR.glob(f"{FRAME_PREFIX}-*.png"))
expected_count = COLUMNS * ROWS

if len(sources) != expected_count:
    raise ValueError(
        f"Expected {expected_count} frames for a {COLUMNS}x{ROWS} atlas, "
        f"found {len(sources)}."
    )

with Image.open(REFERENCE_IMAGE) as reference_source:
    reference = reference_source.convert("RGBA")
    reference_box = require_foreground(reference, REFERENCE_IMAGE)
    _, reference_height = dimensions(reference_box)

frames = []
measurements = []

for source in sources:
    with Image.open(source) as opened:
        if "A" not in opened.getbands():
            raise ValueError(f"Frame has no alpha channel: {source}")

        frame = opened.convert("RGBA")
        box = require_foreground(frame, source)
        width, height = dimensions(box)
        left, top, right, bottom = box

        frames.append((source, frame.copy()))
        measurements.append(
            {
                "source": source,
                "width": width,
                "height": height,
                "center_x": (left + right) / 2,
                "bottom_y": bottom,
            }
        )

animation_median_height = median(
    measurement["height"] for measurement in measurements
)
scale = reference_height / animation_median_height

if not 0.75 <= scale <= 1.25:
    raise ValueError(
        f"Calculated scale {scale:.3f} is outside the expected range "
        "0.75–1.25. Confirm the reference image before continuing."
    )

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

output_paths = [
    OUTPUT_DIR / f"{FRAME_PREFIX}-{index:03d}.png"
    for index in range(len(frames))
]
preview_paths = [ATLAS_PATH, CONTACT_SHEET_PATH, GIF_PATH]
existing = [
    path for path in output_paths + preview_paths
    if path.exists()
]

if existing and not ALLOW_OVERWRITE:
    raise FileExistsError(
        f"Refusing to overwrite existing output: {existing[0]}"
    )

normalized_frames = []

for index, (source, frame) in enumerate(frames):
    scaled_width = max(1, round(frame.width * scale))
    scaled_height = max(1, round(frame.height * scale))
    scaled = frame.resize(
        (scaled_width, scaled_height),
        Image.Resampling.LANCZOS,
    )

    box = require_foreground(scaled, source)
    foreground = scaled.crop(box)
    visible_width, visible_height = foreground.size
    anchor_x = local_anchor_x(scaled, box)

    paste_x = round(TARGET_ANCHOR_X - anchor_x)
    paste_y = round(TARGET_BOTTOM_Y - visible_height)

    if (
        paste_x < 0
        or paste_y < 0
        or paste_x + visible_width > CANVAS_WIDTH
        or paste_y + visible_height > CANVAS_HEIGHT
    ):
        raise ValueError(
            f"Normalized foreground does not fit the canvas: {source}; "
            f"foreground={visible_width}x{visible_height}, "
            f"position=({paste_x}, {paste_y}), "
            f"canvas={CANVAS_WIDTH}x{CANVAS_HEIGHT}"
        )

    canvas = Image.new(
        "RGBA",
        (CANVAS_WIDTH, CANVAS_HEIGHT),
        (0, 0, 0, 0),
    )
    canvas.alpha_composite(foreground, (paste_x, paste_y))

    output_path = output_paths[index]
    canvas.save(output_path, format="PNG")
    normalized_frames.append(canvas)

atlas = Image.new(
    "RGBA",
    (COLUMNS * CANVAS_WIDTH, ROWS * CANVAS_HEIGHT),
    (0, 0, 0, 0),
)

for index, frame in enumerate(normalized_frames):
    column = index % COLUMNS
    row = index // COLUMNS
    atlas.alpha_composite(
        frame,
        (column * CANVAS_WIDTH, row * CANVAS_HEIGHT),
    )

atlas.save(ATLAS_PATH, format="PNG")

label_height = 24
contact_sheet = Image.new(
    "RGBA",
    (
        COLUMNS * CANVAS_WIDTH,
        ROWS * (CANVAS_HEIGHT + label_height),
    ),
    (32, 32, 32, 255),
)
draw = ImageDraw.Draw(contact_sheet)

for index, frame in enumerate(normalized_frames):
    column = index % COLUMNS
    row = index // COLUMNS
    x = column * CANVAS_WIDTH
    y = row * (CANVAS_HEIGHT + label_height)
    contact_sheet.alpha_composite(frame, (x, y))
    draw.text((x + 6, y + CANVAS_HEIGHT + 4), f"{index:03d}", fill="white")

contact_sheet.save(CONTACT_SHEET_PATH, format="PNG")

gif_frames = [
    Image.new("RGBA", frame.size, (32, 32, 32, 255))
    for frame in normalized_frames
]

for background, frame in zip(gif_frames, normalized_frames):
    background.alpha_composite(frame)

gif_frames[0].save(
    GIF_PATH,
    save_all=True,
    append_images=gif_frames[1:],
    duration=round(1000 / FPS),
    loop=0,
    disposal=2,
)

print(f"Frames normalized: {len(normalized_frames)}")
print(f"Reference visible height: {reference_height}px")
print(f"Animation median visible height: {animation_median_height}px")
print(f"Global scale: {scale:.4f}")
print(f"Canvas: {CANVAS_WIDTH}x{CANVAS_HEIGHT}")
print(
    f"Anchor: mode={ANCHOR_MODE}, "
    f"x={TARGET_ANCHOR_X}, bottom_y={TARGET_BOTTOM_Y}"
)
print(f"Normalized frames: {OUTPUT_DIR}")
print(f"Atlas: {ATLAS_PATH}")
print(f"Contact sheet: {CONTACT_SHEET_PATH}")
print(f"GIF: {GIF_PATH}")
```

## Validation

After processing, verify all of the following:

1. The normalized frame count matches the input frame count.
2. Every normalized frame is RGBA and exactly the target canvas size.
3. Every frame has transparent corners.
4. Every frame’s configured body/pivot landmark is aligned to
   `TARGET_ANCHOR_X`, allowing at most one pixel of rounding difference.
5. Every frame’s alpha-bounds bottom is aligned to `TARGET_BOTTOM_Y`.
6. No foreground pixel touches or crosses a canvas edge.
7. The atlas dimensions equal:

   ```text
   COLUMNS × CANVAS_WIDTH
   ROWS × CANVAS_HEIGHT
   ```

8. Atlas order is left to right, then top to bottom.
9. The GIF has the expected frame count and playback rate.
10. The contact sheet and GIF show no accidental drift.
11. Intentional squash, stretch, and smears remain visible.
12. Compare the normalized animation with the approved idle or walk reference and confirm there is no unintended scale jump.
13. Confirm no frame contains pixels recovered from a neighboring atlas cell.
14. Confirm visible antialiased edge pixels are neutral rather than
    chroma-colored.

Do not promote the animation into game assets if validation fails.

## Completion report

Report:

- input directory
- reference image
- frame count
- original median visible height
- reference visible height
- global scale factor
- canvas size
- anchor coordinates
- atlas grid and dimensions
- FPS
- normalized-frame directory
- atlas path
- contact-sheet path
- GIF path
- any clipping, scale, alpha, or anchor warnings
- whether the user approved the preview and step 006 was started

## Important limitations

- Alpha-bound centering cannot distinguish a character body from a long intentional smear.
- Bottom alignment assumes the bottom silhouette is the desired gameplay anchor.
- Loose translucent effects may affect alpha bounds. Raise `ALPHA_THRESHOLD` cautiously or normalize the body separately from VFX.
- Cross-animation normalization is only reliable when all animations use the same approved reference and anchor convention.
- This process corrects scale and placement. It does not repair inconsistent drawing, anatomy, lighting, or frame-to-frame character identity.
