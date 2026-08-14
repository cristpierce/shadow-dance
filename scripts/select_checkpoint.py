#!/usr/bin/env python3
"""Apply the frozen novelty, improvement, and retention gates to checkpoints."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

MPJPE_L = "eval/all/mpjpe_l"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_entry(path: Path, *, label: str, split: str) -> dict[str, str]:
    return {
        "label": label,
        "split": split,
        "path": f"summaries/{path.name}",
        "sha256": sha256(path),
    }


def load_summary(path: Path, expected_split: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("format") != "shadow_dance_eval_summary_v1":
        raise ValueError(f"unsupported summary format: {path}")
    if payload.get("split") != expected_split:
        raise ValueError(f"{path} is not a {expected_split} summary")
    if MPJPE_L not in payload.get("aggregate", {}):
        raise ValueError(f"{path} does not contain {MPJPE_L}")
    return payload


def compact(summary: dict[str, Any], *, label: str) -> dict[str, float | int]:
    result = {
        "motion_count": int(summary["motion_count"]),
        "success_count": int(summary["success_count"]),
        "success_rate": float(summary["success_rate"]),
        "mpjpe_l": float(summary["aggregate"][MPJPE_L]),
    }
    if result["motion_count"] <= 0:
        raise ValueError(f"{label} has no motions")
    if not 0 <= result["success_count"] <= result["motion_count"]:
        raise ValueError(f"{label} has an invalid success count")
    expected_rate = result["success_count"] / result["motion_count"]
    if not math.isfinite(result["success_rate"]) or not math.isclose(
        result["success_rate"], expected_rate, abs_tol=1e-9
    ):
        raise ValueError(f"{label} has an inconsistent success rate")
    if not math.isfinite(result["mpjpe_l"]) or result["mpjpe_l"] <= 0:
        raise ValueError(f"{label} has a non-positive or non-finite MPJPE")
    return result


def motion_ids(summary: dict[str, Any], *, label: str) -> tuple[str, ...]:
    motions = summary.get("motions")
    if not isinstance(motions, list) or len(motions) != int(summary["motion_count"]):
        raise ValueError(f"{label} has an invalid motion inventory")
    identifiers = tuple(str(row["motion"]) for row in motions)
    if len(set(identifiers)) != len(identifiers):
        raise ValueError(f"{label} has duplicate motion identifiers")
    return identifiers


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stock-heldout", type=Path, required=True)
    parser.add_argument("--stock-retention", type=Path, required=True)
    parser.add_argument(
        "--candidate",
        nargs=4,
        action="append",
        metavar=("LABEL", "CHECKPOINT", "HELDOUT", "RETENTION"),
        required=True,
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--require-eligible", action="store_true")
    parser.add_argument("--max-stock-success", type=float, default=0.75)
    parser.add_argument("--min-stock-mpjpe-l", type=float, default=50.0)
    parser.add_argument("--min-hero-success-delta", type=float, default=0.25)
    parser.add_argument("--min-hero-mpjpe-improvement", type=float, default=0.10)
    parser.add_argument("--max-retention-success-drop", type=float, default=1 / 6)
    parser.add_argument("--max-retention-mpjpe-increase", type=float, default=0.15)
    args = parser.parse_args()

    stock_held_summary = load_summary(args.stock_heldout, "heldout")
    stock_ret_summary = load_summary(args.stock_retention, "retention")
    if stock_held_summary.get("label") != "stock" or stock_ret_summary.get("label") != "stock":
        raise ValueError("stock summaries must use label 'stock'")
    stock_held = compact(stock_held_summary, label="stock heldout")
    stock_ret = compact(stock_ret_summary, label="stock retention")
    stock_held_ids = motion_ids(stock_held_summary, label="stock heldout")
    stock_ret_ids = motion_ids(stock_ret_summary, label="stock retention")
    selection_seed = int(stock_held_summary.get("seed", -1))
    if selection_seed < 0 or int(stock_ret_summary.get("seed", -2)) != selection_seed:
        raise ValueError("stock selection summaries use different or invalid seeds")
    novelty = (
        stock_held["success_rate"] <= args.max_stock_success
        or stock_held["mpjpe_l"] >= args.min_stock_mpjpe_l
    )

    candidates = []
    candidate_sources: dict[str, dict[str, dict[str, str]]] = {}
    labels: set[str] = set()
    for label, checkpoint, held_path, ret_path in args.candidate:
        if label in labels:
            raise ValueError(f"duplicate candidate label: {label}")
        labels.add(label)
        held_summary = load_summary(Path(held_path), "heldout")
        ret_summary = load_summary(Path(ret_path), "retention")
        if held_summary.get("label") != label or ret_summary.get("label") != label:
            raise ValueError(f"{label} summaries have the wrong label")
        if (
            int(held_summary.get("seed", -1)) != selection_seed
            or int(ret_summary.get("seed", -1)) != selection_seed
        ):
            raise ValueError(f"{label} selection summaries use the wrong seed")
        if motion_ids(held_summary, label=f"{label} heldout") != stock_held_ids:
            raise ValueError(f"{label} heldout motions differ from stock")
        if motion_ids(ret_summary, label=f"{label} retention") != stock_ret_ids:
            raise ValueError(f"{label} retention motions differ from stock")
        held = compact(held_summary, label=f"{label} heldout")
        retention = compact(ret_summary, label=f"{label} retention")
        checkpoint_path = Path(checkpoint).resolve()
        if not checkpoint_path.is_file():
            raise ValueError(f"candidate checkpoint does not exist: {checkpoint}")
        success_delta = held["success_rate"] - stock_held["success_rate"]
        mpjpe_improvement = 1.0 - held["mpjpe_l"] / stock_held["mpjpe_l"]
        retention_success_delta = retention["success_rate"] - stock_ret["success_rate"]
        retention_mpjpe_increase = retention["mpjpe_l"] / stock_ret["mpjpe_l"] - 1.0
        hero_improved = success_delta >= args.min_hero_success_delta or (
            success_delta >= 0.0 and mpjpe_improvement >= args.min_hero_mpjpe_improvement
        )
        retention_ok = (
            retention_success_delta >= -args.max_retention_success_drop
            and retention_mpjpe_increase <= args.max_retention_mpjpe_increase
        )
        candidates.append(
            {
                "label": label,
                "checkpoint": str(checkpoint_path),
                "checkpoint_size_bytes": checkpoint_path.stat().st_size,
                "checkpoint_sha256": sha256(checkpoint_path),
                "heldout": held,
                "retention": retention,
                "hero_success_delta": success_delta,
                "hero_mpjpe_improvement_fraction": mpjpe_improvement,
                "retention_success_delta": retention_success_delta,
                "retention_mpjpe_increase_fraction": retention_mpjpe_increase,
                "hero_improved": hero_improved,
                "retention_ok": retention_ok,
                "eligible": bool(novelty and hero_improved and retention_ok),
            }
        )
        candidate_sources[label] = {
            "heldout": source_entry(Path(held_path), label=label, split="heldout"),
            "retention": source_entry(Path(ret_path), label=label, split="retention"),
        }

    eligible = [candidate for candidate in candidates if candidate["eligible"]]
    selected = max(
        eligible,
        key=lambda item: (
            item["heldout"]["success_rate"],
            -item["heldout"]["mpjpe_l"],
            item["retention"]["success_rate"],
            -item["retention"]["mpjpe_l"],
        ),
        default=None,
    )
    report = {
        "format": "shadow_dance_checkpoint_selection_v1",
        "thresholds": {
            "max_stock_success": args.max_stock_success,
            "min_stock_mpjpe_l": args.min_stock_mpjpe_l,
            "min_hero_success_delta": args.min_hero_success_delta,
            "min_hero_mpjpe_improvement": args.min_hero_mpjpe_improvement,
            "max_retention_success_drop": args.max_retention_success_drop,
            "max_retention_mpjpe_increase": args.max_retention_mpjpe_increase,
        },
        "stock_heldout": stock_held,
        "stock_retention": stock_ret,
        "selection_seed": selection_seed,
        "sources": {
            "stock_heldout": source_entry(args.stock_heldout, label="stock", split="heldout"),
            "stock_retention": source_entry(args.stock_retention, label="stock", split="retention"),
            "candidates": candidate_sources,
        },
        "novelty_gate_pass": novelty,
        "candidates": candidates,
        "selected": selected,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if args.require_eligible and selected is None:
        raise SystemExit(4)


if __name__ == "__main__":
    main()
