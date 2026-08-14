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

ORT_DTYPES = {
    "tensor(bool)": np.bool_,
    "tensor(double)": np.float64,
    "tensor(float)": np.float32,
    "tensor(float16)": np.float16,
    "tensor(int8)": np.int8,
    "tensor(int16)": np.int16,
    "tensor(int32)": np.int32,
    "tensor(int64)": np.int64,
    "tensor(uint8)": np.uint8,
    "tensor(uint16)": np.uint16,
    "tensor(uint32)": np.uint32,
    "tensor(uint64)": np.uint64,
}
SONIC_SUFFIXES = (
    "_smpl.onnx",
    "_g1.onnx",
    "_teleop.onnx",
    "_encoder.onnx",
    "_decoder.onnx",
)


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
    feed = {}
    for value in session.get_inputs():
        dtype = ORT_DTYPES.get(value.type)
        if dtype is None:
            raise ValueError(f"unsupported ONNX Runtime input type {value.type}: {path.name}")
        probe_shape = [dim if isinstance(dim, int) and dim > 0 else 1 for dim in value.shape]
        feed[value.name] = np.zeros(probe_shape, dtype=dtype)
    result = session.run(None, feed)
    inference = {
        "attempted": True,
        "passed": all(array.size > 0 and np.isfinite(array).all() for array in result),
        "output_summaries": [
            {
                "shape": list(array.shape),
                "dtype": str(array.dtype),
                "min": float(array.min()),
                "max": float(array.max()),
            }
            for array in result
        ],
    }
    if not inference["passed"]:
        raise ValueError(f"ONNX Runtime inference returned empty or non-finite output: {path.name}")
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
    matches = {
        suffix: [path for path in files if path.name.endswith(suffix)] for suffix in SONIC_SUFFIXES
    }
    invalid = {suffix: paths for suffix, paths in matches.items() if len(paths) != 1}
    if invalid:
        rendered = {suffix: [path.name for path in paths] for suffix, paths in invalid.items()}
        raise SystemExit(f"Incomplete or ambiguous SONIC ONNX bundle: {rendered}")
    prefixes = {paths[0].name.removesuffix(suffix) for suffix, paths in matches.items()}
    if len(prefixes) != 1 or len(files) != len(SONIC_SUFFIXES):
        raise SystemExit("SONIC ONNX files do not form one exact five-graph export bundle")
    portal_nominee = matches["_g1.onnx"][0].name
    report = {
        "format": "shadow_dance_onnx_validation_v1",
        "overall_pass": True,
        "portal_nominee": portal_nominee,
        "bundle_prefix": prefixes.pop(),
        "artifacts": [inspect(path) for path in files],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
