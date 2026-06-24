# Batch Spritesheet Workflow

## Purpose

This directory defines a batch prefilter workflow for spritesheet generation.
It is meant to reduce wasted review time by generating multiple controlled
variants, running automatic QC, and showing the user only the strongest
candidates.

This layer does not replace the standard single-sheet workflow in
`instructions/001-generate-spritesheet.md` through
`instructions/006-finalize-animation-assets.md`. Instead, it wraps the early
generation stage and feeds one selected candidate into the existing pipeline.

## When to use batch mode

Use the batch workflow when:

- the animation is expensive to review by eye
- the source material is stable enough to support multiple variants
- you want automatic filtering before any human review
- you expect several candidates to fail on identity, style, or motion quality

Do not use batch mode when the request is so narrow that only one exact
candidate is viable.

## Batch principle

Batch mode keeps the anchor contract strict and varies only the parts that are
safe to explore, such as:

- timing emphasis
- motion staging
- pose energy
- smear strength
- prompt phrasing
- generation seed or equivalent model randomness

Identity, palette, silhouette language, framing, and other locked anchor traits
do not vary across candidates.

## Batch flow

```text
batch 001 plan campaign
        ↓
batch 002 generate candidate variants
        ↓
batch 003 auto-QC and rank candidates
        ↓
batch 004 human shortlist review
        ↓ approved choice
standard 003 slice
        ↓
standard 004 background removal
        ↓
standard 005 normalize
        ↓
standard 006 finalize
```

## Output philosophy

The batch workflow should produce:

- one batch plan
- a set of candidate sheets
- a QC report for each candidate
- one comparison board for shortlist review
- one selected sheet promoted into the standard workflow

The workflow should avoid leaving multiple competing candidate branches around
after the user has chosen a winner.

The selected candidate should be promoted into
`work/<animation-name>/001-generated/` so the standard workflow can continue at
step 003 without changing the existing single-sheet instructions.

## Directory convention

Use a dedicated batch workspace under the animation workspace. Keep all batch
artifacts inside the active batch folder until one candidate is promoted.

Do not create ad hoc retry folders such as `pass-*`, `v2`, or `corrected`.

## Step files

Follow the numbered instructions in this directory in order:

1. `001-plan-batch-campaign.md`
2. `002-generate-candidate-variants.md`
3. `003-auto-qc-and-rank.md`
4. `004-human-shortlist-review.md`
5. `005-promote-selected-candidate.md`

## Tooling

Use `scripts/batch_spritesheet.py` to create and manage batch workspaces.
The main knobs are:

- `--candidate-count`: how many spritesheets to generate in a batch round
- `--shortlist-count`: how many survivors should reach human review
- `--prompt-file`: optional file containing your custom base prompt
- `--generate-command`: optional shell command that receives `BATCH_*`
  environment variables for each candidate
- `--prompt-variant`: optional human-written variant notes for each candidate
- `start --config`: one-command batch run from a JSON config file

An example batch config lives at
`instructions/batch/batch-config.example.json`.

The `--generate-command` template can use placeholders such as
`{prompt_file}`, `{output_file}`, `{candidate_dir}`, `{batch_dir}`,
`{animation_name}`, `{batch_name}`, `{candidate_index}`, and `{variant_name}`.

If you do not provide `--generate-command`, the batch tool uses the built-in
OpenAI adapter in `scripts/openai_image_adapter.py` and requires
`OPENAI_API_KEY` in the environment.

If you want the shortest path, use `start` with a JSON config file and let the
tool create, generate, QC, and board the batch in one command.

Typical flow:

```bash
python3 scripts/batch_spritesheet.py init \
  --animation-name curse-cast \
  --subject "curse caster" \
  --action "cast curse" \
  --anchor-image anchors/anchor.png \
  --anchor-image anchors/directional-anchor.png \
  --prompt-file prompts/curse-cast.md \
  --candidate-count 8

python3 scripts/batch_spritesheet.py generate \
  --batch-dir work/dash-east/batch/<batch-name>

python3 scripts/batch_spritesheet.py qc \
  --batch-dir work/dash-east/batch/<batch-name>

python3 scripts/batch_spritesheet.py board \
  --batch-dir work/dash-east/batch/<batch-name>

python3 scripts/batch_spritesheet.py promote \
  --batch-dir work/dash-east/batch/<batch-name>
```

Replace `<batch-name>` with the generated batch slug from the `init` step.

One-command example:

```bash
python3 scripts/batch_spritesheet.py start --config instructions/batch/batch-config.example.json
```
