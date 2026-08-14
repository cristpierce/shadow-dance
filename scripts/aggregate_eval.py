#!/usr/bin/env python3
"""Aggregate repeated SONIC evaluations across an identical motion inventory."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

MPJPE_L = "eval/all/mpjpe_l"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finite_positive(value: Any, label: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{label} must be finite and positive")
    return number


def load_summary(path: Path, *, label: str, split: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("format") != "shadow_dance_eval_summary_v1":
        raise ValueError(f"unsupported summary format: {path}")
    if payload.get("label") != label or payload.get("split") != split:
        raise ValueError(f"wrong label or split: {path}")
    if not isinstance(payload.get("seed"), int):
        raise ValueError(f"summary has no integer seed: {path}")
    motions = payload.get("motions")
    if not isinstance(motions, list) or len(motions) != int(payload.get("motion_count", 0)):
        raise ValueError(f"summary has an invalid motion inventory: {path}")
    if MPJPE_L not in payload.get("aggregate", {}):
        raise ValueError(f"summary lacks {MPJPE_L}: {path}")
    finite_positive(payload["aggregate"][MPJPE_L], f"aggregate MPJPE in {path}")
    return payload


def build_aggregate(
    payloads: list[dict[str, Any]],
    source_paths: list[Path],
    *,
    label: str,
    split: str,
) -> dict[str, Any]:
    if not payloads or len(payloads) != len(source_paths):
        raise ValueError("aggregate requires one source path per non-empty summary")
    seeds = [int(payload["seed"]) for payload in payloads]
    if len(set(seeds)) != len(seeds):
        raise ValueError("evaluation summaries contain duplicate seeds")
    first_ids = tuple(str(row["motion"]) for row in payloads[0]["motions"])
    if not first_ids or len(set(first_ids)) != len(first_ids):
        raise ValueError("evaluation summaries contain empty or duplicate motion IDs")

    per_motion: dict[str, list[dict[str, Any]]] = {motion_id: [] for motion_id in first_ids}
    seed_results = []
    for path, payload in zip(source_paths, payloads, strict=True):
        motion_ids = tuple(str(row["motion"]) for row in payload["motions"])
        if motion_ids != first_ids:
            raise ValueError(f"motion inventory differs across seeds: {path}")
        success_count = int(payload["success_count"])
        expected_rate = success_count / len(first_ids)
        if not math.isclose(float(payload["success_rate"]), expected_rate, abs_tol=1e-9):
            raise ValueError(f"summary has an inconsistent success rate: {path}")
        for row in payload["motions"]:
            if "mpjpe_l" not in row:
                raise ValueError(f"summary lacks per-motion mpjpe_l: {path}")
            finite_positive(row["mpjpe_l"], f"per-motion MPJPE in {path}")
            per_motion[str(row["motion"])].append(row)
        seed_results.append(
            {
                "seed": int(payload["seed"]),
                "success_count": success_count,
                "success_rate": float(payload["success_rate"]),
                "mpjpe_l": float(payload["aggregate"][MPJPE_L]),
            }
        )

    motion_results = []
    for motion_id in first_ids:
        trials = per_motion[motion_id]
        successes = sum(bool(row["success"]) for row in trials)
        motion_results.append(
            {
                "motion": motion_id,
                "trial_count": len(trials),
                "success_count": successes,
                "success_rate": successes / len(trials),
                "mpjpe_l_macro_mean": sum(float(row["mpjpe_l"]) for row in trials) / len(trials),
            }
        )

    trial_count = len(first_ids) * len(payloads)
    success_count = sum(row["success_count"] for row in motion_results)
    return {
        "format": "shadow_dance_eval_aggregate_v1",
        "label": label,
        "split": split,
        "motion_count": len(first_ids),
        "seed_count": len(seeds),
        "trial_count": trial_count,
        "success_count": success_count,
        "success_rate": success_count / trial_count,
        "mpjpe_l": sum(row["mpjpe_l_macro_mean"] for row in motion_results) / len(motion_results),
        "mpjpe_l_definition": "macro mean across motion-by-seed trial means, millimetres",
        "motion_inventory": list(first_ids),
        "seeds": seeds,
        "seed_results": seed_results,
        "motions": motion_results,
        "sources": [
            {
                "path": f"summaries/{path.name}",
                "sha256": sha256(path),
            }
            for path in source_paths
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("summaries", nargs="+", type=Path)
    parser.add_argument("--label", required=True)
    parser.add_argument("--split", required=True, choices=("heldout", "retention", "test"))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    payloads = [load_summary(path, label=args.label, split=args.split) for path in args.summaries]
    report = build_aggregate(
        payloads,
        args.summaries,
        label=args.label,
        split=args.split,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
