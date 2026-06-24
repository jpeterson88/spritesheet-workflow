# Generate Batch Candidate Variants

## Objective

Generate a controlled set of candidate spritesheets for the same animation
request.

Each candidate must obey the same anchor contract, but differ in the specific
variation knobs defined in the batch plan.

## Inputs

Determine or confirm these values before generating:

- `BATCH_NAME`: batch campaign slug
- `WORK_DIR`: batch workspace directory
- `CANDIDATE_COUNT`: number of candidates to generate
- `PROMPT_VARIANTS`: prompt variations from the batch plan
- `SEED_STRATEGY`: per-candidate seed or randomness strategy
- `ANCHOR_IMAGES`: required reference images
- `OUTPUT_DIR`: directory for candidate sheets

## Rules

- Preserve the locked traits from the batch plan.
- Do not let candidates drift in identity, palette, silhouette, or rendering
  language.
- Keep each candidate internally coherent as a complete sheet.
- Do not reuse a rejected candidate as a new candidate without an explicit
  reroll note.
- Do not start downstream slicing, background removal, or normalization yet.

## Candidate variation

Allowed candidate differences may include:

- more or less motion energy
- slightly different anticipation or recoil timing
- different prompt emphasis on body lean, smear, or pose staging
- different seed values when supported

Do not vary:

- the reference roles
- the subject identity
- the direction contract
- the canvas or grid contract
- the output background color

## Procedure

1. Build one candidate prompt per variant.
2. Generate the candidate sheet.
3. Validate the grid, dimensions, and anchor consistency.
4. Save each candidate in its own subdirectory.
5. Record the prompt variant and seed used for each candidate.

## Handoff

When all candidates are generated, proceed to
`003-auto-qc-and-rank.md`.

