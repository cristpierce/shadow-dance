"""Fit a bounded post-decoder affine adapter from training-only proxy statistics."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--alpha", type=float, required=True)
    parser.add_argument("--ridge", type=float, default=1e-6)
    parser.add_argument("--gain-min", type=float, default=0.5)
    parser.add_argument("--gain-max", type=float, default=1.5)
    parser.add_argument("--bias-limit", type=float, default=0.5)
    args = parser.parse_args()
    if not 0.0 <= args.alpha <= 1.0:
        raise ValueError("alpha must be in [0, 1]")

    paths = sorted(args.input.glob("*.json"))
    if not paths:
        raise ValueError("no training statistics found")
    documents = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    if any("_train_" not in document["motion_id"] for document in documents):
        raise ValueError("refusing non-training motion in adapter fit")

    stats = [document["adapter_fit_sufficient_statistics"] for document in documents]
    frames = sum(int(stat["frames"]) for stat in stats)
    zeros = np.zeros(29, dtype=np.float64)
    sum_x = sum((np.asarray(stat["sum_x"]) for stat in stats), zeros.copy())
    sum_y = sum((np.asarray(stat["sum_y"]) for stat in stats), zeros.copy())
    sum_xx = sum((np.asarray(stat["sum_xx"]) for stat in stats), zeros.copy())
    sum_xy = sum((np.asarray(stat["sum_xy"]) for stat in stats), zeros.copy())
    variance = sum_xx - sum_x * sum_x / frames
    covariance = sum_xy - sum_x * sum_y / frames
    raw_gain = covariance / (variance + args.ridge)
    raw_bias = sum_y / frames - raw_gain * sum_x / frames

    bounded_gain = np.clip(raw_gain, args.gain_min, args.gain_max)
    bounded_bias = np.clip(raw_bias, -args.bias_limit, args.bias_limit)
    gain = 1.0 + args.alpha * (bounded_gain - 1.0)
    bias = args.alpha * bounded_bias
    output = {
        "format": "shadow_dance_affine_action_adapter_v1",
        "method": "training-only per-joint least-squares calibration with bounded shrinkage",
        "alpha": args.alpha,
        "ridge": args.ridge,
        "gain_bounds": [args.gain_min, args.gain_max],
        "bias_limit": args.bias_limit,
        "training_motion_count": len(paths),
        "training_frames": frames,
        "training_motion_ids": [document["motion_id"] for document in documents],
        "training_reports": [
            {"path": path.as_posix(), "sha256": sha256(path)} for path in paths
        ],
        "gain": gain.tolist(),
        "bias": bias.tolist(),
        "raw_fit_gain": raw_gain.tolist(),
        "raw_fit_bias": raw_bias.tolist(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
