#!/usr/bin/env python3
"""Fail closed when stock SONIC already clears the pre-registered hero gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("summary", type=Path)
    parser.add_argument("--max-stock-success", type=float, default=0.75)
    parser.add_argument("--min-stock-mpjpe-l", type=float, default=50.0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.summary.read_text(encoding="utf-8"))
    if (
        payload.get("format") != "shadow_dance_eval_summary_v1"
        or payload.get("label") != "stock"
        or payload.get("split") != "heldout"
        or not isinstance(payload.get("seed"), int)
    ):
        raise ValueError("novelty gate requires a stock heldout evaluation summary")
    success_rate = float(payload["success_rate"])
    mpjpe_l = float(payload["aggregate"]["eval/all/mpjpe_l"])
    if not 0 <= success_rate <= 1 or not math.isfinite(mpjpe_l) or mpjpe_l <= 0:
        raise ValueError("novelty summary contains invalid metrics")
    novelty = success_rate <= args.max_stock_success or mpjpe_l >= args.min_stock_mpjpe_l
    report = {
        "format": "shadow_dance_novelty_gate_v1",
        "novelty_gate_pass": novelty,
        "stock_success_rate": success_rate,
        "stock_mpjpe_l": mpjpe_l,
        "max_stock_success": args.max_stock_success,
        "min_stock_mpjpe_l": args.min_stock_mpjpe_l,
        "source": {
            "path": f"summaries/{args.summary.name}",
            "sha256": hashlib.sha256(args.summary.read_bytes()).hexdigest(),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not novelty:
        raise SystemExit(3)


if __name__ == "__main__":
    main()
