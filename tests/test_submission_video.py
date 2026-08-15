from __future__ import annotations

import hashlib
import json
import runpy
import subprocess
import sys
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
import pytest

ROOT = Path(__file__).parents[1]


def write_clip(path: Path, *, color: tuple[int, int, int]) -> None:
    writer = imageio.get_writer(
        path,
        fps=5,
        codec="libx264",
        pixelformat="yuv420p",
        macro_block_size=1,
    )
    try:
        for index in range(5):
            frame = np.zeros((64, 96, 3), dtype=np.uint8)
            frame[:, :, :] = color
            frame[12:52, 8 + index * 8 : 24 + index * 8] = (240, 240, 240)
            writer.append_data(frame)
    finally:
        writer.close()


def test_submission_video_binds_full_matched_runs(tmp_path: Path) -> None:
    stock_dir = tmp_path / "media" / "stock"
    selected_dir = tmp_path / "media" / "selected"
    stock_dir.mkdir(parents=True)
    selected_dir.mkdir(parents=True)
    for index in range(2):
        write_clip(stock_dir / f"{index:06d}.mp4", color=(90, 20, 20))
        write_clip(selected_dir / f"{index:06d}.mp4", color=(20, 90, 45))
    reference = tmp_path / "media" / "reference-kinematic.mp4"
    write_clip(reference, color=(20, 45, 90))

    comparison = {
        "format": "shadow_dance_final_comparison_v1",
        "split": "test",
        "used_for_checkpoint_selection": False,
        "selected_label": "stage-500",
        "stock": {
            "motion_count": 2,
            "seed_count": 3,
            "trial_count": 6,
            "success_count": 1,
            "success_rate": 1 / 6,
            "mpjpe_l": 80.0,
        },
        "selected": {
            "motion_count": 2,
            "seed_count": 3,
            "trial_count": 6,
            "success_count": 6,
            "success_rate": 1.0,
            "mpjpe_l": 28.0,
        },
    }
    comparison_path = tmp_path / "final-comparison.json"
    comparison_path.write_text(json.dumps(comparison), encoding="utf-8")
    output = tmp_path / "media" / "hero-before-after.mp4"
    manifest = tmp_path / "media" / "video-manifest.json"
    motion_ids = tmp_path / "test-motions.txt"
    motion_ids.write_text("motion_alpha\nmotion_beta\n", encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_submission_video.py"),
            "--stock-dir",
            str(stock_dir),
            "--selected-dir",
            str(selected_dir),
            "--reference",
            str(reference),
            "--comparison",
            str(comparison_path),
            "--motion-ids",
            str(motion_ids),
            "--output",
            str(output),
            "--manifest",
            str(manifest),
            "--render-seed",
            "303",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(manifest.read_text(encoding="utf-8"))
    assert report["format"] == "shadow_dance_video_manifest_v1"
    assert report["source_policy_runs_uncut"] is True
    assert report["selected_label"] == "stage-500"
    assert len(report["stock"]) == len(report["selected"]) == 2
    assert [entry["motion"] for entry in report["stock"]] == ["motion_alpha", "motion_beta"]
    assert report["output"]["sha256"] == hashlib.sha256(output.read_bytes()).hexdigest()
    assert report["output"]["duration_seconds"] > 5


def test_submission_video_rejects_mismatched_clip_inventory(tmp_path: Path) -> None:
    stock = tmp_path / "stock"
    selected = tmp_path / "selected"
    stock.mkdir()
    selected.mkdir()
    (stock / "000000.mp4").write_bytes(b"stock")
    (selected / "000001.mp4").write_bytes(b"selected")
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import importlib.util,pathlib; "
                f"p=pathlib.Path({str(ROOT / 'scripts' / 'build_submission_video.py')!r}); "
                "s=importlib.util.spec_from_file_location('video',p); "
                "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
                f"m.matched_clips(pathlib.Path({str(stock)!r}), "
                f"pathlib.Path({str(selected)!r}), expected_count=1)"
            ),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "inventories differ" in result.stderr


def test_submission_video_rejects_nonfrozen_checkpoint_label(tmp_path: Path) -> None:
    summary = {
        "motion_count": 1,
        "seed_count": 3,
        "trial_count": 3,
        "success_count": 1,
        "success_rate": 1 / 3,
        "mpjpe_l": 50.0,
    }
    comparison = {
        "format": "shadow_dance_final_comparison_v1",
        "split": "test",
        "used_for_checkpoint_selection": False,
        "selected_label": "stage-2000",
        "stock": summary,
        "selected": summary,
    }
    comparison_path = tmp_path / "final-comparison.json"
    comparison_path.write_text(json.dumps(comparison), encoding="utf-8")
    load_comparison = runpy.run_path(str(ROOT / "scripts" / "build_submission_video.py"))[
        "load_comparison"
    ]

    with pytest.raises(ValueError, match="valid frozen checkpoint label"):
        load_comparison(comparison_path)
