# Batch-Remove Image Backgrounds with Pillow

## Objective

Remove a flat chroma-key background from every supported image in an input folder and save transparent PNG copies in a separate output folder.

The default key color is bright green `#00FF00`. Preserve the source images.

When invoked from the spritesheet pipeline, run automatically after step 003
and continue directly to step 005 after validation.

## Required inputs

Determine these values before processing, ask the user to provide them:

- `INPUT_DIR`: folder containing source images
- `OUTPUT_DIR`: folder for transparent PNG results; default
  `work/<animation-name>/004-transparent`
- `KEY_COLOR`: background color to remove; default `(0, 255, 0)`
- `TOLERANCE`: allowed per-channel color difference; default `20`

Use a low tolerance for a perfectly uniform background. Raise it cautiously when antialiasing or compression creates slightly different green pixels.

## Rules

- Check whether Python 3 and Pillow are installed before processing.
- If Pillow is missing, install it and then continue automatically.
- Process all supported images directly inside `INPUT_DIR`.
- Supported extensions: `.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`, and `.tif`/`.tiff`.
- Preserve every source file.
- Save results as PNG so alpha transparency is retained.
- Do not recursively process subfolders unless the user requests it.
- Do not read generated files back from `OUTPUT_DIR` when it is inside `INPUT_DIR`.
- Do not overwrite existing output files unless the user explicitly permits it.
- Keep original image dimensions.
- Report failed files without discarding successful results.
- For pipeline retries, clear and reuse only the current animation's
  `004-transparent` directory instead of creating pass/version directories.

## Procedure

### 1. Confirm Python 3

```bash
python3 --version
```

If Python 3 is unavailable, stop and report that it must be installed.

### 2. Check for Pillow and install it if missing

Run:

```bash
if python3 -c "import PIL" 2>/dev/null; then
  echo "Pillow is already installed."
else
  echo "Pillow is not installed; installing it now."
  python3 -m pip install Pillow
fi
```

Then verify the installation:

```bash
python3 -c "import PIL; print(f'Pillow {PIL.__version__} is ready')"
```

If installation fails because the environment is externally managed, create a project-local virtual environment instead:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install Pillow
```

Run the remaining commands from that activated environment.

### 3. Process the folder

Replace the configuration values at the top of this script before running it:

```python
from pathlib import Path
from PIL import Image

INPUT_DIR = Path("path/to/input/images")
OUTPUT_DIR = Path("path/to/output/images")
KEY_COLOR = (0, 255, 0)
TOLERANCE = 20
ALLOW_OVERWRITE = False

SUPPORTED_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
}

if not INPUT_DIR.is_dir():
    raise NotADirectoryError(f"Input directory not found: {INPUT_DIR}")

if TOLERANCE < 0 or TOLERANCE > 255:
    raise ValueError("TOLERANCE must be between 0 and 255.")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

input_dir_resolved = INPUT_DIR.resolve()
output_dir_resolved = OUTPUT_DIR.resolve()

if input_dir_resolved == output_dir_resolved:
    raise ValueError("INPUT_DIR and OUTPUT_DIR must be different directories.")

sources = sorted(
    path
    for path in INPUT_DIR.iterdir()
    if path.is_file()
    and path.suffix.lower() in SUPPORTED_EXTENSIONS
)

if not sources:
    raise FileNotFoundError(f"No supported images found in: {INPUT_DIR}")

processed = 0
failed = []

for source_path in sources:
    output_path = OUTPUT_DIR / f"{source_path.stem}.png"

    if output_path.exists() and not ALLOW_OVERWRITE:
        failed.append((source_path, "output already exists"))
        continue

    try:
        with Image.open(source_path) as image:
            rgba = image.convert("RGBA")
            pixels = rgba.load()
            width, height = rgba.size

            for y in range(height):
                for x in range(width):
                    red, green, blue, alpha = pixels[x, y]

                    matches_key = (
                        abs(red - KEY_COLOR[0]) <= TOLERANCE
                        and abs(green - KEY_COLOR[1]) <= TOLERANCE
                        and abs(blue - KEY_COLOR[2]) <= TOLERANCE
                    )

                    if matches_key:
                        pixels[x, y] = (red, green, blue, 0)

            rgba.save(output_path, format="PNG")
            processed += 1
            print(f"Processed: {source_path.name} -> {output_path.name}")

    except Exception as error:
        failed.append((source_path, str(error)))

print(f"\nImages processed: {processed}")
print(f"Images failed or skipped: {len(failed)}")
print(f"Output directory: {OUTPUT_DIR}")

if failed:
    print("\nFailures:")
    for path, reason in failed:
        print(f"- {path.name}: {reason}")
```

## Validation

After processing:

1. Confirm that every successful output is a PNG with an alpha channel.
2. Confirm that output dimensions match the corresponding source dimensions.
3. Inspect corners and other known background areas; they should be fully transparent.
4. Inspect the character outline for green fringe or accidentally removed character colors.
5. Compare the number of source images with the number processed, skipped, and failed.
6. Report the input folder, output folder, key color, tolerance, and result counts.

## Automatic handoff

If step 001 started the pipeline and validation succeeds, do not ask the user
for approval here. Run step 005 with:

```text
INPUT_DIR = work/<animation-name>/004-transparent
OUTPUT_DIR = work/<animation-name>/005-normalized/frames
```

Stop only if background removal fails validation. Green fringe, lost subject
colors, or opaque corners must be corrected before normalization.

## Edge-quality note

The basic script makes matching pixels fully transparent. It does not create a
soft alpha transition or remove green spill from antialiased edges. If visible
green fringing remains, use a dedicated chroma-key routine with soft-matte and
despill processing rather than repeatedly increasing `TOLERANCE`; a high
tolerance may erase colors within the subject.

The cleanest fix is usually upstream: generate or assemble the source artwork
with real alpha first, then put the chroma key only behind pixels that should be
fully transparent. Semi-transparent subject edges should retain subject-colored
RGB values instead of being blended against the key color. After removal, audit
visible pixels on a dark background for chroma-colored fringe before continuing
to normalization.
