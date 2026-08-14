#!/usr/bin/env python3
"""Publish the frozen dataset files to a Hugging Face dataset repository."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from huggingface_hub import CommitOperationAdd, HfApi


def collect_files(project_root: Path) -> list[tuple[Path, str]]:
    mappings = [
        (project_root / "data" / "huggingface-README.md", "README.md"),
        (project_root / "LICENSE", "LICENSE"),
        (project_root / "NOTICE", "NOTICE"),
        (
            project_root / "data" / "manifests" / "shadow-dip-v1.json",
            "manifest/shadow-dip-v1.json",
        ),
        (
            project_root / "results" / "reference-validation.json",
            "validation/reference-validation.json",
        ),
    ]
    for split_path in sorted((project_root / "data" / "splits").glob("*.txt")):
        mappings.append((split_path, f"splits/{split_path.name}"))
    for csv_path in sorted((project_root / "data" / "generated" / "csv").glob("**/*.csv")):
        relative = csv_path.relative_to(project_root / "data" / "generated" / "csv")
        mappings.append((csv_path, f"source_csv/{relative.as_posix()}"))
    for pkl_path in sorted((project_root / "data" / "generated").glob("**/*.pkl")):
        relative = pkl_path.relative_to(project_root / "data" / "generated")
        mappings.append((pkl_path, f"motion_lib/{relative.as_posix()}"))
    return mappings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Publish shadow-dip-v1 after running shadow-generate and shadow-validate"
    )
    parser.add_argument("--repo-id", required=True, help="Hugging Face namespace/repository")
    parser.add_argument("--private", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    report = json.loads(
        (project_root / "results" / "reference-validation.json").read_text(encoding="utf-8")
    )
    if not report["overall_pass"]:
        raise SystemExit("Refusing to publish: reference validation did not pass")
    files = collect_files(project_root)
    missing = [str(path) for path, _ in files if not path.is_file()]
    if missing:
        raise SystemExit(f"Refusing to publish; missing files: {missing}")
    pkl_count = sum(path.suffix == ".pkl" for path, _ in files)
    if pkl_count != report["sequence_count"]:
        raise SystemExit(
            f"Refusing to publish: found {pkl_count} PKLs for {report['sequence_count']} motions"
        )

    summary = {
        "repo_id": args.repo_id,
        "private": args.private,
        "files": len(files),
        "pkl_files": pkl_count,
        "bytes": sum(path.stat().st_size for path, _ in files),
    }
    print(json.dumps(summary, indent=2))
    if args.dry_run:
        return

    api = HfApi()
    api.create_repo(
        repo_id=args.repo_id,
        repo_type="dataset",
        private=args.private,
        exist_ok=True,
    )
    commit = api.create_commit(
        repo_id=args.repo_id,
        repo_type="dataset",
        operations=[
            CommitOperationAdd(path_in_repo=target, path_or_fileobj=source)
            for source, target in files
        ],
        commit_message="Publish shadow-dip-v1",
        commit_description=(
            "Frozen SuperSONIC reference dataset: 22/22 motions pass the committed QA report."
        ),
    )
    print(commit.commit_url)


if __name__ == "__main__":
    main()
