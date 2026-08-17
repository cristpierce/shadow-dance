#!/usr/bin/env python3
"""Publish the frozen dataset files to a Hugging Face dataset repository."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from huggingface_hub import CommitOperationAdd, CommitOperationDelete, HfApi


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_reference_report(report: dict[str, Any], manifest: dict[str, Any]) -> None:
    sequences = manifest.get("sequences")
    results = report.get("sequences")
    if not isinstance(sequences, list) or not isinstance(results, list):
        raise ValueError("manifest or reference report has no sequence inventory")
    count = len(sequences)
    if (
        report.get("overall_pass") is not True
        or int(report.get("sequence_count", 0)) != count
        or int(report.get("passed", 0)) != count
        or int(report.get("failed", -1)) != 0
        or int(report.get("warning_count", -1)) != 0
    ):
        raise ValueError("reference report does not record a clean pass for every motion")
    manifest_status = report.get("manifest")
    if (
        not isinstance(manifest_status, dict)
        or manifest_status.get("id_set_matches") is not True
        or manifest_status.get("artifact_checks_pass") is not True
        or manifest_status.get("missing_from_files") != []
        or manifest_status.get("missing_from_manifest") != []
        or manifest_status.get("artifact_failures") != []
    ):
        raise ValueError("reference report did not pass its manifest/artifact checks")
    result_by_id = {str(result.get("id")): result for result in results}
    if len(result_by_id) != count:
        raise ValueError("reference report has missing or duplicate sequence IDs")
    for sequence in sequences:
        identifier = str(sequence["id"])
        result = result_by_id.get(identifier)
        files = sequence["files"]
        checks = result.get("manifest_checks") if isinstance(result, dict) else None
        if (
            not isinstance(result, dict)
            or result.get("pass") is not True
            or result.get("errors") != []
            or result.get("warnings") != []
            or result.get("file") != files["motion_lib"]
            or result.get("sha256") != files["motion_lib_sha256"]
            or not isinstance(checks, dict)
            or not checks
            or not all(value is True for value in checks.values())
        ):
            raise ValueError(f"reference report is not bound to manifest sequence {identifier}")


def collect_files(project_root: Path) -> list[tuple[Path, str]]:
    mappings = [
        (project_root / "data" / "huggingface-README.md", "README.md"),
        (project_root / "LICENSE", "LICENSE"),
        (project_root / "NOTICE", "NOTICE"),
        (
            project_root / "data" / "manifests" / "shadow-dance-v2.json",
            "manifest/shadow-dance-v2.json",
        ),
        (
            project_root / "results" / "reference-validation-v2.json",
            "validation/reference-validation-v2.json",
        ),
    ]
    for split_path in sorted((project_root / "data" / "splits-v2").glob("*.txt")):
        mappings.append((split_path, f"splits/{split_path.name}"))
    for csv_path in sorted((project_root / "data" / "generated-v2" / "csv").glob("**/*.csv")):
        relative = csv_path.relative_to(project_root / "data" / "generated-v2" / "csv")
        mappings.append((csv_path, f"source_csv/{relative.as_posix()}"))
    for pkl_path in sorted((project_root / "data" / "generated-v2").glob("**/*.pkl")):
        relative = pkl_path.relative_to(project_root / "data" / "generated-v2")
        mappings.append((pkl_path, f"motion_lib/{relative.as_posix()}"))
    return mappings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Publish shadow-dance-v2 after running shadow-generate and shadow-validate"
    )
    parser.add_argument("--repo-id", required=True, help="Hugging Face namespace/repository")
    parser.add_argument("--private", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    subprocess.run(
        [
            sys.executable,
            str(project_root / "scripts" / "verify_dataset_bundle.py"),
            "--profile",
            "dance-v2",
        ],
        cwd=project_root,
        check=True,
    )
    report = json.loads(
        (project_root / "results" / "reference-validation-v2.json").read_text(encoding="utf-8")
    )
    manifest_path = project_root / "data" / "manifests" / "shadow-dance-v2.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    validate_reference_report(report, manifest)
    files = collect_files(project_root)
    missing = [str(path) for path, _ in files if not path.is_file()]
    if missing:
        raise SystemExit(f"Refusing to publish; missing files: {missing}")
    pkl_count = sum(path.suffix == ".pkl" for path, _ in files)
    if pkl_count != report["sequence_count"]:
        raise SystemExit(
            f"Refusing to publish: found {pkl_count} PKLs for {report['sequence_count']} motions"
        )

    targets = [target for _, target in files]
    if len(set(targets)) != len(targets):
        raise ValueError("dataset publication contains duplicate target paths")
    validation_path = project_root / "results" / "reference-validation-v2.json"
    summary = {
        "repo_id": args.repo_id,
        "private": args.private,
        "files": len(files),
        "pkl_files": pkl_count,
        "bytes": sum(path.stat().st_size for path, _ in files),
        "manifest_sha256": sha256(manifest_path),
        "validation_sha256": sha256(validation_path),
        "removed_stale_files": [],
        "commit_url": None,
        "commit_sha": None,
        "dataset_url": None,
    }
    print(json.dumps(summary, indent=2))
    if not args.dry_run:
        api = HfApi()
        api.create_repo(
            repo_id=args.repo_id,
            repo_type="dataset",
            private=args.private,
            exist_ok=True,
        )
        expected_targets = set(targets)
        preserved_targets = {".gitattributes"}
        existing_targets = set(api.list_repo_files(args.repo_id, repo_type="dataset"))
        stale_targets = sorted(existing_targets - expected_targets - preserved_targets)
        summary["removed_stale_files"] = stale_targets
        commit = api.create_commit(
            repo_id=args.repo_id,
            repo_type="dataset",
            operations=[
                *[CommitOperationDelete(path_in_repo=target) for target in stale_targets],
                *[
                    CommitOperationAdd(path_in_repo=target, path_or_fileobj=source)
                    for source, target in files
                ],
            ],
            commit_message="Publish shadow-dance-v2",
            commit_description=(
                f"Frozen SuperSONIC reference dataset: {report['passed']}/"
                f"{report['sequence_count']} motions pass the committed QA report."
            ),
        )
        summary["commit_url"] = commit.commit_url
        summary["commit_sha"] = commit.oid
        summary["dataset_url"] = f"https://huggingface.co/datasets/{args.repo_id}/tree/{commit.oid}"
        print(json.dumps(summary, indent=2))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
