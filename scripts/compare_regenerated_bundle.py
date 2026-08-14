#!/usr/bin/env python3
"""Prove cross-platform regeneration is numerically equivalent to the frozen bundle."""

from __future__ import annotations

import argparse
import copy
import csv
import json
import math
from pathlib import Path
from typing import Any

import joblib
import numpy as np


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def payload_paths(root: Path, suffix: str) -> dict[str, Path]:
    return {
        path.relative_to(root).as_posix(): path
        for path in sorted(root.rglob(f"*{suffix}"))
        if path.is_file()
    }


def compare_array(reference: Any, candidate: Any, label: str, atol: float) -> float:
    reference_array = np.asarray(reference)
    candidate_array = np.asarray(candidate)
    require(reference_array.shape == candidate_array.shape, f"{label}: shape drift")
    require(reference_array.dtype == candidate_array.dtype, f"{label}: dtype drift")
    require(np.isfinite(reference_array).all(), f"{label}: reference contains non-finite values")
    require(np.isfinite(candidate_array).all(), f"{label}: candidate contains non-finite values")
    difference = float(np.max(np.abs(reference_array - candidate_array), initial=0.0))
    require(difference <= atol, f"{label}: max absolute drift {difference:.9g} exceeds {atol}")
    return difference


def compare_csvs(reference_root: Path, candidate_root: Path, atol: float) -> tuple[int, float]:
    reference_paths = payload_paths(reference_root, ".csv")
    candidate_paths = payload_paths(candidate_root, ".csv")
    require(reference_paths.keys() == candidate_paths.keys(), "CSV relative-path inventory drift")
    maximum = 0.0
    for relative, reference_path in reference_paths.items():
        candidate_path = candidate_paths[relative]
        with reference_path.open(newline="", encoding="utf-8") as stream:
            reference_rows = list(csv.reader(stream))
        with candidate_path.open(newline="", encoding="utf-8") as stream:
            candidate_rows = list(csv.reader(stream))
        require(reference_rows[0] == candidate_rows[0], f"{relative}: CSV header drift")
        reference_values = np.asarray(reference_rows[1:], dtype=np.float64)
        candidate_values = np.asarray(candidate_rows[1:], dtype=np.float64)
        maximum = max(
            maximum,
            compare_array(reference_values, candidate_values, f"{relative}: CSV", atol),
        )
    return len(reference_paths), maximum


def compare_pkls(reference_root: Path, candidate_root: Path, atol: float) -> tuple[int, float]:
    reference_paths = payload_paths(reference_root, ".pkl")
    candidate_paths = payload_paths(candidate_root, ".pkl")
    require(reference_paths.keys() == candidate_paths.keys(), "PKL relative-path inventory drift")
    maximum = 0.0
    for relative, reference_path in reference_paths.items():
        reference_data = joblib.load(reference_path)
        candidate_data = joblib.load(candidate_paths[relative])
        require(reference_data.keys() == candidate_data.keys(), f"{relative}: motion ID drift")
        require(len(reference_data) == 1, f"{relative}: expected exactly one motion")
        motion_id = next(iter(reference_data))
        reference_entry = reference_data[motion_id]
        candidate_entry = candidate_data[motion_id]
        require(reference_entry.keys() == candidate_entry.keys(), f"{relative}: field drift")
        for field, reference_value in reference_entry.items():
            candidate_value = candidate_entry[field]
            if isinstance(reference_value, np.ndarray):
                maximum = max(
                    maximum,
                    compare_array(
                        reference_value,
                        candidate_value,
                        f"{relative}:{field}",
                        atol,
                    ),
                )
            else:
                require(reference_value == candidate_value, f"{relative}:{field}: value drift")
    return len(reference_paths), maximum


def manifest_contract(document: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(document)
    for record in result["sequences"]:
        record.pop("ik_max_position_error_m")
        record.pop("ik_max_orientation_error_deg")
        record["files"].pop("motion_lib_sha256")
        record["files"].pop("source_csv_sha256")
    return result


def compare_manifests(reference_path: Path, candidate_path: Path, atol: float) -> float:
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    require(manifest_contract(reference) == manifest_contract(candidate), "manifest contract drift")
    maximum = 0.0
    for reference_record, candidate_record in zip(
        reference["sequences"], candidate["sequences"], strict=True
    ):
        for field in ("ik_max_position_error_m", "ik_max_orientation_error_deg"):
            difference = abs(float(reference_record[field]) - float(candidate_record[field]))
            maximum = max(maximum, difference)
            require(
                difference <= atol,
                f"{reference_record['id']}:{field}: drift {difference:.9g} exceeds {atol}",
            )
    return maximum


def compare_scalar(reference: Any, candidate: Any, label: str, atol: float) -> float:
    if isinstance(reference, bool) or isinstance(candidate, bool):
        require(reference is candidate, f"{label}: boolean drift")
        return 0.0
    if isinstance(reference, (int, float)) and isinstance(candidate, (int, float)):
        require(
            math.isfinite(reference) and math.isfinite(candidate), f"{label}: non-finite metric"
        )
        difference = abs(float(reference) - float(candidate))
        require(difference <= atol, f"{label}: metric drift {difference:.9g} exceeds {atol}")
        return difference
    require(reference == candidate, f"{label}: value drift")
    return 0.0


def compare_reports(reference_path: Path, candidate_path: Path, atol: float) -> float:
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    for document in (reference, candidate):
        document.pop("dataset_dir")
        document.pop("mjcf")
    reference_sequences = reference.pop("sequences")
    candidate_sequences = candidate.pop("sequences")
    require(reference == candidate, "validation summary or manifest-check drift")
    require(len(reference_sequences) == len(candidate_sequences), "validation sequence-count drift")

    maximum = 0.0
    for reference_record, candidate_record in zip(
        reference_sequences, candidate_sequences, strict=True
    ):
        reference_metrics = reference_record.pop("metrics")
        candidate_metrics = candidate_record.pop("metrics")
        reference_record.pop("sha256")
        candidate_record.pop("sha256")
        require(reference_record == candidate_record, "validation per-sequence contract drift")
        require(reference_metrics.keys() == candidate_metrics.keys(), "validation metric-key drift")
        for key, reference_value in reference_metrics.items():
            maximum = max(
                maximum,
                compare_scalar(
                    reference_value,
                    candidate_metrics[key],
                    f"{reference_record['id']}:{key}",
                    atol,
                ),
            )
    return maximum


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--candidate-manifest", type=Path, required=True)
    parser.add_argument("--candidate-report", type=Path, required=True)
    parser.add_argument("--reference-root", type=Path, default=Path("data/generated"))
    parser.add_argument(
        "--reference-manifest", type=Path, default=Path("data/manifests/shadow-dip-v1.json")
    )
    parser.add_argument(
        "--reference-report", type=Path, default=Path("results/reference-validation.json")
    )
    parser.add_argument("--atol", type=float, default=1e-6)
    args = parser.parse_args()
    require(args.atol > 0, "absolute tolerance must be positive")

    csv_count, csv_maximum = compare_csvs(args.reference_root, args.candidate_root, args.atol)
    pkl_count, pkl_maximum = compare_pkls(args.reference_root, args.candidate_root, args.atol)
    manifest_maximum = compare_manifests(
        args.reference_manifest, args.candidate_manifest, args.atol
    )
    report_maximum = compare_reports(args.reference_report, args.candidate_report, args.atol)
    print(
        json.dumps(
            {
                "format": "shadow_dance_cross_platform_reproduction_v1",
                "absolute_tolerance": args.atol,
                "csv_files": csv_count,
                "pkl_files": pkl_count,
                "csv_max_abs_drift": csv_maximum,
                "pkl_max_abs_drift": pkl_maximum,
                "manifest_ik_max_abs_drift": manifest_maximum,
                "validation_metric_max_abs_drift": report_maximum,
                "equivalent": True,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
