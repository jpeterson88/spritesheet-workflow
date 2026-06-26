# Game Animation Asset Tools

This repository defines a staged workflow for turning user-provided anchor
images and an animation request into an approved GIF and production
spritesheet.

## Spritesheet workflow

```text
001 Generate spritesheet
        ↓
User reviews generated sheet
        ↓ approved
003 Slice sheet into frames
        ↓ automatic
004 Remove frame backgrounds
        ↓ automatic
005 Normalize and anchor frames
        ↓
User reviews GIF and normalized frames
        ↓ approved
006 Build final assets and clean workspace
```

At the first checkpoint, user can request changes through prompts.

At the second checkpoint, the user may remove or reorder frames, adjust
anchors, request border cleanup, or fix clipping, bleeding, and chroma residue.
Rebuild the preview after every revision and continue until it is approved.


## Final output

After step 005 is approved, step 006 creates:

```text
output/<animation-name>/
├── <animation-name>.gif
└── <animation-name>-spritesheet.png
```

## Batch spritesheet workflow

Use the instructions in `instructions/batch/` when the user wants multiple
spritesheets generated, ranked, and finalized from one config. The batch
workflow preserves the normal single-sheet workflow above.

```text
001 Batch create spritesheets
        ↓
002 Batch stack rank spritesheets
        ↓
003 Batch process ranked candidates
```

Batch inputs are provided as JSON. See:

```text
configs/batch-spritesheet.example.json
```

The batch config is the single request file for a batch run. It tells the
pipeline which prompt to use, how many candidate spritesheets to generate, how
many ranked candidates to keep, and how to validate/process the generated
sheet geometry before ranking and finalization.

Fields:

- `animation_name`: filesystem-safe slug used for disposable and final output
  paths.
- `prompt_path`: repo-relative prompt file used for every generated
  candidate.
- `generation_count`: number of candidate spritesheets to generate.
- `keep_count`: number of ranked candidates to process and finalize.
- `frame_count`: total frames expected in each spritesheet.
- `grid.columns`: number of atlas columns; must satisfy
  `grid.columns * grid.rows == frame_count`.
- `grid.rows`: number of atlas rows; must satisfy
  `grid.columns * grid.rows == frame_count`.
- `frame_size.width`: width of each frame cell in pixels.
- `frame_size.height`: height of each frame cell in pixels.
- `background_color`: chroma-key color expected behind transparent regions;
  defaults to `#00FF00`.
- `fps`: playback rate for generated GIF previews; defaults to `12`.
- `background_tolerance`: chroma-key tolerance used during background removal;
  defaults to `20`.
- `alpha_threshold`: minimum alpha value treated as visible during
  normalization; defaults to `8`.
- `allow_overwrite`: whether to reuse an existing disposable batch workspace;
  defaults to `false`.

Batch work is kept under:

```text
disposable/batch/<animation-name>/
```

Final ranked outputs are written to:

```text
output/batch/<animation-name>/<rank-number>/
├── <animation-name>.gif
└── <animation-name>-spritesheet.png
```

Batch generation still uses the `001` prompt construction and validation
criteria, but it does not pause for user review on each generated candidate.
Rank candidates first, then process only the kept candidates through
`003 -> 006`. Do not automatically clean up `disposable/batch`.
