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

Steps 003, 004, and 005 run automatically after the generated spritesheet is
approved. The workflow pauses only at these review checkpoints:

1. The generated spritesheet from step 001.
2. The normalized animation GIF and frames from step 005.

At the second checkpoint, the user may remove or reorder frames, adjust
anchors, request border cleanup, or fix clipping, bleeding, and chroma residue.
Rebuild the preview after every revision and continue until it is approved.

## Workspace layout

Use one disposable workspace per animation:

```text
work/<animation-name>/
├── 001-generated/
│   └── <animation-name>-spritesheet.png
├── 003-sliced/
├── 004-transparent/
└── 005-normalized/
    ├── frames/
    ├── <animation-name>-contact-sheet.png
    └── <animation-name>-preview.gif
```

Do not create top-level retry directories such as `pass-02`, `corrected`, or
`v2`. Replace rejected artifacts within the appropriate numbered stage
directory. Never modify another animation's workspace.

User-provided source images belong in `anchors/` and must be preserved.

## Final output

After step 005 is approved, step 006 creates:

```text
output/<animation-name>/
├── <animation-name>.gif
└── <animation-name>-spritesheet.png
```

The final GIF must be the approved preview. The final spritesheet must be
rebuilt from the exact approved normalized frames.

After validating both files, delete only `work/<animation-name>/`. Do not keep
rejected generations, sliced frames, transparent intermediates, alternate
previews, reports, contact sheets, or temporary backups.

## Instruction index

- `001-generate-spritesheet.md`: generate and iterate on an initial sheet
- `002-generate-animation-i2v.md`: alternate image-to-video workflow
- `003-slice-spritesheet.md`: split a sheet into ordered frame images
- `004-remove-backgrounds-with-pillow.md`: convert chroma backgrounds to alpha
- `005-normalize-animation-frames.md`: normalize scale, anchors, and previews
- `006-finalize-animation-assets.md`: package approved assets and clean up
