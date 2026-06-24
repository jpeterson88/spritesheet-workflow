# Batch Stack Rank Spritesheets

## Objective

Rank all generated batch candidates before any deterministic cleanup runs.
Keep exactly the configured top candidates and write a machine-readable ranking
report.

This is step 2 of the batch workflow:

```text
001 batch create spritesheets
  -> 002 batch stack rank spritesheets
  -> 003 batch process ranked candidates
```

## Required inputs

Use the artifacts created by step 001:

- `disposable/batch/<animation-name>/batch-config.resolved.json`
- `disposable/batch/<animation-name>/candidate-manifest.json`
- every generated candidate under
  `disposable/batch/<animation-name>/001-generated/`
- authoritative anchors from `./anchors/anchor.*` and
  `./anchors/directional-anchor.*`
- the prompt file referenced by the batch config

Do not regenerate candidates during ranking unless a candidate file is missing
or unreadable and the user explicitly approves a retry.

## Ranking rules

Rank candidates before running steps `003 -> 006`.

Use best judgement and inspect actual image artifacts. Score each candidate on:

- `atlas_validity`: correct canvas size, grid, frame count, no labels, no grid
  lines, no watermark, correct background
- `identity_fidelity`: preserves the identity anchor's proportions, palette,
  silhouette, face, outline, and rendering language
- `directional_fidelity`: uses the directional anchor only for facing/body
  bias, without copying the same pose into every cell
- `prompt_fidelity`: follows the requested subject, action, direction, style,
  and negative constraints
- `animation_readability`: frames show deliberate progression, meaningful
  variation, and a clear loop or non-loop timing contract
- `consistency`: stable camera, scale, baseline, palette, anatomy, and outline
  across frames
- `cleanup_readiness`: no severe clipping, cell-boundary overlap, extra limbs,
  merged frames, or artifacts likely to fail slicing/normalization

Recommended weights:

```json
{
  "atlas_validity": 25,
  "identity_fidelity": 20,
  "directional_fidelity": 15,
  "prompt_fidelity": 15,
  "animation_readability": 15,
  "consistency": 5,
  "cleanup_readiness": 5
}
```

Reject candidates with fatal atlas problems even if the artwork is appealing.
A beautiful sheet that cannot be sliced safely is not a batch winner.

## Ranking report

Write the ranking report to:

```text
disposable/batch/<animation-name>/ranking.json
```

Use this shape:

```json
{
  "rankings": [
    {
      "rank": 1,
      "candidate_id": "candidate-003",
      "source_sheet": "disposable/batch/example/001-generated/candidate-003/example-candidate-003-spritesheet.png",
      "scores": {
        "atlas_validity": 24,
        "identity_fidelity": 18,
        "directional_fidelity": 13,
        "prompt_fidelity": 14,
        "animation_readability": 13,
        "consistency": 4,
        "cleanup_readiness": 5
      },
      "total_score": 91,
      "notes": "Best identity match and cleanest frame progression."
    }
  ]
}
```

The report may include more than `keep_count` candidates, but the top
`keep_count` ranks are the only candidates processed in step 003.

## Validation

Before moving to step 003:

1. Confirm that `ranking.json` includes every generated candidate or clearly
   notes any rejected/unreadable candidate.
2. Confirm that ranks are unique and sorted by quality.
3. Confirm that each top-ranked `source_sheet` points under
   `disposable/batch/<animation-name>/001-generated/`.
4. Confirm that every score object includes all required scoring keys.

## Handoff

After ranking is complete, continue to:

```text
instructions/batch/003-batch-process-ranked-candidates.md
```
