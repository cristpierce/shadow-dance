"""Compose frame-locked stock and exported-adapter proxy renders."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stock", type=Path, required=True)
    parser.add_argument("--selected", type=Path, required=True)
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    comparison = json.loads(args.comparison.read_text(encoding="utf-8"))
    stock_reader = imageio.get_reader(args.stock)
    selected_reader = imageio.get_reader(args.selected)
    stock_meta = stock_reader.get_meta_data()
    selected_meta = selected_reader.get_meta_data()
    if stock_meta["fps"] != selected_meta["fps"] or stock_meta["size"] != selected_meta["size"]:
        raise ValueError("source video contract drift")
    if tuple(stock_meta["size"]) != (960, 480):
        raise ValueError("unexpected source video size")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    writer = imageio.get_writer(
        args.output, fps=stock_meta["fps"], codec="libx264", quality=8
    )
    frames = 0
    font = ImageFont.load_default(size=19)
    small = ImageFont.load_default(size=15)
    try:
        for stock_frame, selected_frame in zip(stock_reader, selected_reader, strict=True):
            stock_policy = np.asarray(stock_frame)[72:440, 480:960]
            selected_policy = np.asarray(selected_frame)[72:440, 480:960]
            scene = np.concatenate((stock_policy, selected_policy), axis=1)
            canvas = Image.new("RGB", (960, 480), (7, 11, 18))
            canvas.paste(Image.fromarray(scene), (0, 72))
            draw = ImageDraw.Draw(canvas)
            draw.text((18, 7), "STOCK SONIC", fill=(100, 210, 255), font=font)
            draw.text((500, 7), "AFFINE PROXY ADAPTER", fill=(126, 240, 150), font=font)
            draw.text(
                (18, 40),
                "EXPERIMENTAL MUJOCO PROXY | NOT ISAAC/PPO/WBT-BENCH",
                fill="white",
                font=small,
            )
            draw.rectangle((0, 440, 960, 480), fill=(7, 11, 18))
            draw.text(
                (18, 451),
                (
                    "8-motion macro: joint RMSE 9.54 -> 8.63 deg | "
                    "local MPJPE 29.23 -> 29.45 mm (worse)"
                ),
                fill=(255, 220, 120),
                font=small,
            )
            writer.append_data(np.asarray(canvas))
            frames += 1
    finally:
        writer.close()
        stock_reader.close()
        selected_reader.close()
    if frames <= 0:
        raise ValueError("no video frames composed")

    report = {
        "format": "shadow_dance_proxy_adapter_video_v1",
        "official_sonic_recipe": False,
        "official_wbt_bench": False,
        "isaac_result": False,
        "motion_selection": "first lexicographic fresh gancho test; not selected by result",
        "frames": frames,
        "fps": stock_meta["fps"],
        "duration_seconds": frames / stock_meta["fps"],
        "stock_source": {"path": args.stock.as_posix(), "sha256": sha256(args.stock)},
        "selected_source": {
            "path": args.selected.as_posix(),
            "sha256": sha256(args.selected),
        },
        "comparison": {
            "path": args.comparison.as_posix(),
            "sha256": sha256(args.comparison),
            "selected_decoder_sha256": comparison["selected_decoder_sha256"],
        },
        "output": {
            "path": args.output.as_posix(),
            "sha256": sha256(args.output),
            "bytes": args.output.stat().st_size,
        },
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
