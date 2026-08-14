#!/usr/bin/env python3
"""Turn SONIC's metrics_eval.json into a compact, auditable scorecard."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finite_number(value: Any, label: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} is not finite: {value!r}")
    return number


def summarize(payload: dict[str, Any], *, label: str, split: str, seed: int) -> dict[str, Any]:
    details = payload.get("eval/all_metrics_dict")
    if not isinstance(details, dict):
        raise ValueError("missing eval/all_metrics_dict")
    keys = details.get("motion_keys")
    terminated = details.get("terminated")
    progress = details.get("progress")
    if not isinstance(keys, list) or not keys:
        raise ValueError("motion_keys must be a non-empty list")
    if not isinstance(terminated, list) or len(terminated) != len(keys):
        raise ValueError("terminated length does not match motion_keys")
    if not isinstance(progress, list) or len(progress) != len(keys):
        raise ValueError("progress length does not match motion_keys")
    if len(set(map(str, keys))) != len(keys):
        raise ValueError("motion_keys contains duplicates")

    per_motion_fields: dict[str, list[Any]] = {}
    for name, values in details.items():
        if name in {"motion_keys", "sampling_prob", "terminated", "progress"}:
            continue
        if isinstance(values, list) and len(values) == len(keys):
            per_motion_fields[name] = values

    motions = []
    for index, key in enumerate(keys):
        row: dict[str, Any] = {
            "motion": str(key),
            "success": not bool(terminated[index]),
            "progress": finite_number(progress[index], f"progress[{index}]"),
        }
        for name, values in sorted(per_motion_fields.items()):
            value = values[index]
            if isinstance(value, int | float) and not isinstance(value, bool):
                row[name] = finite_number(value, f"{name}[{index}]")
        motions.append(row)

    successes = sum(row["success"] for row in motions)
    computed_success_rate = successes / len(motions)
    reported_success_rate = payload.get("eval/success/success_rate")
    if reported_success_rate is not None:
        reported_success_rate = finite_number(reported_success_rate, "reported success rate")
        if not math.isclose(reported_success_rate, computed_success_rate, abs_tol=1e-6):
            raise ValueError(
                "reported success rate does not match per-motion termination flags: "
                f"{reported_success_rate} != {computed_success_rate}"
            )

    aggregate: dict[str, float] = {}
    for name, value in sorted(payload.items()):
        if name.startswith(("eval/all/", "eval/success/")) and isinstance(value, int | float):
            aggregate[name] = finite_number(value, name)

    return {
        "format": "shadow_dance_eval_summary_v1",
        "label": label,
        "split": split,
        "seed": seed,
        "motion_count": len(motions),
        "success_count": successes,
        "success_rate": computed_success_rate,
        "progress_mean": sum(row["progress"] for row in motions) / len(motions),
        "aggregate": aggregate,
        "motions": motions,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("metrics", type=Path)
    parser.add_argument("--label", required=True)
    parser.add_argument("--split", required=True, choices=("heldout", "retention", "test"))
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--expected-motion-dir", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    payload = json.loads(args.metrics.read_text(encoding="utf-8"))
    result = summarize(payload, label=args.label, split=args.split, seed=args.seed)
    if args.expected_motion_dir is not None:
        expected_ids = sorted(
            path.stem for path in args.expected_motion_dir.rglob("*.pkl") if path.is_file()
        )
        if not expected_ids or len(set(expected_ids)) != len(expected_ids):
            raise ValueError("expected motion directory has an empty or duplicate inventory")
        observed_ids = sorted(str(row["motion"]) for row in result["motions"])
        if observed_ids != expected_ids:
            raise ValueError(
                "evaluated motion inventory differs from the requested directory: "
                f"expected={expected_ids}, observed={observed_ids}"
            )
        result["expected_motion_inventory_sha256"] = hashlib.sha256(
            json.dumps(expected_ids, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
    result["source"] = {
        "path": args.metrics.as_posix(),
        "sha256": sha256(args.metrics),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
