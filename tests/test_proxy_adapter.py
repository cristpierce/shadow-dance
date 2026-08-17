from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]


def write_fit_report(path: Path, motion_id: str) -> None:
    path.write_text(
        json.dumps(
            {
                "motion_id": motion_id,
                "adapter_fit_sufficient_statistics": {
                    "frames": 2,
                    "sum_x": [1.0] * 29,
                    "sum_y": [2.0] * 29,
                    "sum_xx": [1.0] * 29,
                    "sum_xy": [2.0] * 29,
                },
            }
        ),
        encoding="utf-8",
    )


def run_fit(input_dir: Path, output: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "fit_action_adapter.py"),
            "--input",
            str(input_dir),
            "--output",
            str(output),
            "--alpha",
            "0.1",
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_adapter_fit_is_bounded_and_training_only(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    write_fit_report(reports / "train.json", "shadow_gancho_left_train_01")
    output = tmp_path / "adapter.json"

    process = run_fit(reports, output)

    assert process.returncode == 0, process.stderr
    adapter = json.loads(output.read_text(encoding="utf-8"))
    assert adapter["training_motion_count"] == 1
    assert adapter["training_frames"] == 2
    assert len(adapter["gain"]) == 29
    assert len(adapter["bias"]) == 29
    assert all(0.95 <= value <= 1.05 for value in adapter["gain"])
    assert all(-0.05 <= value <= 0.05 for value in adapter["bias"])


def test_adapter_fit_rejects_heldout_report(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    write_fit_report(reports / "heldout.json", "shadow_gancho_left_heldout_01")

    process = run_fit(reports, tmp_path / "adapter.json")

    assert process.returncode != 0
    assert "refusing non-training motion" in process.stderr
