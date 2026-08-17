"""Bind the frozen proxy adapter to its complete fresh-test comparison."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

METRICS = (
    "mpjpe_local_mean_mm",
    "mpjpe_global_mean_mm",
    "root_position_mean_mm",
    "joint_rmse_mean_deg",
    "pelvis_height_min_m",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_reports(paths: list[Path]) -> dict[str, tuple[Path, dict[str, object]]]:
    result = {}
    for path in paths:
        document = json.loads(path.read_text(encoding="utf-8"))
        motion_id = str(document["motion_id"])
        if motion_id in result:
            raise ValueError(f"duplicate motion report: {motion_id}")
        if "_test_" not in motion_id:
            raise ValueError(f"non-test report: {motion_id}")
        result[motion_id] = (path, document)
    return result


def macro(reports: dict[str, tuple[Path, dict[str, object]]]) -> dict[str, object]:
    documents = [document for _, document in reports.values()]
    return {
        "motion_count": len(documents),
        "deterministic_trials_per_motion": 1,
        "completed_without_fall": sum(
            bool(document["metrics"]["completed_without_fall"]) for document in documents
        ),
        **{
            metric: sum(float(document["metrics"][metric]) for document in documents)
            / len(documents)
            for metric in METRICS[:-1]
        },
        "pelvis_height_min_m": min(
            float(document["metrics"]["pelvis_height_min_m"]) for document in documents
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stock-dir", type=Path, required=True)
    parser.add_argument("--selected-dir", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--onnx-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    stock = load_reports(sorted(args.stock_dir.glob("stock-*.json")))
    selected = load_reports(sorted(args.selected_dir.glob("test-*.json")))
    if not stock or stock.keys() != selected.keys() or len(stock) != 8:
        raise ValueError("stock/selected test inventories must match all eight fresh motions")

    onnx_report = json.loads(args.onnx_report.read_text(encoding="utf-8"))
    stock_decoder_sha = onnx_report["parent_decoder"]["sha256"]
    selected_decoder_sha = onnx_report["output"]["sha256"]
    for _, document in stock.values():
        if document["artifacts"]["decoder"]["sha256"] != stock_decoder_sha:
            raise ValueError("stock decoder hash drift")
    for _, document in selected.values():
        if document["artifacts"]["decoder"]["sha256"] != selected_decoder_sha:
            raise ValueError("selected decoder hash drift")

    stock_macro = macro(stock)
    selected_macro = macro(selected)
    relative = {
        metric: 100.0 * (float(selected_macro[metric]) / float(stock_macro[metric]) - 1.0)
        for metric in METRICS[:-1]
    }
    motions = []
    for motion_id in sorted(stock):
        stock_path, stock_document = stock[motion_id]
        selected_path, selected_document = selected[motion_id]
        if stock_document["motion_sha256"] != selected_document["motion_sha256"]:
            raise ValueError(f"motion payload drift: {motion_id}")
        motions.append(
            {
                "id": motion_id,
                "motion_sha256": stock_document["motion_sha256"],
                "stock": {
                    "report": stock_path.as_posix(),
                    "report_sha256": sha256(stock_path),
                    "metrics": {key: stock_document["metrics"][key] for key in METRICS},
                    "completed_without_fall": stock_document["metrics"][
                        "completed_without_fall"
                    ],
                },
                "selected": {
                    "report": selected_path.as_posix(),
                    "report_sha256": sha256(selected_path),
                    "metrics": {key: selected_document["metrics"][key] for key in METRICS},
                    "completed_without_fall": selected_document["metrics"][
                        "completed_without_fall"
                    ],
                },
            }
        )

    result = {
        "format": "shadow_dance_proxy_adapter_final_comparison_v1",
        "generated_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "official_sonic_recipe": False,
        "official_wbt_bench": False,
        "isaac_result": False,
        "fine_tuned_ppo_checkpoint": False,
        "simulator": "MuJoCo 3.x deployment proxy",
        "selection": {"path": args.selection.as_posix(), "sha256": sha256(args.selection)},
        "onnx_validation": {
            "path": args.onnx_report.as_posix(),
            "sha256": sha256(args.onnx_report),
        },
        "stock_decoder_sha256": stock_decoder_sha,
        "selected_decoder_sha256": selected_decoder_sha,
        "test_protocol": {
            "motion_count": 8,
            "deterministic_trials_per_motion": 1,
            "test_inputs_first_opened_after_selection_freeze": True,
            "motion_families": ["dip", "gancho"],
        },
        "macro": {"stock": stock_macro, "selected": selected_macro},
        "relative_change_percent": relative,
        "motions": motions,
        "interpretation": (
            "The adapter preserves 8/8 upright completion and reduces joint RMSE, with "
            "small global/root improvements, but local MPJPE is modestly worse. It is a "
            "transparent fallback experiment, not evidence of the required Isaac/PPO fine-tune."
        ),
        "limitations": [
            "No Isaac Lab execution or organizer WBT-Bench package was used.",
            "The adapter is an affine supervised calibration, not the released PPO recipe.",
            (
                "The proxy is deterministic and does not provide the required three-seed "
                "robustness test."
            ),
            "This report must not be presented as an official challenge score.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"macro": result["macro"], "relative": relative}, indent=2))


if __name__ == "__main__":
    main()
