#!/usr/bin/env python3
"""Verify the committed motion/CSV bundle against its frozen manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/manifests/shadow-dip-v1.json"),
    )
    parser.add_argument("--dataset-root", type=Path, default=Path("data/generated"))
    parser.add_argument("--splits-root", type=Path, default=Path("data/splits"))
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    failures: list[str] = []
    checked = 0
    expected_upstream = {
        "repository": "https://github.com/NVlabs/GR00T-WholeBodyControl",
        "commit": "c374bae5b9039cd0ee71377e654d11ce1bc69e1d",
        "mjcf": "gear_sonic/data/assets/robot_description/mjcf/g1_29dof_rev_1_0.xml",
    }
    expected_metadata = {
        "dataset": "shadow-dip-v1",
        "generator": "shadow-dance",
        "generator_version": "0.1.0",
        "license": "Apache-2.0",
        "contains_bones_seed": False,
    }
    for key, expected in expected_metadata.items():
        if manifest.get(key) != expected:
            failures.append(f"manifest {key} differs from the frozen value {expected!r}")
    if manifest.get("upstream") != expected_upstream:
        failures.append("manifest upstream repository, commit, or MJCF identity drifted")
    sequences = manifest.get("sequences")
    if not isinstance(sequences, list):
        raise SystemExit("manifest sequences must be an array")
    identifiers = [str(sequence.get("id", "")) for sequence in sequences]
    if not all(identifiers) or len(set(identifiers)) != len(identifiers):
        failures.append("manifest sequence IDs are empty or duplicated")

    computed_splits: dict[str, list[str]] = {}
    expected_payloads: set[str] = set()
    dataset_root = args.dataset_root.resolve()
    for sequence in sequences:
        split = str(sequence.get("split", ""))
        computed_splits.setdefault(split, []).append(str(sequence.get("id", "")))
        expected_sequence_metadata = {
            "robot": "unitree_g1_29dof",
            "source": "team-authored procedural keyframes plus MuJoCo foot IK",
            "source_license": "Apache-2.0",
            "performer_consent": "not_applicable_synthetic",
            "upstream_mjcf_commit": expected_upstream["commit"],
            "fps": 50,
            "smpl": "dummy",
        }
        for key, expected in expected_sequence_metadata.items():
            if sequence.get(key) != expected:
                failures.append(f"sequence {sequence.get('id')} {key} differs from {expected!r}")
        files = sequence["files"]
        for path_key, hash_key in (
            ("motion_lib", "motion_lib_sha256"),
            ("source_csv", "source_csv_sha256"),
        ):
            relative = str(files[path_key])
            if relative in expected_payloads:
                failures.append(f"duplicate manifest payload path: {relative}")
            expected_payloads.add(relative)
            path = (args.dataset_root / relative).resolve()
            try:
                path.relative_to(dataset_root)
            except ValueError:
                failures.append(f"payload escapes dataset root: {relative}")
                continue
            if not path.is_file():
                failures.append(f"missing: {path.as_posix()}")
                continue
            actual = sha256(path)
            expected = files[hash_key]
            if actual != expected:
                failures.append(
                    f"hash mismatch: {path.as_posix()} expected={expected} actual={actual}"
                )
            checked += 1

    if len(sequences) != manifest.get("sequence_count"):
        failures.append("manifest sequence_count does not match sequences array")
    if manifest.get("splits") != computed_splits:
        failures.append("manifest splits do not match sequence order and membership")
    expected_split_counts = {"train": 18, "heldout": 4, "test": 4}
    observed_split_counts = {name: len(values) for name, values in computed_splits.items()}
    if observed_split_counts != expected_split_counts:
        failures.append(
            f"frozen split counts drifted: expected={expected_split_counts} "
            f"observed={observed_split_counts}"
        )
    for split, expected_ids in computed_splits.items():
        split_file = args.splits_root / f"{split}.txt"
        if not split_file.is_file():
            failures.append(f"missing split file: {split_file.as_posix()}")
            continue
        observed_ids = [
            line.strip()
            for line in split_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if observed_ids != expected_ids:
            failures.append(f"split file differs from manifest: {split_file.as_posix()}")
    discovered_split_names = {
        path.stem for path in args.splits_root.glob("*.txt") if path.is_file()
    }
    if discovered_split_names != set(computed_splits):
        failures.append(
            "split-file inventory mismatch: "
            f"expected={sorted(computed_splits)} observed={sorted(discovered_split_names)}"
        )

    discovered_payloads = {
        path.relative_to(dataset_root).as_posix()
        for pattern in ("*.pkl", "*.csv")
        for path in dataset_root.rglob(pattern)
        if path.is_file()
    }
    if discovered_payloads != expected_payloads:
        missing = sorted(expected_payloads - discovered_payloads)
        extra = sorted(discovered_payloads - expected_payloads)
        failures.append(f"dataset payload inventory mismatch: missing={missing}, extra={extra}")
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"dataset bundle verified: {manifest['sequence_count']} sequences, {checked} files")


if __name__ == "__main__":
    main()
