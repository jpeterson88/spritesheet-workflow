# Finalize Approved Animation Assets

## Objective

Take the user-approved normalized frames and preview GIF from step 005, rebuild
the production spritesheet from only the approved frames, copy the approved GIF
to the final output folder, validate both deliverables, and remove the
disposable workspace.

Run this step only after the user explicitly approves the step-005 preview.

## Required inputs

- `ANIMATION_NAME`: filesystem-safe animation slug
- `WORK_DIR`: `work/<animation-name>`
- `FRAMES_DIR`: `work/<animation-name>/005-normalized/frames`
- `APPROVED_GIF`: `work/<animation-name>/005-normalized/<animation-name>-preview.gif`
- `OUTPUT_DIR`: `output/<animation-name>`
- `COLUMNS`: final spritesheet column count
- `ROWS`: final spritesheet row count

Infer the frame order from zero-padded filenames. If the user removed frames,
use the remaining files in lexical order and renumber only in the final
spritesheet placement; do not rename approved source frames merely to hide
gaps.

## Final output contract

Keep exactly these deliverables:

```text
output/<animation-name>/
├── <animation-name>.gif
└── <animation-name>-spritesheet.png
```

The GIF is the exact approved step-005 preview. The spritesheet is rebuilt from
the exact approved normalized PNG frames.

## Grid selection

- Require `COLUMNS × ROWS` to equal the approved frame count.
- If frames were removed and the old layout no longer fits, choose a compact
  rectangular layout when the user has not specified one.
- Prefer fewer empty cells over preserving the rejected source layout.
- Never add transparent placeholder cells without telling the user.

Examples:

```text
12 frames -> 4 × 3
16 frames -> 4 × 4
8 frames  -> 4 × 2
6 frames  -> 3 × 2
```

## Procedure

Use Pillow to validate and pack the approved frames:

```python
from pathlib import Path
from shutil import copy2
from PIL import Image

ANIMATION_NAME = "dash-east"
WORK_DIR = Path("work") / ANIMATION_NAME
FRAMES_DIR = WORK_DIR / "005-normalized" / "frames"
APPROVED_GIF = (
    WORK_DIR / "005-normalized" / f"{ANIMATION_NAME}-preview.gif"
)
OUTPUT_DIR = Path("output") / ANIMATION_NAME
COLUMNS = 4
ROWS = 3
ALLOW_OVERWRITE = False

if not FRAMES_DIR.is_dir():
    raise NotADirectoryError(f"Approved frames not found: {FRAMES_DIR}")

if not APPROVED_GIF.is_file():
    raise FileNotFoundError(f"Approved GIF not found: {APPROVED_GIF}")

frame_paths = sorted(FRAMES_DIR.glob(f"{ANIMATION_NAME}-*.png"))
if not frame_paths:
    raise FileNotFoundError(f"No approved frames found in: {FRAMES_DIR}")

if COLUMNS <= 0 or ROWS <= 0:
    raise ValueError("COLUMNS and ROWS must be positive integers.")

if len(frame_paths) != COLUMNS * ROWS:
    raise ValueError(
        f"{len(frame_paths)} approved frames do not fill a "
        f"{COLUMNS}x{ROWS} spritesheet."
    )

frames = []
frame_size = None

for path in frame_paths:
    with Image.open(path) as opened:
        if "A" not in opened.getbands():
            raise ValueError(f"Approved frame has no alpha channel: {path}")

        frame = opened.convert("RGBA")

        if frame_size is None:
            frame_size = frame.size
        elif frame.size != frame_size:
            raise ValueError(
                f"Frame size mismatch: {path} is {frame.size}; "
                f"expected {frame_size}."
            )

        frames.append(frame.copy())

cell_width, cell_height = frame_size
sheet = Image.new(
    "RGBA",
    (COLUMNS * cell_width, ROWS * cell_height),
    (0, 0, 0, 0),
)

for index, frame in enumerate(frames):
    column = index % COLUMNS
    row = index // COLUMNS
    sheet.alpha_composite(
        frame,
        (column * cell_width, row * cell_height),
    )

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
sheet_path = OUTPUT_DIR / f"{ANIMATION_NAME}-spritesheet.png"
gif_path = OUTPUT_DIR / f"{ANIMATION_NAME}.gif"

existing = [path for path in (sheet_path, gif_path) if path.exists()]
if existing and not ALLOW_OVERWRITE:
    raise FileExistsError(
        f"Refusing to overwrite final output: {existing[0]}"
    )

sheet.save(sheet_path, format="PNG")
copy2(APPROVED_GIF, gif_path)

print(f"Approved frames: {len(frames)}")
print(f"Frame size: {cell_width}x{cell_height}px")
print(f"Grid: {COLUMNS}x{ROWS}")
print(f"Spritesheet: {sheet_path}")
print(f"GIF: {gif_path}")
```

## Validation

Before cleanup, verify:

1. The final GIF is byte-for-byte identical to the approved preview GIF.
2. The spritesheet contains every approved frame exactly once and in order.
3. Every frame is RGBA and has the same dimensions.
4. Spritesheet dimensions equal:

   ```text
   COLUMNS × frame width
   ROWS × frame height
   ```

5. No approved frame was resized, trimmed, recolored, or re-anchored.
6. Opening the final sheet shows no clipping, bleeding, or reordered frames.

## Cleanup

After validation succeeds:

- Delete only `work/<animation-name>/`.
- Keep `anchors/`.
- Keep `output/<animation-name>/<animation-name>.gif`.
- Keep `output/<animation-name>/<animation-name>-spritesheet.png`.
- Keep instruction files and reusable tooling.
- Do not keep contact sheets, rejected generations, sliced source frames,
  transparent intermediates, normalization reports, alternate GIFs, or retry
  folders.
- Do not delete another animation's workspace.

If final validation fails, do not clean up. Return to step 005 with the current
workspace intact.

## Completion report

Report only:

- approved frame count
- frame size
- final grid and spritesheet dimensions
- final GIF path
- final spritesheet path
- confirmation that the animation workspace was removed
