# Slice a Spritesheet into Individual Frames

## Objective

Slice one spritesheet into evenly sized individual PNG frames. Validate the sheet before slicing, preserve the source image, and write the frames in animation order.

## Required inputs

Determine these values before processing, ask the user to provide them:

- `INPUT_SHEET`: path to the spritesheet
- `OUTPUT_DIR`: directory for the extracted frames
- `COLUMNS`: number of columns in the sheet
- `ROWS`: number of rows in the sheet
- `FRAME_PREFIX`: output filename prefix, such as `dash-east`

If the column or row count is not provided and cannot be determined reliably, ask the user. Do not guess based only on the number of visible characters.

## Rules

- Do not modify or delete the source spritesheet.
- The sheet width must be evenly divisible by `COLUMNS`.
- The sheet height must be evenly divisible by `ROWS`.
- IF padding is an option, prompt the user if they want to pad, otherwise stop with a clear error if either dimension is not evenly divisible.
- Read frames left to right, then top to bottom.
- Use zero-padded frame numbers beginning at `000`.
- Preserve alpha transparency and color information.
- Do not resize, resample, trim, rotate, or otherwise alter individual frames.
- Create the output directory if it does not exist.
- Do not overwrite existing frames unless the user explicitly permits it.

## Procedure

1. Confirm that Python 3 is available:

   ```bash
   python3 --version
   ```

2. Check whether Pillow is installed:

   ```bash
   python3 -c "import PIL; print(PIL.__version__)"
   ```

3. If Pillow is missing, install it:

   ```bash
   python3 -m pip install Pillow
   ```

4. Use the following Python script. Replace the configuration values at the top before running it.

   ```python
   from pathlib import Path
   from PIL import Image

   INPUT_SHEET = Path("path/to/spritesheet.png")
   OUTPUT_DIR = Path("path/to/output/frames")
   COLUMNS = 4
   ROWS = 4
   FRAME_PREFIX = "dash-east"
   ALLOW_OVERWRITE = False

   if not INPUT_SHEET.is_file():
       raise FileNotFoundError(f"Spritesheet not found: {INPUT_SHEET}")

   if COLUMNS <= 0 or ROWS <= 0:
       raise ValueError("COLUMNS and ROWS must both be positive integers.")

   with Image.open(INPUT_SHEET) as sheet:
       sheet.load()
       width, height = sheet.size

       if width % COLUMNS != 0:
           raise ValueError(
               f"Sheet width {width}px is not evenly divisible by "
               f"{COLUMNS} columns."
           )

       if height % ROWS != 0:
           raise ValueError(
               f"Sheet height {height}px is not evenly divisible by "
               f"{ROWS} rows."
           )

       frame_width = width // COLUMNS
       frame_height = height // ROWS
       frame_count = COLUMNS * ROWS
       digits = max(3, len(str(frame_count - 1)))

       OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

       output_paths = [
           OUTPUT_DIR / f"{FRAME_PREFIX}-{index:0{digits}d}.png"
           for index in range(frame_count)
       ]

       existing = [path for path in output_paths if path.exists()]
       if existing and not ALLOW_OVERWRITE:
           preview = "\n".join(f"- {path}" for path in existing[:10])
           raise FileExistsError(
               "Refusing to overwrite existing frame files. "
               "Use a new output directory or set ALLOW_OVERWRITE = True.\n"
               f"{preview}"
           )

       for index, output_path in enumerate(output_paths):
           row = index // COLUMNS
           column = index % COLUMNS
           left = column * frame_width
           top = row * frame_height
           box = (
               left,
               top,
               left + frame_width,
               top + frame_height,
           )

           frame = sheet.crop(box)
           frame.save(output_path, format="PNG")

   print(f"Source: {INPUT_SHEET}")
   print(f"Sheet size: {width}x{height}px")
   print(f"Grid: {COLUMNS} columns x {ROWS} rows")
   print(f"Frame size: {frame_width}x{frame_height}px")
   print(f"Frames written: {frame_count}")
   print(f"Output: {OUTPUT_DIR}")
   ```

## Validation

After slicing:

1. Confirm that the number of files equals `COLUMNS × ROWS`.
2. Confirm that every frame has the calculated dimensions.
3. Confirm that frame `000` is the top-left cell.
4. Confirm that numbering proceeds left to right and then top to bottom.
5. Visually inspect the first, middle, and final frames for clipping or incorrect boundaries.
6. Report the source dimensions, grid dimensions, frame dimensions, frame count, and output directory.

## Important limitation

If a sheet is 1254×1254 pixels, it cannot be divided exactly into a 4×4 grid because 1254 is not divisible by 4. Do not silently crop, pad, or resize such a sheet. Ask the user which correction they prefer.
