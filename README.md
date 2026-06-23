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
