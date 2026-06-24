#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import statistics
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps, ImageStat


SUPPORTED_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
}

DEFAULT_BATCH_ROOT = Path("work")
DEFAULT_WORKSPACE_NAME = "batch"
DEFAULT_SHORTLIST_COUNT = 4
DEFAULT_FAIL_THRESHOLD = 60.0
DEFAULT_CANDIDATE_COUNT = 8
DEFAULT_MAX_ROUNDS = 3
DEFAULT_ALPHA_THRESHOLD = 8
DEFAULT_CELL_SIZE_THUMB = (256, 256)
DEFAULT_BOARD_TILE_SIZE = (360, 320)
DEFAULT_COMPARE_SIZE = (96, 96)


@dataclass
class BatchConfig:
    animation_name: str
    batch_name: str
    subject: str
    action: str
    direction: str | None
    candidate_count: int
    shortlist_count: int
    max_rounds: int
    fail_threshold: float
    seed_strategy: str
    anchor_images: list[str]
    columns: int | None = None
    rows: int | None = None
    prompt_file: str = ""
    base_prompt_text: str = ""
    prompt_variants: list[str] = field(default_factory=list)
    locked_traits: list[str] = field(default_factory=list)
    allowed_variations: list[str] = field(default_factory=list)
    background_color: str = "#00FF00"
    generate_command: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    notes: str = ""


@dataclass
class CandidateReport:
    candidate: str
    sheet_path: str | None
    prompt_path: str | None
    score: float
    passed: bool
    failures: list[str]
    metrics: dict[str, float]


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "batch"


def utc_batch_name() -> str:
    return datetime.utcnow().strftime("%Y%m%d-%H%M%S")


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def merge_args_with_config(args: argparse.Namespace, required: Sequence[str]) -> dict:
    config_data: dict = {}
    if getattr(args, "config", None):
        config_data = load_json(Path(args.config))

    merged = dict(config_data)
    for key, value in vars(args).items():
        if key == "config":
            continue
        if value is not None:
            merged[key] = value

    missing = [name for name in required if merged.get(name) in (None, "", [])]
    if missing:
        raise ValueError(f"Missing required configuration values: {', '.join(missing)}")
    return merged


def build_batch_config(payload: dict) -> BatchConfig:
    prompt_file = payload.get("prompt_file", "")
    base_prompt_text = payload.get("base_prompt_text", "")
    if prompt_file and not base_prompt_text:
        base_prompt_text = Path(prompt_file).read_text(encoding="utf-8")

    candidate_count = payload.get("candidate_count", DEFAULT_CANDIDATE_COUNT)
    prompt_variants = list(payload.get("prompt_variants", []))
    if not prompt_variants:
        prompt_variants = default_variants(candidate_count)
    if len(prompt_variants) < candidate_count:
        prompt_variants.extend(default_variants(candidate_count - len(prompt_variants)))
    prompt_variants = prompt_variants[:candidate_count]

    return BatchConfig(
        animation_name=payload.get("animation_name", "batch"),
        batch_name=payload.get("batch_name", "batch"),
        subject=payload.get("subject", ""),
        action=payload.get("action", ""),
        direction=payload.get("direction"),
        candidate_count=candidate_count,
        shortlist_count=payload.get("shortlist_count", DEFAULT_SHORTLIST_COUNT),
        max_rounds=payload.get("max_rounds", DEFAULT_MAX_ROUNDS),
        fail_threshold=payload.get("fail_threshold", DEFAULT_FAIL_THRESHOLD),
        seed_strategy=payload.get("seed_strategy", "incremental"),
        anchor_images=payload.get("anchor_images", []),
        columns=payload.get("columns"),
        rows=payload.get("rows"),
        prompt_file=prompt_file,
        base_prompt_text=base_prompt_text,
        prompt_variants=prompt_variants,
        locked_traits=payload.get("locked_traits", []),
        allowed_variations=payload.get("allowed_variations", []),
        background_color=payload.get("background_color", "#00FF00"),
        generate_command=payload.get("generate_command", ""),
        notes=payload.get("notes", ""),
    )


def ensure_pillow() -> None:
    try:
        import PIL  # noqa: F401
    except Exception as exc:  # pragma: no cover - environment specific
        raise RuntimeError(
            "Pillow is required for batch spritesheet tooling."
        ) from exc


def batch_root(animation_name: str, batch_name: str) -> Path:
    return DEFAULT_BATCH_ROOT / animation_name / DEFAULT_WORKSPACE_NAME / batch_name


def generated_output(animation_name: str) -> Path:
    return DEFAULT_BATCH_ROOT / animation_name / "001-generated" / f"{animation_name}-spritesheet.png"


def candidate_dir(batch_dir: Path, index: int) -> Path:
    return batch_dir / "candidates" / f"candidate-{index:03d}"


def candidate_sheet_path(batch_dir: Path, animation_name: str, index: int) -> Path:
    return candidate_dir(batch_dir, index) / f"{animation_name}-spritesheet.png"


def candidate_prompt_path(batch_dir: Path, index: int) -> Path:
    return candidate_dir(batch_dir, index) / "prompt.md"


def candidate_qc_path(batch_dir: Path, index: int) -> Path:
    return candidate_dir(batch_dir, index) / "qc.json"


def compare_dir(batch_dir: Path) -> Path:
    return batch_dir / "reports"


def config_path(batch_dir: Path) -> Path:
    return batch_dir / "batch.json"


def parse_hex_color(value: str) -> tuple[int, int, int]:
    text = value.strip().lstrip("#")
    if len(text) != 6 or any(ch not in "0123456789abcdefABCDEF" for ch in text):
        raise ValueError(f"Invalid hex color: {value}")
    return tuple(int(text[index : index + 2], 16) for index in (0, 2, 4))


def default_variants(candidate_count: int) -> list[str]:
    base_variants = [
        "balanced motion, conservative silhouette",
        "slightly stronger anticipation, still readable",
        "cleaner pose separation, modest smear",
        "higher energy, stronger recoil",
        "tighter silhouette, restrained deformation",
        "more expressive timing, stable identity",
    ]
    return [base_variants[index % len(base_variants)] for index in range(candidate_count)]


def build_locked_traits(subject: str, action: str, direction: str | None) -> list[str]:
    traits = [
        f"subject identity: {subject}",
        f"action: {action}",
    ]
    if direction:
        traits.append(f"direction: {direction}")
    traits.extend(
        [
            "identity anchor must remain authoritative",
            "palette, silhouette language, and rendering medium are locked",
            "camera, grid, and output dimensions are locked",
        ]
    )
    return traits


def build_allowed_variations() -> list[str]:
    return [
        "timing emphasis",
        "motion staging",
        "pose energy",
        "smear strength",
        "prompt phrasing",
        "generation seed or equivalent randomness",
    ]


def build_prompt_text(config: BatchConfig, candidate_index: int) -> str:
    variant = config.prompt_variants[candidate_index - 1]
    direction_line = f"- Direction: {config.direction}" if config.direction else "- Direction: not specified"
    anchors = "\n".join(f"- {path}" for path in config.anchor_images)
    locked_traits = "\n".join(f"- {trait}" for trait in config.locked_traits)
    allowed = "\n".join(f"- {item}" for item in config.allowed_variations)
    base_prompt = config.base_prompt_text.strip()
    base_prompt_block = base_prompt if base_prompt else "(no custom base prompt provided)"

    return (
        f"# Batch Candidate {candidate_index:03d}\n\n"
        "## Reference instructions\n"
        "- Follow `instructions/001-generate-spritesheet.md` exactly.\n"
        "- Treat the identity anchor as non-negotiable.\n"
        "- Do not change palette, silhouette language, camera, or rendering medium.\n\n"
        "## Base prompt\n"
        f"{base_prompt_block}\n\n"
        "## Batch metadata\n"
        f"- Animation: {config.animation_name}\n"
        f"- Subject: {config.subject}\n"
        f"- Action: {config.action}\n"
        f"{direction_line}\n"
        f"- Variant note: {variant}\n"
        f"- Seed strategy: {config.seed_strategy}\n\n"
        "## Anchor images\n"
        f"{anchors}\n\n"
        "## Locked traits\n"
        f"{locked_traits}\n\n"
        "## Allowed variation knobs\n"
        f"{allowed}\n\n"
        "## Hard constraint\n"
        "If this candidate drifts from the anchor identity or rendering language,\n"
        "treat it as a failure and regenerate using a different variant.\n"
    )


def build_batch_plan_text(config: BatchConfig) -> str:
    anchors = "\n".join(f"- {path}" for path in config.anchor_images) or "- none"
    locked = "\n".join(f"- {trait}" for trait in config.locked_traits)
    allowed = "\n".join(f"- {item}" for item in config.allowed_variations)
    variants = "\n".join(
        f"{index + 1}. {variant}" for index, variant in enumerate(config.prompt_variants)
    )

    return (
        f"# Batch Plan: {config.batch_name}\n\n"
        "## Request\n"
        f"- Animation: {config.animation_name}\n"
        f"- Subject: {config.subject}\n"
        f"- Action: {config.action}\n"
        f"- Direction: {config.direction or 'not specified'}\n"
        f"- Candidate count: {config.candidate_count}\n"
        f"- Shortlist count: {config.shortlist_count}\n"
        f"- Max rounds: {config.max_rounds}\n"
        f"- Fail threshold: {config.fail_threshold}\n"
        f"- Seed strategy: {config.seed_strategy}\n\n"
        f"- Background color: {config.background_color}\n"
        "## Base prompt\n"
        f"{config.base_prompt_text.strip() or '(none)'}\n\n"
        "## Anchor images\n"
        f"{anchors}\n\n"
        "## Locked traits\n"
        f"{locked}\n\n"
        "## Allowed variation knobs\n"
        f"{allowed}\n\n"
        "## Prompt variants\n"
        f"{variants}\n"
    )


def init_workspace(config: BatchConfig) -> Path:
    batch_dir = batch_root(config.animation_name, config.batch_name)
    (batch_dir / "candidates").mkdir(parents=True, exist_ok=True)
    compare_dir(batch_dir).mkdir(parents=True, exist_ok=True)
    save_json(config_path(batch_dir), asdict(config))
    (batch_dir / "batch-plan.md").write_text(build_batch_plan_text(config), encoding="utf-8")
    for index in range(1, config.candidate_count + 1):
        cdir = candidate_dir(batch_dir, index)
        cdir.mkdir(parents=True, exist_ok=True)
        candidate_prompt_path(batch_dir, index).write_text(
            build_prompt_text(config, index),
            encoding="utf-8",
        )
    return batch_dir


def alpha_mask_bbox(image: Image.Image, threshold: int) -> tuple[int, int, int, int] | None:
    alpha = image.getchannel("A")
    mask = alpha.point(lambda value: 255 if value > threshold else 0)
    return mask.getbbox()


def image_alpha_pixels(image: Image.Image, threshold: int) -> int:
    alpha = image.getchannel("A")
    return sum(1 for value in alpha.getdata() if value > threshold)


def resize_for_compare(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    rgba = image.convert("RGBA")
    if rgba.size == size:
        return rgba
    return ImageOps.contain(rgba, size, method=Image.Resampling.LANCZOS)


def compare_score(left: Image.Image, right: Image.Image) -> float:
    left_rgba = left.convert("RGBA")
    right_rgba = right.convert("RGBA")
    target_size = (
        max(left_rgba.width, right_rgba.width),
        max(left_rgba.height, right_rgba.height),
    )
    def centered_fit(image: Image.Image) -> Image.Image:
        fitted = resize_for_compare(image, target_size)
        canvas = Image.new("RGBA", target_size, (0, 0, 0, 0))
        paste_x = (target_size[0] - fitted.width) // 2
        paste_y = (target_size[1] - fitted.height) // 2
        canvas.alpha_composite(fitted, (paste_x, paste_y))
        return canvas

    left_fit = centered_fit(left_rgba)
    right_fit = centered_fit(right_rgba)
    diff = ImageChops.difference(left_fit, right_fit)
    stat = ImageStat.Stat(diff)
    return sum(stat.mean) / len(stat.mean)


def load_candidate_sheet(path: Path) -> Image.Image:
    with Image.open(path) as opened:
        return opened.convert("RGBA")


def frame_grid(sheet: Image.Image, columns: int, rows: int) -> list[Image.Image]:
    width, height = sheet.size
    cell_width = width // columns
    cell_height = height // rows
    frames: list[Image.Image] = []
    for row in range(rows):
        for column in range(columns):
            box = (
                column * cell_width,
                row * cell_height,
                (column + 1) * cell_width,
                (row + 1) * cell_height,
            )
            frames.append(sheet.crop(box))
    return frames


def quantize_float(value: float) -> float:
    return round(value, 4)


def load_batch_config(batch_dir: Path) -> BatchConfig:
    payload = load_json(config_path(batch_dir))
    return build_batch_config(payload)


def background_score(sheet: Image.Image, background_rgb: tuple[int, int, int], patch_size: int = 10) -> tuple[float, list[str]]:
    width, height = sheet.size
    if width < patch_size or height < patch_size:
        return 0.0, ["sheet too small to sample background"]

    patches = [
        sheet.crop((0, 0, patch_size, patch_size)),
        sheet.crop((width - patch_size, 0, width, patch_size)),
        sheet.crop((0, height - patch_size, patch_size, height)),
        sheet.crop((width - patch_size, height - patch_size, width, height)),
    ]
    deltas = []
    for patch in patches:
        stat = ImageStat.Stat(patch.convert("RGB"))
        mean_rgb = tuple(stat.mean[index] for index in range(3))
        delta = sum(abs(mean_rgb[index] - background_rgb[index]) for index in range(3)) / 3.0
        deltas.append(delta)
    mean_delta = statistics.mean(deltas)
    score = max(0.0, 100.0 - mean_delta * 4.0)
    failures: list[str] = []
    if mean_delta > 18.0:
        failures.append("background corners deviate from expected key color")
    return score, failures


def score_candidate_sheet(
    sheet_path: Path,
    config: BatchConfig,
    threshold: int = DEFAULT_ALPHA_THRESHOLD,
) -> CandidateReport:
    failures: list[str] = []
    metrics: dict[str, float] = {}

    if not sheet_path.is_file():
        return CandidateReport(
            candidate=sheet_path.parent.name,
            sheet_path=str(sheet_path),
            prompt_path=str(sheet_path.parent / "prompt.md"),
            score=0.0,
            passed=False,
            failures=[f"sheet not found: {sheet_path}"],
            metrics=metrics,
        )

    with Image.open(sheet_path) as opened:
        sheet = opened.convert("RGBA")

    width, height = sheet.size
    columns = config.columns or 0
    rows = config.rows or 0
    if columns <= 0 or rows <= 0:
        failures.append("missing grid dimensions in batch config")
        return CandidateReport(
            candidate=sheet_path.parent.name,
            sheet_path=str(sheet_path),
            prompt_path=str(sheet_path.parent / "prompt.md"),
            score=0.0,
            passed=False,
            failures=failures,
            metrics=metrics,
        )

    if width % columns != 0 or height % rows != 0:
        failures.append("sheet dimensions do not divide evenly by grid")
        return CandidateReport(
            candidate=sheet_path.parent.name,
            sheet_path=str(sheet_path),
            prompt_path=str(sheet_path.parent / "prompt.md"),
            score=0.0,
            passed=False,
            failures=failures,
            metrics=metrics,
        )

    frames = frame_grid(sheet, columns, rows)
    cell_width = width // columns
    cell_height = height // rows
    cell_area = cell_width * cell_height

    frame_coverages: list[float] = []
    edge_contacts = 0
    blank_frames = 0
    frame_diffs: list[float] = []
    bg_score, bg_failures = background_score(sheet, parse_hex_color(config.background_color))
    failures.extend(bg_failures)

    normalized_frames = [resize_for_compare(frame, DEFAULT_COMPARE_SIZE) for frame in frames]
    representative_frame = normalized_frames[len(normalized_frames) // 2]

    for index, frame in enumerate(frames):
        alpha_pixels = image_alpha_pixels(frame, threshold)
        coverage = alpha_pixels / cell_area if cell_area else 0.0
        frame_coverages.append(coverage)

        bbox = alpha_mask_bbox(frame, threshold)
        if bbox is None:
            blank_frames += 1
            failures.append(f"frame {index:03d} is empty")
            continue

        left, top, right, bottom = bbox
        if left == 0 or top == 0 or right == cell_width or bottom == cell_height:
            edge_contacts += 1

    for left, right in zip(normalized_frames, normalized_frames[1:]):
        frame_diffs.append(compare_score(left, right))

    anchor_score = 0.0
    if config.anchor_images:
        anchor_path = Path(config.anchor_images[0])
        if anchor_path.is_file():
            with Image.open(anchor_path) as anchor_opened:
                anchor = resize_for_compare(anchor_opened.convert("RGBA"), DEFAULT_COMPARE_SIZE)
            anchor_score = max(0.0, 100.0 - compare_score(representative_frame, anchor) * 2.0)
        else:
            failures.append(f"anchor image missing: {anchor_path}")

    if blank_frames:
        failures.append(f"{blank_frames} empty frame(s)")

    avg_coverage = statistics.mean(frame_coverages) if frame_coverages else 0.0
    coverage_target = 0.18
    coverage_score = max(
        0.0,
        100.0 - abs(avg_coverage - coverage_target) / max(coverage_target, 0.01) * 100.0,
    )

    edge_penalty_ratio = edge_contacts / max(len(frames), 1)
    boundary_score = max(0.0, 100.0 - edge_penalty_ratio * 100.0)

    if frame_diffs:
        avg_motion = statistics.mean(frame_diffs)
        motion_stdev = statistics.pstdev(frame_diffs) if len(frame_diffs) > 1 else 0.0
        motion_score = max(
            0.0,
            min(100.0, (avg_motion / 18.0) * 100.0),
        )
        smoothness_score = max(0.0, 100.0 - motion_stdev * 4.0)
    else:
        avg_motion = 0.0
        motion_stdev = 0.0
        motion_score = 0.0
        smoothness_score = 0.0

    metrics.update(
        {
            "avg_coverage": quantize_float(avg_coverage),
            "edge_contacts": float(edge_contacts),
            "boundary_score": quantize_float(boundary_score),
            "anchor_score": quantize_float(anchor_score),
            "motion_score": quantize_float(motion_score),
            "smoothness_score": quantize_float(smoothness_score),
            "background_score": quantize_float(bg_score),
            "avg_motion_delta": quantize_float(avg_motion),
            "motion_stdev": quantize_float(motion_stdev),
        }
    )

    if avg_coverage < 0.02:
        failures.append("subject coverage is too low")
    if avg_coverage > 0.85:
        failures.append("subject coverage is too high")
    if edge_penalty_ratio > 0.35:
        failures.append("too many frames touch the cell boundary")
    if bg_score < 80.0:
        failures.append("background does not match the configured key color")
    if "idle" not in config.action.lower() and avg_motion < 4.0:
        failures.append("motion is too weak for a non-idle animation")

    score = (
        anchor_score * 0.45
        + boundary_score * 0.25
        + coverage_score * 0.15
        + bg_score * 0.1
        + (0.6 * motion_score + 0.4 * smoothness_score) * 0.05
    )

    if failures:
        score *= 0.5

    return CandidateReport(
        candidate=sheet_path.parent.name,
        sheet_path=str(sheet_path),
        prompt_path=str(sheet_path.parent / "prompt.md"),
        score=quantize_float(score),
        passed=not failures,
        failures=failures,
        metrics=metrics,
    )


def discover_candidate_sheets(batch_dir: Path, animation_name: str) -> list[Path]:
    candidates_dir = batch_dir / "candidates"
    if not candidates_dir.is_dir():
        return []
    sheets: list[Path] = []
    for candidate_path in sorted(candidates_dir.iterdir()):
        if not candidate_path.is_dir():
            continue
        sheet = candidate_path / f"{animation_name}-spritesheet.png"
        if sheet.exists():
            sheets.append(sheet)
    return sheets


def write_reports(batch_dir: Path, reports: list[CandidateReport], shortlist_count: int) -> None:
    reports_dir = compare_dir(batch_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    for report in reports:
        report_path = candidate_qc_path(batch_dir, int(report.candidate.split("-")[-1]))
        save_json(report_path, asdict(report))
    passing = [report for report in reports if report.passed]
    payload = {
        "shortlist_count": shortlist_count,
        "candidates": [asdict(report) for report in reports],
        "passing_candidates": [asdict(report) for report in passing],
    }
    save_json(reports_dir / "qc-report.json", payload)
    shortlist_source = passing if passing else reports
    shortlist = sorted(shortlist_source, key=lambda report: report.score, reverse=True)[:shortlist_count]
    save_json(
        reports_dir / "shortlist.json",
        {
            "shortlist_count": shortlist_count,
            "shortlist": [asdict(report) for report in shortlist],
        },
    )
    ranked = sorted(reports, key=lambda report: report.score, reverse=True)
    save_json(
        reports_dir / "ranked.json",
        {
            "shortlist_count": shortlist_count,
            "ranked": [asdict(report) for report in ranked],
        },
    )
    (reports_dir / "ranked.md").write_text(render_ranked_markdown(ranked, shortlist_count), encoding="utf-8")


def render_ranked_markdown(reports: Sequence[CandidateReport], shortlist_count: int) -> str:
    lines = ["# Ranked batch candidates", ""]
    lines.append(f"- Shortlist count: {shortlist_count}")
    lines.append("")
    for index, report in enumerate(reports, start=1):
        status = "pass" if report.passed else "fail"
        lines.append(f"{index}. {report.candidate} ({status}, {report.score:.2f})")
        if report.failures:
            lines.append(f"   - failures: {', '.join(report.failures)}")
        if report.metrics:
            metric_bits = ", ".join(f"{key}={value}" for key, value in report.metrics.items())
            lines.append(f"   - metrics: {metric_bits}")
    return "\n".join(lines) + "\n"


def sheet_thumbnail(sheet_path: Path, size: tuple[int, int] = DEFAULT_CELL_SIZE_THUMB) -> Image.Image:
    with Image.open(sheet_path) as opened:
        sheet = opened.convert("RGBA")
    return ImageOps.contain(sheet, size, method=Image.Resampling.LANCZOS)


def render_shortlist_board(batch_dir: Path, reports: Sequence[CandidateReport], shortlist_count: int) -> Path:
    top_reports = list(sorted(reports, key=lambda report: report.score, reverse=True)[:shortlist_count])
    if not top_reports:
        raise FileNotFoundError("No candidate reports available for shortlist board.")

    tile_width, tile_height = DEFAULT_BOARD_TILE_SIZE
    tile_padding = 16
    label_height = 64
    columns = 2 if len(top_reports) > 1 else 1
    rows = math.ceil(len(top_reports) / columns)
    board = Image.new(
        "RGBA",
        (columns * tile_width, rows * tile_height + 56),
        (24, 24, 28, 255),
    )
    draw = ImageDraw.Draw(board)
    font = ImageFont.load_default()

    title = f"Batch shortlist: {batch_dir.parents[1].name}/{batch_dir.name}"
    draw.text((16, 12), title, fill=(245, 245, 245, 255), font=font)

    for index, report in enumerate(top_reports):
        column = index % columns
        row = index // columns
        left = column * tile_width
        top = row * tile_height + 56
        tile = Image.new("RGBA", (tile_width, tile_height), (38, 38, 44, 255))
        tile_draw = ImageDraw.Draw(tile)
        border_color = (96, 196, 96, 255) if report.passed else (220, 80, 80, 255)
        tile_draw.rectangle((0, 0, tile_width - 1, tile_height - 1), outline=border_color, width=3)

        if report.sheet_path:
            thumb = sheet_thumbnail(Path(report.sheet_path), (tile_width - 2 * tile_padding, tile_height - label_height - 2 * tile_padding))
            x = (tile_width - thumb.width) // 2
            y = tile_padding
            tile.alpha_composite(thumb, (x, y))

        caption = f"{report.candidate}  score {report.score:.1f}"
        tile_draw.text((tile_padding, tile_height - 40), caption, fill=(250, 250, 250, 255), font=font)
        if report.failures:
            tile_draw.text((tile_padding, tile_height - 24), "; ".join(report.failures[:2]), fill=(255, 180, 180, 255), font=font)

        board.alpha_composite(tile, (left, top))

    board_path = compare_dir(batch_dir) / "shortlist-board.png"
    board.save(board_path)
    return board_path


def run_generator_command(command: str, env: dict[str, str]) -> None:
    subprocess.run(command, shell=True, check=True, env={**os.environ, **env})


def run_openai_adapter(
    prompt_path: Path,
    output_path: Path,
    anchor_images: Sequence[str],
    background_color: str,
) -> None:
    adapter = Path(__file__).with_name("openai_image_adapter.py")
    command = [
        sys.executable,
        str(adapter),
        "--prompt-file",
        str(prompt_path),
        "--output",
        str(output_path),
        "--model",
        "gpt-image-2",
        "--background",
        "auto",
    ]
    for anchor in anchor_images:
        command.extend(["--image", anchor])
    # The prompt file already carries the exact output contract and background color.
    # Keep the adapter focused on transport and let the prompt control composition.
    subprocess.run(command, check=True, env={**os.environ, "BATCH_BACKGROUND_COLOR": background_color})


def choose_selected_candidate(reports: Sequence[CandidateReport], candidate_name: str | None) -> CandidateReport:
    ranked = sorted(reports, key=lambda report: report.score, reverse=True)
    if candidate_name:
        for report in ranked:
            if report.candidate == candidate_name:
                return report
        raise FileNotFoundError(f"Candidate not found in reports: {candidate_name}")
    if not ranked:
        raise FileNotFoundError("No candidate reports available.")
    return ranked[0]


def cmd_init(args: argparse.Namespace) -> int:
    ensure_pillow()
    animation_name = slugify(args.animation_name)
    batch_name = slugify(args.batch_name or utc_batch_name())
    candidate_count = args.candidate_count
    prompt_variants = list(args.prompt_variant or [])
    if not prompt_variants:
        prompt_variants = default_variants(candidate_count)
    if len(prompt_variants) < candidate_count:
        prompt_variants.extend(default_variants(candidate_count - len(prompt_variants)))
    prompt_variants = prompt_variants[:candidate_count]
    base_prompt_text = Path(args.prompt_file).read_text(encoding="utf-8") if args.prompt_file else ""

    config = BatchConfig(
        animation_name=animation_name,
        batch_name=batch_name,
        subject=args.subject,
        action=args.action,
        direction=args.direction,
        candidate_count=candidate_count,
        shortlist_count=args.shortlist_count,
        max_rounds=args.max_rounds,
        fail_threshold=args.fail_threshold,
        seed_strategy=args.seed_strategy,
        anchor_images=[str(Path(anchor)) for anchor in args.anchor_image],
        columns=args.columns,
        rows=args.rows,
        base_prompt_text=base_prompt_text,
        prompt_variants=prompt_variants,
        locked_traits=build_locked_traits(args.subject, args.action, args.direction),
        allowed_variations=build_allowed_variations(),
        background_color=args.background_color,
        generate_command=args.generate_command or "",
        notes=args.notes or "",
    )

    batch_dir = init_workspace(config)
    print(batch_dir)
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    ensure_pillow()
    batch_dir = Path(args.batch_dir)
    config = load_batch_config(batch_dir)
    generate_command = args.generate_command or config.generate_command

    for index in range(1, config.candidate_count + 1):
        cdir = candidate_dir(batch_dir, index)
        cdir.mkdir(parents=True, exist_ok=True)
        prompt_path = candidate_prompt_path(batch_dir, index)
        if not prompt_path.exists():
            prompt_path.write_text(build_prompt_text(config, index), encoding="utf-8")

        if generate_command:
            sheet_path = candidate_sheet_path(batch_dir, config.animation_name, index)
            env = {
                "BATCH_DIR": str(batch_dir),
                "BATCH_CANDIDATE_DIR": str(cdir),
                "BATCH_PROMPT_FILE": str(prompt_path),
                "BATCH_OUTPUT_FILE": str(sheet_path),
                "BATCH_VARIANT_INDEX": str(index),
                "BATCH_VARIANT_NAME": config.prompt_variants[index - 1],
                "BATCH_ANIMATION_NAME": config.animation_name,
                "BATCH_BATCH_NAME": config.batch_name,
                "BATCH_CANDIDATE_COUNT": str(config.candidate_count),
                "BATCH_SHORTLIST_COUNT": str(config.shortlist_count),
                "BATCH_BACKGROUND_COLOR": config.background_color,
            }
            run_generator_command(generate_command.format(
                prompt_file=str(prompt_path),
                output_file=str(sheet_path),
                candidate_dir=str(cdir),
                batch_dir=str(batch_dir),
                animation_name=config.animation_name,
                batch_name=config.batch_name,
                candidate_index=index,
                variant_name=config.prompt_variants[index - 1],
            ), env)
        else:
            sheet_path = candidate_sheet_path(batch_dir, config.animation_name, index)
            run_openai_adapter(
                prompt_path=prompt_path,
                output_path=sheet_path,
                anchor_images=config.anchor_images,
                background_color=config.background_color,
            )

    print(batch_dir)
    return 0


def cmd_qc(args: argparse.Namespace) -> int:
    ensure_pillow()
    batch_dir = Path(args.batch_dir)
    config = load_batch_config(batch_dir)
    threshold = args.alpha_threshold if args.alpha_threshold is not None else DEFAULT_ALPHA_THRESHOLD

    sheet_paths = discover_candidate_sheets(batch_dir, config.animation_name)
    if not sheet_paths:
        raise FileNotFoundError(f"No candidate sheets found in: {batch_dir}")

    reports = [score_candidate_sheet(sheet_path, config, threshold) for sheet_path in sheet_paths]
    write_reports(batch_dir, reports, config.shortlist_count)
    print(render_ranked_markdown(sorted(reports, key=lambda report: report.score, reverse=True), config.shortlist_count))
    return 0


def cmd_board(args: argparse.Namespace) -> int:
    ensure_pillow()
    batch_dir = Path(args.batch_dir)
    reports_path = compare_dir(batch_dir) / "ranked.json"
    if not reports_path.exists():
        raise FileNotFoundError(f"Ranked report not found: {reports_path}")
    payload = load_json(reports_path)
    shortlist_payload = load_json(compare_dir(batch_dir) / "shortlist.json")
    reports = [CandidateReport(**item) for item in shortlist_payload.get("shortlist", [])]
    shortlist_count = int(payload.get("shortlist_count", DEFAULT_SHORTLIST_COUNT))
    board_path = render_shortlist_board(batch_dir, reports, shortlist_count)
    print(board_path)
    return 0


def cmd_promote(args: argparse.Namespace) -> int:
    ensure_pillow()
    batch_dir = Path(args.batch_dir)
    config = load_batch_config(batch_dir)
    reports_path = compare_dir(batch_dir) / "ranked.json"
    if not reports_path.exists():
        raise FileNotFoundError(f"Ranked report not found: {reports_path}")
    payload = load_json(reports_path)
    reports = [CandidateReport(**item) for item in payload.get("ranked", [])]
    selected = choose_selected_candidate(reports, args.candidate)

    if not selected.sheet_path:
        raise FileNotFoundError("Selected candidate has no sheet path.")
    source = Path(selected.sheet_path)
    if not source.is_file():
        raise FileNotFoundError(f"Selected candidate sheet not found: {source}")

    destination = generated_output(config.animation_name)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not args.overwrite:
        raise FileExistsError(f"Refusing to overwrite: {destination}")

    shutil.copy2(source, destination)
    print(destination)
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    ensure_pillow()
    animation_name = slugify(args.animation_name)
    batch_name = slugify(args.batch_name or utc_batch_name())

    prompt_variants = list(args.prompt_variant or [])
    if not prompt_variants:
        prompt_variants = default_variants(args.candidate_count)
    if len(prompt_variants) < args.candidate_count:
        prompt_variants.extend(default_variants(args.candidate_count - len(prompt_variants)))
    prompt_variants = prompt_variants[: args.candidate_count]
    base_prompt_text = Path(args.prompt_file).read_text(encoding="utf-8") if args.prompt_file else ""

    config = BatchConfig(
        animation_name=animation_name,
        batch_name=batch_name,
        subject=args.subject,
        action=args.action,
        direction=args.direction,
        candidate_count=args.candidate_count,
        shortlist_count=args.shortlist_count,
        max_rounds=args.max_rounds,
        fail_threshold=args.fail_threshold,
        seed_strategy=args.seed_strategy,
        anchor_images=[str(Path(anchor)) for anchor in args.anchor_image],
        columns=args.columns,
        rows=args.rows,
        base_prompt_text=base_prompt_text,
        prompt_variants=prompt_variants,
        locked_traits=build_locked_traits(args.subject, args.action, args.direction),
        allowed_variations=build_allowed_variations(),
        background_color=args.background_color,
        generate_command=args.generate_command or "",
        notes=args.notes or "",
    )
    batch_dir = init_workspace(config)
    if args.generate_command:
        cmd_generate(
            argparse.Namespace(batch_dir=str(batch_dir), generate_command=args.generate_command)
        )
    else:
        cmd_generate(argparse.Namespace(batch_dir=str(batch_dir), generate_command=""))
    cmd_qc(argparse.Namespace(batch_dir=str(batch_dir), alpha_threshold=args.alpha_threshold))
    cmd_board(argparse.Namespace(batch_dir=str(batch_dir)))
    return 0


def cmd_start(args: argparse.Namespace) -> int:
    ensure_pillow()
    if not args.config:
        raise ValueError("--config is required for start mode.")
    payload = load_json(Path(args.config))
    config = build_batch_config(payload)
    batch_dir = init_workspace(config)
    cmd_generate(argparse.Namespace(batch_dir=str(batch_dir), generate_command=config.generate_command))
    cmd_qc(argparse.Namespace(batch_dir=str(batch_dir), alpha_threshold=DEFAULT_ALPHA_THRESHOLD))
    cmd_board(argparse.Namespace(batch_dir=str(batch_dir)))
    print(batch_dir)
    return 0


def add_common_batch_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--animation-name", required=True, help="Filesystem-safe animation name.")
    parser.add_argument("--batch-name", help="Optional batch slug; defaults to a UTC timestamp.")
    parser.add_argument("--subject", required=True, help="Character or object being animated.")
    parser.add_argument("--action", required=True, help="Requested animation action.")
    parser.add_argument("--direction", help="Facing or movement direction, when applicable.")
    parser.add_argument(
        "--anchor-image",
        action="append",
        required=True,
        help="Anchor image path. Repeat for multiple references.",
    )
    parser.add_argument(
        "--candidate-count",
        type=int,
        default=DEFAULT_CANDIDATE_COUNT,
        help="Number of batch variants to create.",
    )
    parser.add_argument(
        "--shortlist-count",
        type=int,
        default=DEFAULT_SHORTLIST_COUNT,
        help="How many candidates should survive automatic QC.",
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=DEFAULT_MAX_ROUNDS,
        help="Maximum batch reroll rounds before pausing for user input.",
    )
    parser.add_argument(
        "--fail-threshold",
        type=float,
        default=DEFAULT_FAIL_THRESHOLD,
        help="Score below which a candidate is treated as rejected.",
    )
    parser.add_argument(
        "--seed-strategy",
        default="incremental",
        help="Seed strategy label to record in the batch manifest.",
    )
    parser.add_argument(
        "--prompt-variant",
        action="append",
        help="Optional human-readable variant note. Repeat for custom variants.",
    )
    parser.add_argument(
        "--columns",
        type=int,
        help="Optional grid columns for QC validation.",
    )
    parser.add_argument(
        "--rows",
        type=int,
        help="Optional grid rows for QC validation.",
    )
    parser.add_argument(
        "--notes",
        default="",
        help="Optional freeform batch notes.",
    )
    parser.add_argument(
        "--prompt-file",
        help="Optional text file containing your custom base prompt.",
    )
    parser.add_argument(
        "--background-color",
        default="#00FF00",
        help="Expected key/background color in hex, used during QC.",
    )
    parser.add_argument(
        "--generate-command",
        default="",
        help="Optional shell command template to run during candidate generation.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Batch spritesheet workflow helper.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a new batch workspace and prompt files.")
    add_common_batch_args(init_parser)
    init_parser.set_defaults(func=cmd_init)

    generate_parser = subparsers.add_parser("generate", help="Emit prompts and optionally execute a generator command.")
    generate_parser.add_argument("--batch-dir", required=True, help="Path to the batch workspace.")
    generate_parser.add_argument(
        "--generate-command",
        help="Optional shell command template to run for each candidate. It receives BATCH_* environment variables.",
    )
    generate_parser.set_defaults(func=cmd_generate)

    qc_parser = subparsers.add_parser("qc", help="Score and rank generated candidate sheets.")
    qc_parser.add_argument("--batch-dir", required=True, help="Path to the batch workspace.")
    qc_parser.add_argument(
        "--alpha-threshold",
        type=int,
        default=DEFAULT_ALPHA_THRESHOLD,
        help="Alpha threshold used to treat pixels as visible.",
    )
    qc_parser.set_defaults(func=cmd_qc)

    board_parser = subparsers.add_parser("board", help="Render a shortlist comparison board from QC results.")
    board_parser.add_argument("--batch-dir", required=True, help="Path to the batch workspace.")
    board_parser.set_defaults(func=cmd_board)

    promote_parser = subparsers.add_parser("promote", help="Promote one candidate into the standard workflow.")
    promote_parser.add_argument("--batch-dir", required=True, help="Path to the batch workspace.")
    promote_parser.add_argument(
        "--candidate",
        help="Candidate name to promote. If omitted, the top-ranked candidate is used.",
    )
    promote_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting the standard step-001 spritesheet output.",
    )
    promote_parser.set_defaults(func=cmd_promote)

    run_parser = subparsers.add_parser("run", help="Create a batch workspace, optionally generate candidates, and QC them.")
    add_common_batch_args(run_parser)
    run_parser.add_argument(
        "--alpha-threshold",
        type=int,
        default=DEFAULT_ALPHA_THRESHOLD,
        help="Alpha threshold used during QC.",
    )
    run_parser.set_defaults(func=cmd_run)

    start_parser = subparsers.add_parser("start", help="Run the full batch workflow from a JSON config file.")
    start_parser.add_argument("--config", required=True, help="Path to a JSON config file.")
    start_parser.set_defaults(func=cmd_start)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
