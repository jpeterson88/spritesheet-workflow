# Batch Create Spritesheets

## Objective

Generate every requested spritesheet candidate from the same JSON config,
prompt, and anchor images. Do not ask the user to review individual
candidates.

This is step 1 of the batch workflow:

```text
001 batch create spritesheets
  -> 002 batch stack rank spritesheets
  -> 003 batch process ranked candidates
```

The batch workflow extends the standard `001 -> 006` flow. It must not change
or replace the normal single-spritesheet approval workflow.

## Required inputs

The user provides a JSON config with:

- `animation_name`: filesystem-safe animation slug
- `prompt_path`: path to a repo prompt file
- `generation_count`: number of candidate spritesheets to generate
- `keep_count`: number of ranked candidates to finalize
- `frame_count`: total animation frames
- `grid.columns` and `grid.rows`
- `frame_size.width` and `frame_size.height`

Optional values:

- `background_color`: default `#00FF00`
- `fps`: default `12`
- `background_tolerance`: default `20`
- `alpha_threshold`: default `8`
- `allow_overwrite`: default `false`; set to `true` only when intentionally
  revising an existing batch output

Anchor images are always loaded from `./anchors`. The identity anchor must be
named `anchor` and the directional anchor must be named `directional-anchor`,
with any supported image extension such as `.png`, `.jpg`, `.jpeg`, or `.webp`.

The grid must satisfy:

```text
grid.columns * grid.rows == frame_count
```

## Workspace layout

All batch work is disposable and must stay under:

```text
disposable/batch/<animation-name>/
```

Do not place generated candidates in `work/`, `generated/`, or `output/`.

Do not automatically delete `disposable/batch/<animation-name>`. The user can
delete it manually or ask for a later cleanup step. Every file in that folder
must be safe to delete.

## Setup

Validate the config and prepare the workspace:

```bash
python3 tools/batch_pipeline.py prepare path/to/config.json
```

This creates:

```text
disposable/batch/<animation-name>/
├── anchors/
├── batch-config.resolved.json
├── candidate-manifest.json
└── 001-generated/
```

The copied anchors in the disposable workspace are for traceability only. The
authoritative anchors remain in `./anchors`.

## Candidate generation

For every candidate, follow the prompt-writing rules in
`instructions/001-generate-spritesheet.md`, with these batch-specific changes:

- Generate exactly `generation_count` candidate spritesheets.
- Do not ask the user to approve individual candidates.
- The image generation step must use the `image_gen` tool.
- Use both required anchors: `./anchors/anchor.*` and
  `./anchors/directional-anchor.*`.
- Preserve all config requirements across every generation attempt.
- Use the same prompt path, anchor roles, output spec, frame count, grid, frame
  size, background color, and hard constraints for every candidate.
- Avoid chroma-matted edges. If a candidate is assembled locally from
  transparent or generated elements, compose the artwork on real alpha first,
  then fill only fully transparent pixels with the configured background color.
  Do not blend semi-transparent subject edges against `#00FF00`; keep those
  edge RGB values in the subject palette so deterministic background removal
  does not leave a green fringe.
- Save each candidate under its manifest path:

```text
disposable/batch/<animation-name>/001-generated/candidate-001/<animation-name>-candidate-001-spritesheet.png
disposable/batch/<animation-name>/001-generated/candidate-002/<animation-name>-candidate-002-spritesheet.png
...
```

## Validation

Before moving to step 002:

1. Confirm that the candidate count equals `generation_count`.
2. Confirm that every generated file exists at the manifest path.
3. Confirm that every candidate has the expected canvas dimensions:

   ```text
   grid.columns * frame_size.width
   grid.rows * frame_size.height
   ```

4. Inspect actual image artifacts when anything looks questionable.
5. For chroma-key candidates, simulate or audit key removal on a dark
   background and reject candidates with visible chroma-colored fringe on
   foreground pixels.
6. Do not run deterministic cleanup here.

## Handoff

After all candidates are generated and basic validation passes, continue to:

```text
instructions/batch/002-batch-stack-rank-spritesheets.md
```
