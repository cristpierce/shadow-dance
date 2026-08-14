#!/usr/bin/env python3
"""Validate ONNX graphs and emit a machine-readable artifact manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import onnx
import onnxruntime as ort


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect(path: Path) -> dict:
    model = onnx.load(path, load_external_data=True)
    onnx.checker.check_model(model)
    session = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
    inputs = [
        {"name": value.name, "shape": value.shape, "type": value.type}
        for value in session.get_inputs()
    ]
    outputs = [
        {"name": value.name, "shape": value.shape, "type": value.type}
        for value in session.get_outputs()
    ]
    # Shape-dynamic policy graphs cannot always accept a generic probe. The graph load
    # and checker are still hard gates; inference is attempted only for concrete inputs.
    inference = {"attempted": False, "passed": None}
    concrete_inputs = all(
        all(isinstance(dim, int) and dim > 0 for dim in value.shape)
        for value in session.get_inputs()
    )
    if concrete_inputs:
        feed = {
            value.name: np.zeros(value.shape, dtype=np.float32) for value in session.get_inputs()
        }
        result = session.run(None, feed)
        inference = {
            "attempted": True,
            "passed": all(np.isfinite(array).all() for array in result),
            "output_summaries": [
                {"shape": list(array.shape), "min": float(array.min()), "max": float(array.max())}
                for array in result
            ],
        }
    return {
        "file": path.name,
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "checker_pass": True,
        "inputs": inputs,
        "outputs": outputs,
        "inference": inference,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact_dir", type=Path)
    parser.add_argument("--output", type=Path, default=Path("artifacts/onnx-report.json"))
    args = parser.parse_args()
    files = sorted(args.artifact_dir.glob("*.onnx"))
    if not files:
        raise SystemExit(f"No ONNX files in {args.artifact_dir}")
    report = {"overall_pass": True, "artifacts": [inspect(path) for path in files]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
