# Review the Batch Shortlist

## Objective

Present the best surviving candidates to the user and ask them to choose a
winner or request another batch round.

## Inputs

Determine or confirm these values before review:

- `SHORTLIST_BOARD`: visual comparison board
- `SHORTLIST_REPORT`: ranked QC summary
- `SHORTLIST_COUNT`: number of candidates shown
- `BATCH_NAME`: batch campaign slug

## Rules

- Show only the shortlisted candidates, not every failed attempt.
- Make the comparison board visually direct and easy to scan.
- Preserve the batch plan's locked traits.
- Do not ask the user to evaluate candidates that already failed hard QC.

## Review flow

Present the shortlist and ask for one of these outcomes:

- choose one candidate
- request a reroll with a specific adjustment
- approve the batch winner and continue

If the user requests another round, preserve the locked traits and only adjust
the allowed variation knobs from the batch plan.

## Handoff

When the user chooses a winner, proceed to
`005-promote-selected-candidate.md`.

