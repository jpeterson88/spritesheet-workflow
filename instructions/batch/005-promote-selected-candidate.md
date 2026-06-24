# Promote the Selected Candidate

## Objective

Move the user-selected batch winner into the standard single-sheet workflow so
the existing `003` through `006` steps can continue unchanged.

## Inputs

Determine or confirm these values before promotion:

- `BATCH_NAME`: batch campaign slug
- `SELECTED_CANDIDATE`: the winning candidate directory
- `ANIMATION_NAME`: filesystem-safe animation slug

## Rules

- Promote exactly one selected candidate unless the user explicitly changes the
  decision.
- Do not modify the winning candidate during promotion.
- Do not rename or alter the approved content to hide differences between
  candidates.
- Preserve the batch report and shortlist in the batch workspace until the user
  approves the downstream step-005 preview.

## Procedure

1. Copy or reference the selected candidate into
   `work/<animation-name>/001-generated/<animation-name>-spritesheet.png`.
2. Resume the existing workflow at step 003.
3. Keep the batch workspace intact until the standard workflow reaches its own
   approval point.

## Handoff

Continue with the standard instructions in `instructions/003-slice-spritesheet.md`.
