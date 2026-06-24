# Batch Process Ranked Candidates

## Objective

Run only the top-ranked batch candidates through the deterministic cleanup
pipeline and produce finalized GIF plus spritesheet outputs for each rank.

This is step 3 of the batch workflow:

```text
001 batch create spritesheets
  -> 002 batch stack rank spritesheets
  -> 003 batch process ranked candidates
```

Do not process candidates until step 002 has written `ranking.json`.

## Required inputs

Use:

- the original JSON config
- `disposable/batch/<animation-name>/ranking.json`
- generated source sheets referenced by the top `keep_count` rankings
- `tools/batch_pipeline.py`

## Deterministic processing

Process the top-ranked candidates:

```bash
python3 tools/batch_pipeline.py process-ranked path/to/config.json
```

For each kept candidate, the script creates an isolated workspace:

```text
disposable/batch/<animation-name>/rank-01/
├── 001-generated/
├── 003-sliced/
├── 004-transparent/
├── 005-normalized/
└── 006-final/
```

The script performs the deterministic equivalent of:

```text
003 slice
004 remove background
005 normalize and preview
006 finalize without disposable cleanup
```

The ranked workspaces are intentionally separate from the source candidate
folders so cleanup or failure in one rank does not modify another rank.

## Final output

Final ranked assets are written to:

```text
output/batch/<animation-name>/<rank-number>/
```

Use zero-padded rank folders:

```text
rank-01
rank-02
rank-03
```

Each rank output contains:

```text
output/batch/<animation-name>/rank-01/
├── <animation-name>.gif
└── <animation-name>-spritesheet.png
```

## Cleanup policy

Do not automatically delete `disposable/batch/<animation-name>`. The user can
delete it manually or ask for a later cleanup step. Every file in that folder
must be safe to delete.

## User checkpoint

Do not bring the user into the loop until all top-ranked spritesheets and GIFs
have been finalized, unless a required input is missing, image generation
failed earlier, or deterministic processing cannot safely continue.

The completion report should include:

- ranking report path
- each finalized rank
- final GIF path
- final spritesheet path
- any rejected or failed candidate notes
- confirmation that disposable batch work was retained
