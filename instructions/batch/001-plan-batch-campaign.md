# Plan a Batch Spritesheet Campaign

## Objective

Define a batch generation campaign that produces multiple controlled candidate
spritesheets for the same animation request.

This step does not generate art. It establishes the locked anchor contract, the
safe variation knobs, the batch size, and the quality gates that later steps
will enforce.

## Inputs

Determine these values before starting:

- `ANIMATION_NAME`: filesystem-safe animation slug
- `SUBJECT`: character or object being animated
- `ACTION`: requested animation
- `DIRECTION`: facing or movement direction, when applicable
- `ANCHOR_IMAGES`: all reference images
- `CANDIDATE_COUNT`: number of variants to generate per round
- `SHORTLIST_COUNT`: how many candidates should survive automatic QC
- `MAX_ROUNDS`: maximum reroll rounds before pausing for user input
- `FAIL_THRESHOLD`: score below which a candidate is rejected outright
- `PROMPT_VARIANTS`: controlled prompt tweaks to explore
- `SEED_STRATEGY`: how candidates differ, if the generator supports seeds

Ask only for information that cannot be inferred safely from the request or
project files.

## Rules

- Keep the anchor hierarchy from `instructions/001-generate-spritesheet.md`.
- Do not relax identity, palette, silhouette, or rendering-language locks.
- Vary only safe dimensions such as timing, energy, staging, and prompt
  phrasing.
- Keep the batch small enough that automatic QC can realistically rank the
  results.
- Prefer fewer, better candidates over large low-signal batches.
- Set explicit rejection criteria before generating anything.

## Procedure

1. Restate the request in batch terms.
2. List the locked traits that every candidate must preserve.
3. List the allowed variation knobs for this campaign.
4. Choose `CANDIDATE_COUNT` and `SHORTLIST_COUNT`.
5. Define the automatic QC criteria and reject thresholds.
6. Define the reroll policy for failed rounds.
7. Write the batch plan to the batch workspace.

## Batch plan contents

The plan should record:

- the animation name and request summary
- the anchor roles
- the locked traits
- the candidate count and shortlist count
- the allowed variation knobs
- the QC criteria
- the reroll limit
- the handoff path into the standard workflow

## Handoff

When the batch plan is complete, proceed to
`002-generate-candidate-variants.md`.

