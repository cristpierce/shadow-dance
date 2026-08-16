#!/usr/bin/env python3
"""Build an honest, hash-bound target/before/after submission video."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont

CANVAS_WIDTH = 1280
CANVAS_HEIGHT = 720
HEADER_HEIGHT = 92
FOOTER_HEIGHT = 86
PANEL_WIDTH = CANVAS_WIDTH // 2
PANEL_HEIGHT = CANVAS_HEIGHT - HEADER_HEIGHT - FOOTER_HEIGHT
EXPECTED_CANDIDATE_LABELS = {
    "stage-5",
    "stage-250",
    "stage-500",
    "stage-2000",
    "stage-4000",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def positive_number(value: Any, label: str) -> float:
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise ValueError(f"{label} must be finite and positive")
    return result


def load_comparison(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("format") != "shadow_dance_final_comparison_v1":
        raise ValueError("unsupported final-comparison format")
    if payload.get("split") != "test" or payload.get("used_for_checkpoint_selection") is not False:
        raise ValueError("video metrics must come from the untouched final-test report")
    for label in ("stock", "selected"):
        summary = payload.get(label)
        if not isinstance(summary, dict):
            raise ValueError(f"final comparison has no {label} result")
        motions = int(summary.get("motion_count", 0))
        seeds = int(summary.get("seed_count", 0))
        trials = int(summary.get("trial_count", 0))
        successes = int(summary.get("success_count", -1))
        rate = float(summary.get("success_rate", -1))
        if motions <= 0 or seeds < 3 or trials != motions * seeds:
            raise ValueError(f"{label} final-test inventory is invalid")
        if not 0 <= successes <= trials or not math.isclose(rate, successes / trials, abs_tol=1e-9):
            raise ValueError(f"{label} final-test success rate is inconsistent")
        positive_number(summary.get("mpjpe_l"), f"{label} MPJPE")
    if payload["stock"]["motion_count"] != payload["selected"]["motion_count"]:
        raise ValueError("stock and selected motion counts differ")
    if payload["stock"]["seed_count"] != payload["selected"]["seed_count"]:
        raise ValueError("stock and selected seed counts differ")
    selected_label = str(payload.get("selected_label", ""))
    if selected_label not in EXPECTED_CANDIDATE_LABELS:
        raise ValueError("final comparison has no valid frozen checkpoint label")
    return payload


def matched_clips(
    stock_dir: Path, selected_dir: Path, *, expected_count: int
) -> list[tuple[Path, Path]]:
    stock = {path.name: path for path in stock_dir.glob("*.mp4") if path.is_file()}
    selected = {path.name: path for path in selected_dir.glob("*.mp4") if path.is_file()}
    if set(stock) != set(selected):
        raise ValueError(
            "stock and selected render inventories differ: "
            f"stock_only={sorted(set(stock) - set(selected))}, "
            f"selected_only={sorted(set(selected) - set(stock))}"
        )
    if len(stock) != expected_count:
        raise ValueError(f"expected {expected_count} matched policy videos, found {len(stock)}")
    expected_names = {f"{index:06d}.mp4" for index in range(expected_count)}
    if set(stock) != expected_names:
        raise ValueError(
            "policy render filenames do not encode the expected ordered environments: "
            f"expected={sorted(expected_names)}, observed={sorted(stock)}"
        )
    pairs = [(stock[name], selected[name]) for name in sorted(stock)]
    for left, right in pairs:
        if left.stat().st_size <= 0 or right.stat().st_size <= 0:
            raise ValueError(f"empty policy video in pair {left.name}")
    return pairs


def load_motion_ids(path: Path, *, expected_count: int) -> list[str]:
    identifiers = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    identifiers = [identifier for identifier in identifiers if identifier]
    if len(identifiers) != expected_count or len(set(identifiers)) != len(identifiers):
        raise ValueError(
            "motion-ID inventory does not match the rendered environment count: "
            f"expected={expected_count}, observed={identifiers}"
        )
    return identifiers


def font(size: int, *, bold: bool = False) -> ImageFont.ImageFont:
    names = (
        ["C:/Windows/Fonts/arialbd.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
        if bold
        else ["C:/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    )
    for name in names:
        try:
            return ImageFont.truetype(name, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def fit_frame(frame: np.ndarray, width: int, height: int) -> Image.Image:
    source = Image.fromarray(np.asarray(frame, dtype=np.uint8)).convert("RGB")
    source.thumbnail((width, height), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (width, height), "black")
    canvas.paste(source, ((width - source.width) // 2, (height - source.height) // 2))
    return canvas


def centered(
    draw: ImageDraw.ImageDraw, text: str, y: int, *, face: ImageFont.ImageFont, fill: str
) -> None:
    bounds = draw.textbbox((0, 0), text, font=face)
    draw.text(((CANVAS_WIDTH - (bounds[2] - bounds[0])) / 2, y), text, font=face, fill=fill)


def metric_lines(comparison: dict[str, Any]) -> tuple[str, str]:
    stock = comparison["stock"]
    selected = comparison["selected"]
    return (
        f"Untouched final test: stock {stock['success_count']}/{stock['trial_count']} | "
        f"selected {selected['success_count']}/{selected['trial_count']}",
        f"Local MPJPE: {stock['mpjpe_l']:.1f} mm -> {selected['mpjpe_l']:.1f} mm | "
        f"{stock['motion_count']} motions x {stock['seed_count']} seeds per policy",
    )


def title_card(comparison: dict[str, Any], *, subtitle: str) -> np.ndarray:
    image = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), (7, 11, 20))
    draw = ImageDraw.Draw(image)
    centered(draw, "G1 SHADOW DANCE", 165, face=font(58, bold=True), fill="#f7f9fc")
    centered(draw, subtitle, 250, face=font(34, bold=True), fill="#65d7ff")
    line_one, line_two = metric_lines(comparison)
    centered(draw, line_one, 365, face=font(27, bold=True), fill="#f7f9fc")
    centered(draw, line_two, 414, face=font(23), fill="#b9c3d3")
    centered(
        draw,
        "Simulation only | winner frozen before test | uncut source runs published",
        545,
        face=font(21),
        fill="#8f9bad",
    )
    return np.asarray(image)


def reference_frame(frame: np.ndarray) -> np.ndarray:
    image = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), (5, 7, 12))
    image.paste(fit_frame(frame, CANVAS_WIDTH, PANEL_HEIGHT), (0, HEADER_HEIGHT))
    draw = ImageDraw.Draw(image)
    centered(
        draw,
        "KINEMATIC TARGET - NOT POLICY OUTPUT",
        25,
        face=font(30, bold=True),
        fill="#65d7ff",
    )
    centered(
        draw,
        "Team-authored reference trajectory: frame, pivot, unsupported dip, hold, recover",
        CANVAS_HEIGHT - FOOTER_HEIGHT + 27,
        face=font(21),
        fill="#dbe4f0",
    )
    return np.asarray(image)


def comparison_frame(
    stock_frame: np.ndarray,
    selected_frame: np.ndarray,
    *,
    clip_index: int,
    clip_count: int,
    motion_id: str,
    selected_label: str,
    render_seed: int,
    stock_ended: bool,
    selected_ended: bool,
) -> np.ndarray:
    image = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), (5, 7, 12))
    image.paste(fit_frame(stock_frame, PANEL_WIDTH, PANEL_HEIGHT), (0, HEADER_HEIGHT))
    image.paste(
        fit_frame(selected_frame, PANEL_WIDTH, PANEL_HEIGHT),
        (PANEL_WIDTH, HEADER_HEIGHT),
    )
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, PANEL_WIDTH, HEADER_HEIGHT), fill=(45, 17, 18))
    draw.rectangle((PANEL_WIDTH, 0, CANVAS_WIDTH, HEADER_HEIGHT), fill=(10, 43, 31))
    draw.text((28, 25), "BEFORE | STOCK SONIC", font=font(29, bold=True), fill="#ffb1a9")
    draw.text(
        (PANEL_WIDTH + 28, 25),
        f"AFTER | {selected_label.upper()}",
        font=font(29, bold=True),
        fill="#8ff0b7",
    )
    if stock_ended:
        draw.rectangle((18, HEADER_HEIGHT + 18, 214, HEADER_HEIGHT + 64), fill=(0, 0, 0))
        draw.text((29, HEADER_HEIGHT + 27), "RUN ENDED", font=font(20, bold=True), fill="#ffb1a9")
    if selected_ended:
        draw.rectangle(
            (PANEL_WIDTH + 18, HEADER_HEIGHT + 18, PANEL_WIDTH + 214, HEADER_HEIGHT + 64),
            fill=(0, 0, 0),
        )
        draw.text(
            (PANEL_WIDTH + 29, HEADER_HEIGHT + 27),
            "RUN ENDED",
            font=font(20, bold=True),
            fill="#8ff0b7",
        )
    centered(
        draw,
        f"{motion_id} | motion {clip_index}/{clip_count} | seed {render_seed} | full run",
        CANVAS_HEIGHT - FOOTER_HEIGHT + 27,
        face=font(22),
        fill="#dbe4f0",
    )
    return np.asarray(image)


def reader_fps(reader: Any, path: Path) -> float:
    fps = positive_number(reader.get_meta_data().get("fps"), f"frame rate for {path}")
    return fps


def resampled_frames(reader: Any, *, source_fps: float, target_fps: float) -> Iterator[np.ndarray]:
    accumulator = 0.0
    first = True
    for frame in reader:
        if first:
            yield frame
            first = False
            continue
        accumulator += target_fps
        while accumulator >= source_fps:
            yield frame
            accumulator -= source_fps


def source_entry(path: Path, *, media_root: Path) -> dict[str, Any]:
    try:
        display = path.resolve().relative_to(media_root.resolve()).as_posix()
    except ValueError:
        display = path.name
    reader = imageio.get_reader(path)
    try:
        metadata = reader.get_meta_data()
        fps = positive_number(metadata.get("fps"), f"frame rate for {path}")
        duration = positive_number(metadata.get("duration"), f"duration for {path}")
    finally:
        reader.close()
    return {
        "path": display,
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "fps": fps,
        "duration_seconds": duration,
    }


def encode(
    *,
    pairs: list[tuple[Path, Path]],
    reference: Path,
    comparison: dict[str, Any],
    motion_ids: list[str],
    output: Path,
    render_seed: int,
    max_clip_seconds: float,
) -> tuple[float, int]:
    first_reader = imageio.get_reader(pairs[0][0])
    try:
        output_fps = reader_fps(first_reader, pairs[0][0])
    finally:
        first_reader.close()
    if output_fps > 120:
        raise ValueError(f"unreasonable output frame rate: {output_fps}")

    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_name(f".{output.stem}.partial{output.suffix}")
    writer = imageio.get_writer(
        partial,
        fps=output_fps,
        codec="libx264",
        quality=8,
        pixelformat="yuv420p",
        macro_block_size=1,
    )
    frame_count = 0

    def append(frame: np.ndarray) -> None:
        nonlocal frame_count
        writer.append_data(frame)
        frame_count += 1

    try:
        for _ in range(round(output_fps * 2.0)):
            append(
                title_card(
                    comparison,
                    subtitle=(
                        "THE UNSUPPORTED PARTNER DIP | "
                        f"{comparison['selected_label'].upper()}"
                    ),
                )
            )

        reference_reader = imageio.get_reader(reference)
        try:
            reference_fps = reader_fps(reference_reader, reference)
            reference_limit = round(max_clip_seconds * output_fps)
            for index, frame in enumerate(
                resampled_frames(reference_reader, source_fps=reference_fps, target_fps=output_fps)
            ):
                if index >= reference_limit:
                    raise ValueError("reference video exceeds the configured full-run limit")
                append(reference_frame(frame))
        finally:
            reference_reader.close()

        pair_limit = round(max_clip_seconds * output_fps)
        for pair_index, (stock_path, selected_path) in enumerate(pairs, start=1):
            stock_reader = imageio.get_reader(stock_path)
            selected_reader = imageio.get_reader(selected_path)
            try:
                stock_fps = reader_fps(stock_reader, stock_path)
                selected_fps = reader_fps(selected_reader, selected_path)
                if not math.isclose(stock_fps, output_fps, abs_tol=0.05) or not math.isclose(
                    selected_fps, output_fps, abs_tol=0.05
                ):
                    raise ValueError("matched policy clips must have an identical frame rate")
                stock_iter = iter(stock_reader)
                selected_iter = iter(selected_reader)
                stock_last = selected_last = None
                stock_done = selected_done = False
                emitted = 0
                while True:
                    if not stock_done:
                        try:
                            stock_last = next(stock_iter)
                        except StopIteration:
                            stock_done = True
                    if not selected_done:
                        try:
                            selected_last = next(selected_iter)
                        except StopIteration:
                            selected_done = True
                    if stock_last is None or selected_last is None:
                        raise ValueError(f"unreadable or empty policy clip pair: {stock_path.name}")
                    if stock_done and selected_done:
                        break
                    if emitted >= pair_limit:
                        raise ValueError(
                            f"policy clip {stock_path.name} exceeds the configured full-run limit"
                        )
                    append(
                        comparison_frame(
                            stock_last,
                            selected_last,
                            clip_index=pair_index,
                            clip_count=len(pairs),
                            motion_id=motion_ids[pair_index - 1],
                            selected_label=comparison["selected_label"],
                            render_seed=render_seed,
                            stock_ended=stock_done,
                            selected_ended=selected_done,
                        )
                    )
                    emitted += 1
            finally:
                stock_reader.close()
                selected_reader.close()

        for _ in range(round(output_fps * 2.0)):
            append(title_card(comparison, subtitle="REPRODUCIBLE EVIDENCE, NOT A BEAUTY TAKE"))
    except Exception:
        writer.close()
        partial.unlink(missing_ok=True)
        raise
    else:
        writer.close()
        partial.replace(output)
    return output_fps, frame_count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stock-dir", type=Path, required=True)
    parser.add_argument("--selected-dir", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--motion-ids", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--render-seed", type=int, required=True)
    parser.add_argument("--max-clip-seconds", type=float, default=12.0)
    args = parser.parse_args()

    if args.render_seed < 0:
        raise ValueError("render seed must be non-negative")
    if not 1 <= args.max_clip_seconds <= 60:
        raise ValueError("max clip duration must be between 1 and 60 seconds")
    comparison = load_comparison(args.comparison)
    pairs = matched_clips(
        args.stock_dir,
        args.selected_dir,
        expected_count=int(comparison["stock"]["motion_count"]),
    )
    motion_ids = load_motion_ids(args.motion_ids, expected_count=len(pairs))
    if not args.reference.is_file() or args.reference.stat().st_size <= 0:
        raise ValueError("reference video is missing or empty")

    output_fps, frame_count = encode(
        pairs=pairs,
        reference=args.reference,
        comparison=comparison,
        motion_ids=motion_ids,
        output=args.output,
        render_seed=args.render_seed,
        max_clip_seconds=args.max_clip_seconds,
    )
    manifest_path = args.manifest or args.output.with_suffix(".json")
    media_root = args.output.parent
    report = {
        "format": "shadow_dance_video_manifest_v1",
        "edited_comparison": True,
        "reference_is_policy_output": False,
        "source_policy_runs_uncut": True,
        "selected_label": comparison["selected_label"],
        "render_seed": args.render_seed,
        "final_comparison": {
            "path": args.comparison.name,
            "sha256": sha256(args.comparison),
        },
        "reference": source_entry(args.reference, media_root=media_root),
        "stock": [
            {**source_entry(left, media_root=media_root), "motion": motion_ids[index]}
            for index, (left, _) in enumerate(pairs)
        ],
        "selected": [
            {**source_entry(right, media_root=media_root), "motion": motion_ids[index]}
            for index, (_, right) in enumerate(pairs)
        ],
        "output": {
            "path": args.output.name,
            "bytes": args.output.stat().st_size,
            "sha256": sha256(args.output),
            "fps": output_fps,
            "frame_count": frame_count,
            "duration_seconds": frame_count / output_fps,
        },
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
