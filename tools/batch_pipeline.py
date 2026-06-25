#!/usr/bin/env python3
"""Deterministic helpers for the batch spritesheet workflow."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ANCHOR_DIR = ROOT / "anchors"
BATCH_ROOT = ROOT / "disposable" / "batch"
OUTPUT_ROOT = ROOT / "output" / "batch"
SUPPORTED_IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
}
SCORE_KEYS = {
    "atlas_validity",
    "identity_fidelity",
    "directional_fidelity",
    "prompt_fidelity",
    "animation_readability",
    "consistency",
    "cleanup_readiness",
}


@dataclass(frozen=True)
class BatchConfig:
    animation_name: str
    prompt_path: Path
    generation_count: int
    keep_count: int
    frame_count: int
    columns: int
    rows: int
    frame_width: int
    frame_height: int
    background_color: tuple[int, int, int]
    fps: int
    background_tolerance: int
    alpha_threshold: int
    allow_overwrite: bool

    @property
    def batch_dir(self) -> Path:
        return BATCH_ROOT / self.animation_name

    @property
    def generated_dir(self) -> Path:
        return self.batch_dir / "001-generated"

    @property
    def ranking_path(self) -> Path:
        return self.batch_dir / "ranking.json"

    @property
    def output_dir(self) -> Path:
        return OUTPUT_ROOT / self.animation_name

    @property
    def canvas_size(self) -> tuple[int, int]:
        return (self.columns * self.frame_width, self.rows * self.frame_height)


def load_config(path: Path) -> BatchConfig:
    raw = json.loads(path.read_text())

    animation_name = require_str(raw, "animation_name")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", animation_name):
        raise ValueError(
            "animation_name must be filesystem-safe: letters, numbers, "
            "underscore, and hyphen only."
        )

    prompt_path = resolve_repo_path(require_str(raw, "prompt_path"))
    if not prompt_path.is_file():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    grid = require_dict(raw, "grid")
    frame_size = require_dict(raw, "frame_size")

    generation_count = require_int(raw, "generation_count")
    keep_count = require_int(raw, "keep_count")
    frame_count = require_int(raw, "frame_count")
    columns = require_int(grid, "columns")
    rows = require_int(grid, "rows")
    frame_width = require_int(frame_size, "width")
    frame_height = require_int(frame_size, "height")

    if generation_count <= 0:
        raise ValueError("generation_count must be positive.")
    if keep_count <= 0:
        raise ValueError("keep_count must be positive.")
    if keep_count > generation_count:
        raise ValueError("keep_count cannot exceed generation_count.")
    if columns <= 0 or rows <= 0:
        raise ValueError("grid columns and rows must be positive.")
    if frame_width <= 0 or frame_height <= 0:
        raise ValueError("frame_size width and height must be positive.")
    if columns * rows != frame_count:
        raise ValueError(
            f"grid {columns}x{rows} does not equal frame_count {frame_count}."
        )

    return BatchConfig(
        animation_name=animation_name,
        prompt_path=prompt_path,
        generation_count=generation_count,
        keep_count=keep_count,
        frame_count=frame_count,
        columns=columns,
        rows=rows,
        frame_width=frame_width,
        frame_height=frame_height,
        background_color=parse_hex_color(raw.get("background_color", "#00FF00")),
        fps=int(raw.get("fps", 12)),
        background_tolerance=int(raw.get("background_tolerance", 20)),
        alpha_threshold=int(raw.get("alpha_threshold", 8)),
        allow_overwrite=bool(raw.get("allow_overwrite", False)),
    )


def require_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Missing string field: {key}")
    return value


def require_int(data: dict[str, Any], key: str) -> int:
    value = data.get(key)
    if not isinstance(value, int):
        raise ValueError(f"Missing integer field: {key}")
    return value


def require_dict(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Missing object field: {key}")
    return value


def resolve_repo_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    resolved = path.resolve()
    if not resolved.is_relative_to(ROOT):
        raise ValueError(f"Path must stay inside the repository: {value}")
    return resolved


def parse_hex_color(value: str) -> tuple[int, int, int]:
    if not isinstance(value, str) or not re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
        raise ValueError("background_color must use #RRGGBB format.")
    return (
        int(value[1:3], 16),
        int(value[3:5], 16),
        int(value[5:7], 16),
    )


def find_anchor(stem: str) -> Path:
    matches = [
        path
        for path in sorted(ANCHOR_DIR.iterdir())
        if path.is_file()
        and path.stem == stem
        and path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
    ]
    if not matches:
        raise FileNotFoundError(
            f"Required anchor not found in {ANCHOR_DIR}: {stem}.*"
        )
    if len(matches) > 1:
        names = ", ".join(path.name for path in matches)
        raise ValueError(f"Ambiguous anchor files for {stem}: {names}")
    return matches[0]


def prepare(config: BatchConfig) -> None:
    anchor = find_anchor("anchor")
    directional_anchor = find_anchor("directional-anchor")

    config.batch_dir.mkdir(parents=True, exist_ok=True)
    config.generated_dir.mkdir(parents=True, exist_ok=True)

    batch_anchor_dir = config.batch_dir / "anchors"
    batch_anchor_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(anchor, batch_anchor_dir / anchor.name)
    shutil.copy2(directional_anchor, batch_anchor_dir / directional_anchor.name)

    resolved_config = {
        "animation_name": config.animation_name,
        "prompt_path": str(config.prompt_path.relative_to(ROOT)),
        "anchor_path": str(anchor.relative_to(ROOT)),
        "directional_anchor_path": str(directional_anchor.relative_to(ROOT)),
        "generation_count": config.generation_count,
        "keep_count": config.keep_count,
        "frame_count": config.frame_count,
        "grid": {"columns": config.columns, "rows": config.rows},
        "frame_size": {"width": config.frame_width, "height": config.frame_height},
        "canvas_size": {
            "width": config.canvas_size[0],
            "height": config.canvas_size[1],
        },
        "background_color": rgb_to_hex(config.background_color),
        "fps": config.fps,
        "background_tolerance": config.background_tolerance,
        "alpha_threshold": config.alpha_threshold,
        "allow_overwrite": config.allow_overwrite,
    }
    write_json(config.batch_dir / "batch-config.resolved.json", resolved_config)

    manifest = {
        "animation_name": config.animation_name,
        "candidates": [
            {
                "candidate_id": candidate_id(index),
                "expected_sheet": str(
                    candidate_sheet_path(config, candidate_id(index)).relative_to(ROOT)
                ),
                "status": "pending-image-gen",
            }
            for index in range(1, config.generation_count + 1)
        ],
    }
    for candidate in manifest["candidates"]:
        (ROOT / candidate["expected_sheet"]).parent.mkdir(parents=True, exist_ok=True)
    write_json(config.batch_dir / "candidate-manifest.json", manifest)

    print(f"Prepared batch workspace: {config.batch_dir.relative_to(ROOT)}")
    print(f"Candidate manifest: {(config.batch_dir / 'candidate-manifest.json').relative_to(ROOT)}")


def process_ranked(config: BatchConfig) -> None:
    require_pillow()
    rankings = load_rankings(config)
    kept = rankings[: config.keep_count]
    if len(kept) < config.keep_count:
        raise ValueError(
            f"ranking.json has {len(kept)} rankings; expected {config.keep_count}."
        )

    for ranking in kept:
        process_one_rank(config, ranking)

    print(f"Processed {len(kept)} ranked candidates.")
    print(f"Ranking report: {config.ranking_path.relative_to(ROOT)}")
    print(f"Output root: {config.output_dir.relative_to(ROOT)}")


def load_rankings(config: BatchConfig) -> list[dict[str, Any]]:
    if not config.ranking_path.is_file():
        raise FileNotFoundError(f"Ranking report not found: {config.ranking_path}")

    report = json.loads(config.ranking_path.read_text())
    rankings = report.get("rankings")
    if not isinstance(rankings, list):
        raise ValueError("ranking.json must contain a rankings array.")

    seen_ranks: set[int] = set()
    validated = []
    for item in rankings:
        if not isinstance(item, dict):
            raise ValueError("Each ranking entry must be an object.")
        rank = require_int(item, "rank")
        candidate = require_str(item, "candidate_id")
        source_sheet = resolve_repo_path(require_str(item, "source_sheet"))
        scores = require_dict(item, "scores")
        if rank in seen_ranks:
            raise ValueError(f"Duplicate rank: {rank}")
        if not re.fullmatch(r"candidate-\d{3}", candidate):
            raise ValueError(f"Invalid candidate_id: {candidate}")
        if not source_sheet.is_file():
            raise FileNotFoundError(f"Ranked source sheet not found: {source_sheet}")
        if not source_sheet.is_relative_to(config.generated_dir):
            raise ValueError(
                f"Ranked source sheet must be under {config.generated_dir}: "
                f"{source_sheet}"
            )
        missing = SCORE_KEYS - set(scores)
        if missing:
            raise ValueError(
                f"Ranking {rank} is missing score keys: {', '.join(sorted(missing))}"
            )
        seen_ranks.add(rank)
        validated.append(item)

    return sorted(validated, key=lambda item: item["rank"])


def process_one_rank(config: BatchConfig, ranking: dict[str, Any]) -> None:
    rank = ranking["rank"]
    rank_id = f"rank-{rank:02d}"
    source_sheet = resolve_repo_path(ranking["source_sheet"])
    rank_dir = config.batch_dir / rank_id

    generated_dir = rank_dir / "001-generated"
    sliced_dir = rank_dir / "003-sliced"
    transparent_dir = rank_dir / "004-transparent"
    normalized_dir = rank_dir / "005-normalized"
    normalized_frames_dir = normalized_dir / "frames"
    final_work_dir = rank_dir / "006-final"
    final_output_dir = config.output_dir / rank_id

    for directory in (
        generated_dir,
        sliced_dir,
        transparent_dir,
        normalized_frames_dir,
        final_work_dir,
        final_output_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    staged_sheet = generated_dir / f"{config.animation_name}-{rank_id}-source.png"
    shutil.copy2(source_sheet, staged_sheet)

    final_sheet_path = final_output_dir / f"{config.animation_name}-spritesheet.png"
    final_gif = final_output_dir / f"{config.animation_name}.gif"
    existing_outputs = [path for path in (final_sheet_path, final_gif) if path.exists()]
    if existing_outputs and not config.allow_overwrite:
        existing = ", ".join(str(path.relative_to(ROOT)) for path in existing_outputs)
        raise FileExistsError(
            "Refusing to overwrite finalized batch output. "
            "Set allow_overwrite to true in the config only when revising this "
            f"batch intentionally: {existing}"
        )

    validate_sheet(config, staged_sheet)
    sliced = slice_sheet(config, staged_sheet, sliced_dir, f"{config.animation_name}-{rank_id}")
    transparent = remove_backgrounds(config, sliced, transparent_dir)
    normalized = normalize_frames(config, transparent, normalized_frames_dir)
    preview_gif = write_preview_gif(config, normalized, normalized_dir / f"{config.animation_name}-preview.gif")
    final_sheet = write_final_sheet(config, normalized, final_sheet_path)
    shutil.copy2(preview_gif, final_gif)

    write_json(
        final_work_dir / "rank-summary.json",
        {
            "rank": rank,
            "candidate_id": ranking["candidate_id"],
            "source_sheet": str(source_sheet.relative_to(ROOT)),
            "scores": ranking["scores"],
            "total_score": ranking.get("total_score"),
            "notes": ranking.get("notes", ""),
            "final_spritesheet": str(final_sheet.relative_to(ROOT)),
            "final_gif": str(final_gif.relative_to(ROOT)),
        },
    )

    print(f"{rank_id}: {final_sheet.relative_to(ROOT)}")
    print(f"{rank_id}: {final_gif.relative_to(ROOT)}")


def validate_sheet(config: BatchConfig, sheet_path: Path) -> None:
    from PIL import Image

    with Image.open(sheet_path) as opened:
        opened.load()
        if opened.size != config.canvas_size:
            raise ValueError(
                f"{sheet_path} is {opened.size}; expected {config.canvas_size}."
            )


def slice_sheet(
    config: BatchConfig, sheet_path: Path, output_dir: Path, prefix: str
) -> list[Path]:
    from PIL import Image

    paths = []
    digits = max(3, len(str(config.frame_count - 1)))
    with Image.open(sheet_path) as opened:
        sheet = opened.convert("RGBA")
        for index in range(config.frame_count):
            row = index // config.columns
            column = index % config.columns
            left = column * config.frame_width
            top = row * config.frame_height
            frame = sheet.crop(
                (
                    left,
                    top,
                    left + config.frame_width,
                    top + config.frame_height,
                )
            )
            path = output_dir / f"{prefix}-{index:0{digits}d}.png"
            frame.save(path, format="PNG")
            paths.append(path)
    return paths


def remove_backgrounds(
    config: BatchConfig, source_paths: list[Path], output_dir: Path
) -> list[Path]:
    from PIL import Image

    output_paths = []
    for source_path in source_paths:
        with Image.open(source_path) as opened:
            rgba = opened.convert("RGBA")
            pixels = rgba.load()
            for y in range(rgba.height):
                for x in range(rgba.width):
                    red, green, blue, alpha = pixels[x, y]
                    if color_matches(
                        (red, green, blue),
                        config.background_color,
                        config.background_tolerance,
                    ):
                        pixels[x, y] = (red, green, blue, 0)
            output_path = output_dir / source_path.name
            rgba.save(output_path, format="PNG")
            output_paths.append(output_path)
    return output_paths


def color_matches(
    color: tuple[int, int, int],
    key: tuple[int, int, int],
    tolerance: int,
) -> bool:
    if all(abs(channel - target) <= tolerance for channel, target in zip(color, key)):
        return True

    red, green, blue = color
    key_red, key_green, key_blue = key
    green_key = key_green > 200 and key_red < 40 and key_blue < 40
    if green_key:
        return green >= 100 and green - max(red, blue) >= 45

    return False


def normalize_frames(
    config: BatchConfig, source_paths: list[Path], output_dir: Path
) -> list[Path]:
    from PIL import Image

    bounds = []
    frames = []
    for path in source_paths:
        with Image.open(path) as opened:
            frame = opened.convert("RGBA")
        box = alpha_bounds(frame, config.alpha_threshold)
        if box is None:
            raise ValueError(f"Frame contains no visible pixels: {path}")
        frames.append((path, frame, box))
        bounds.append(box)

    target_bottom_y = round(config.frame_height * 0.92)
    target_anchor_x = config.frame_width / 2
    output_paths = []

    for path, frame, box in frames:
        left, top, right, bottom = box
        subject = frame.crop(box)
        visible_width = right - left
        visible_height = bottom - top
        paste_x = round(target_anchor_x - (visible_width / 2))
        paste_y = round(target_bottom_y - visible_height)

        if (
            paste_x < 0
            or paste_y < 0
            or paste_x + visible_width > config.frame_width
            or paste_y + visible_height > config.frame_height
        ):
            raise ValueError(
                f"Normalized frame does not fit target canvas: {path.name}"
            )

        output = Image.new(
            "RGBA",
            (config.frame_width, config.frame_height),
            (0, 0, 0, 0),
        )
        output.alpha_composite(subject, (paste_x, paste_y))
        output_path = output_dir / path.name
        output.save(output_path, format="PNG")
        output_paths.append(output_path)

    write_json(
        output_dir.parent / "normalization-report.json",
        {
            "frame_count": len(output_paths),
            "frame_size": [config.frame_width, config.frame_height],
            "target_anchor_x": target_anchor_x,
            "target_bottom_y": target_bottom_y,
            "median_source_visible_height": median(
                bottom - top for _left, top, _right, bottom in bounds
            ),
        },
    )
    return output_paths


def alpha_bounds(image: Image.Image, threshold: int) -> tuple[int, int, int, int] | None:
    alpha = image.getchannel("A")
    mask = alpha.point(lambda value: 255 if value > threshold else 0)
    return mask.getbbox()


def write_preview_gif(config: BatchConfig, frame_paths: list[Path], output_path: Path) -> Path:
    from PIL import Image

    frames = []
    for path in frame_paths:
        with Image.open(path) as opened:
            frames.append(opened.convert("RGBA"))
    duration_ms = round(1000 / config.fps)
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=0,
        disposal=2,
    )
    return output_path


def write_final_sheet(config: BatchConfig, frame_paths: list[Path], output_path: Path) -> Path:
    from PIL import Image

    sheet = Image.new(
        "RGBA",
        config.canvas_size,
        (0, 0, 0, 0),
    )
    for index, path in enumerate(frame_paths):
        with Image.open(path) as opened:
            frame = opened.convert("RGBA")
        if frame.size != (config.frame_width, config.frame_height):
            raise ValueError(f"Frame size mismatch: {path}")
        row = index // config.columns
        column = index % config.columns
        sheet.alpha_composite(
            frame,
            (column * config.frame_width, row * config.frame_height),
        )
    sheet.save(output_path, format="PNG")
    return output_path


def candidate_id(index: int) -> str:
    return f"candidate-{index:03d}"


def candidate_sheet_path(config: BatchConfig, candidate: str) -> Path:
    return (
        config.generated_dir
        / candidate
        / f"{config.animation_name}-{candidate}-spritesheet.png"
    )


def rgb_to_hex(color: tuple[int, int, int]) -> str:
    return f"#{color[0]:02X}{color[1]:02X}{color[2]:02X}"


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n")


def require_pillow() -> None:
    try:
        import PIL  # noqa: F401
    except ImportError as error:
        raise SystemExit(
            "Pillow is required for process-ranked. Install it with "
            "`python3 -m pip install Pillow` or create a local virtual "
            "environment as described in the workflow instructions."
        ) from error


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("config", type=Path)

    process_parser = subparsers.add_parser("process-ranked")
    process_parser.add_argument("config", type=Path)

    args = parser.parse_args()

    try:
        config = load_config(args.config)
        if args.command == "prepare":
            prepare(config)
        elif args.command == "process-ranked":
            process_ranked(config)
    except (FileExistsError, FileNotFoundError, ValueError, NotADirectoryError) as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
