# AGENTS.md

## Project overview

This repository contains agent-run workflows for producing game animation
assets from user-provided anchor images.

The standard spritesheet workflow is:

```text
001 generate → user approval → 003 slice → 004 remove background
→ 005 normalize → user approval → 006 finalize and clean up
```

Read `README.md` before running a workflow. It defines the pipeline, review
checkpoints, workspace layout, final outputs, and cleanup policy.

## Instruction routing

Read and follow the applicable file in `instructions/`:

- Spritesheet generation from anchor images:
  `001-generate-spritesheet.md`
- Image-to-video animation (Currently non-functioning):
  `002-generate-animation-i2v.md`
- Spritesheet slicing:
  `003-slice-spritesheet.md`
- Chroma background removal:
  `004-remove-backgrounds-with-pillow.md`
- Frame normalization and preview:
  `005-normalize-animation-frames.md`
- Final spritesheet packaging and cleanup:
  `006-finalize-animation-assets.md`
- Batch spritesheet generation, ranking, and finalization:
  `batch/001-batch-create-spritesheets.md`,
  `batch/002-batch-stack-rank-spritesheets.md`, and
  `batch/003-batch-process-ranked-candidates.md`

For a complete spritesheet request, start at step 001 and continue through the
full workflow. Do not treat each instruction as an unrelated standalone task
unless the user explicitly requests only that operation.

For a batch spritesheet request, follow the instruction under
`instructions/batch/` in numbered order. The batch flow generates every
requested candidate before ranking, ranks candidates before `003 -> 006`, and
does not pause for user review until the top-ranked GIFs and spritesheets are
finalized.

## Agent operating rules

- Treat user-provided anchor images and animation requirements as
  authoritative.
- Inspect every supplied reference and assign it a clear role before
  generation: identity, directional pose, style, scale, or another stated
  purpose.
- Preserve requirements across iterations unless the user changes them.
- Do not substitute image-to-video for image generation, or image generation
  for image-to-video, without user approval.
- Run steps 003, 004, and 005 automatically after the step-001 spritesheet is
  approved.
- Pause for user approval only at the generated spritesheet and normalized GIF
  checkpoints, unless an error or consequential ambiguity prevents progress.
- After step-005 approval, run step 006 automatically.
- Validate every stage before using its output as the next stage's input.
- When visible output is questionable, inspect the actual image artifacts
  rather than relying only on dimensions or file counts.

## File and workspace rules

- Preserve all source images in `anchors/`.
- Store temporary artifacts only under `work/<animation-name>/`.
- Store approved deliverables only under `output/<animation-name>/`.
- For batch workflows, store disposable artifacts only under
  `disposable/batch/<animation-name>/`.
- For batch workflows, store finalized ranked deliverables only under
  `output/batch/<animation-name>/<rank-number>/`.
- Reuse each numbered stage directory during iteration.
- Do not create retry directories named `pass-*`, `corrected`, `v2`, or
  similar.
- Never overwrite an approved final asset unless the user is revising that
  animation.
- Never modify or delete another animation's workspace or outputs.
- Delete `work/<animation-name>/` only after step 006 validates the final GIF
  and spritesheet.
- Do not leave rejected generations, alternate previews, reports, contact
  sheets, or intermediate frames outside the active workspace.

## Tools and setup

Image-processing steps use Python 3 and Pillow.

Check the environment with:

```bash
python3 --version
python3 -c "import PIL; print(PIL.__version__)"
```

If Pillow is unavailable, follow the installation or local virtual-environment
instructions in the applicable workflow file.

Use deterministic local processing for slicing, alpha removal, normalization,
GIF creation, and final spritesheet assembly.

## Documentation changes

- Keep pipeline-wide human-facing guidance in `README.md`.
- Keep agent-specific execution and safety rules in this file.
- Keep stage-specific procedures in their numbered instruction files.
- When changing the workflow contract, update every affected document so the
  handoffs, paths, checkpoints, and cleanup behavior remain consistent.
