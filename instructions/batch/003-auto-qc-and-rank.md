# Auto-QC and Rank Batch Candidates

## Objective

Run automatic quality checks across the generated candidates, reject obvious
failures, and rank the survivors for human review.

## Inputs

Determine or confirm these values before ranking:

- `BATCH_DIR`: batch workspace
- `CANDIDATE_DIRS`: generated candidate locations
- `SHORTLIST_COUNT`: number of candidates to retain
- `FAIL_THRESHOLD`: rejection score threshold
- `ANCHOR_IMAGES`: the reference images used to judge identity and style

## Checks

Apply the same hard checks to every candidate:

- canvas dimensions and grid integrity
- frame count and ordering
- subject completeness
- boundary safety
- background removability
- identity and style consistency
- motion readability
- frame-to-frame coherence

Reject candidates that fail any non-negotiable check.

## Ranking

Score surviving candidates using a simple, explainable ranking model. Favor:

- closer anchor fidelity
- stronger animation readability
- fewer clipping or boundary issues
- more stable scale and baseline behavior
- fewer cleanup warnings

Keep the scoring model simple enough that the user can understand why a
candidate survived.

## Outputs

Produce:

- one QC report per candidate
- one ranked summary table
- one comparison board of the top survivors
- one shortlist containing at most `SHORTLIST_COUNT` candidates

## Handoff

When QC is complete, proceed to `004-human-shortlist-review.md`.

