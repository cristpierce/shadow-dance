#!/usr/bin/env python3
"""Bind untouched test summaries to the preregistered selected checkpoint."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_summary(path: Path, expected_label: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("format") != "shadow_dance_eval_aggregate_v1":
        raise ValueError(f"final comparison requires a repeated-evaluation aggregate: {path}")
    if payload.get("split") != "test":
        raise ValueError(f"final comparison requires the untouched test split: {path}")
    if payload.get("label") != expected_label:
        raise ValueError(f"expected label {expected_label!r}, got {payload.get('label')!r}")
    return payload


def compact(summary: dict[str, Any], *, label: str) -> dict[str, float | int]:
    result = {
        "motion_count": int(summary["motion_count"]),
        "seed_count": int(summary["seed_count"]),
        "trial_count": int(summary["trial_count"]),
        "success_count": int(summary["success_count"]),
        "success_rate": float(summary["success_rate"]),
        "mpjpe_l": float(summary["mpjpe_l"]),
    }
    if result["motion_count"] <= 0:
        raise ValueError(f"{label} has no motions")
    if result["seed_count"] < 3:
        raise ValueError(f"{label} has fewer than three independent seeds")
    if result["trial_count"] != result["motion_count"] * result["seed_count"]:
        raise ValueError(f"{label} has an inconsistent trial count")
    if not 0 <= result["success_count"] <= result["trial_count"]:
        raise ValueError(f"{label} has an invalid success count")
    expected_rate = result["success_count"] / result["trial_count"]
    if not math.isfinite(result["success_rate"]) or not math.isclose(
        result["success_rate"], expected_rate, abs_tol=1e-9
    ):
        raise ValueError(f"{label} has an inconsistent success rate")
    if not math.isfinite(result["mpjpe_l"]) or result["mpjpe_l"] <= 0:
        raise ValueError(f"{label} has a non-positive or non-finite MPJPE")
    return result


def motion_ids(summary: dict[str, Any], *, label: str) -> tuple[str, ...]:
    motions = summary.get("motion_inventory")
    if not isinstance(motions, list) or len(motions) != int(summary["motion_count"]):
        raise ValueError(f"{label} has an invalid motion inventory")
    identifiers = tuple(str(motion) for motion in motions)
    if len(set(identifiers)) != len(identifiers):
        raise ValueError(f"{label} has duplicate motion identifiers")
    return identifiers


def seeds(summary: dict[str, Any], *, label: str) -> tuple[int, ...]:
    values = summary.get("seeds")
    if not isinstance(values, list) or len(values) != int(summary["seed_count"]):
        raise ValueError(f"{label} has an invalid seed inventory")
    identifiers = tuple(int(seed) for seed in values)
    if len(set(identifiers)) != len(identifiers):
        raise ValueError(f"{label} has duplicate seeds")
    return identifiers


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--stock-test", type=Path, required=True)
    parser.add_argument("--selected-test", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    selection = json.loads(args.selection.read_text(encoding="utf-8"))
    if selection.get("format") != "shadow_dance_checkpoint_selection_v1":
        raise ValueError("unsupported checkpoint selection report")
    selected = selection.get("selected")
    if not isinstance(selected, dict) or not selected.get("eligible"):
        raise ValueError("checkpoint selection has no eligible winner")
    label = str(selected["label"])
    stock_summary = load_summary(args.stock_test, "stock")
    selected_summary = load_summary(args.selected_test, label)
    stock = compact(stock_summary, label="stock test")
    adapted = compact(selected_summary, label=f"{label} test")
    stock_ids = motion_ids(stock_summary, label="stock test")
    selected_ids = motion_ids(selected_summary, label=f"{label} test")
    if stock_ids != selected_ids:
        raise ValueError("stock and selected test summaries have different motion inventories")
    stock_seeds = seeds(stock_summary, label="stock test")
    selected_seeds = seeds(selected_summary, label=f"{label} test")
    if stock_seeds != selected_seeds:
        raise ValueError("stock and selected test summaries have different seed inventories")

    report = {
        "format": "shadow_dance_final_comparison_v1",
        "split": "test",
        "used_for_checkpoint_selection": False,
        "selected_label": label,
        "selection_report_sha256": sha256(args.selection),
        "stock": stock,
        "selected": adapted,
        "success_rate_delta": adapted["success_rate"] - stock["success_rate"],
        "mpjpe_l_improvement_fraction": 1.0 - adapted["mpjpe_l"] / stock["mpjpe_l"],
        "motion_inventory_sha256": hashlib.sha256(
            json.dumps(stock_ids, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "seed_inventory_sha256": hashlib.sha256(
            json.dumps(stock_seeds, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "sources": {
            "stock_summary": {
                "path": f"summaries/{args.stock_test.name}",
                "sha256": sha256(args.stock_test),
            },
            "selected_summary": {
                "path": f"summaries/{args.selected_test.name}",
                "sha256": sha256(args.selected_test),
            },
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
