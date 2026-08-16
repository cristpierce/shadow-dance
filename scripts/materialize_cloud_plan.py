#!/usr/bin/env python3
"""Render and verify the SONIC SkyPilot task without submitting or minting tokens."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

EXPECTED_IMAGE_DIGEST = "sha256:bdf81f5b7f1c879ac920df53588a15129b2ac71d9492e8c2fc34ce636a5373fb"
EXPECTED_REGISTRY_PATTERN = re.compile(r"cr\.eu-north1\.nebius\.cloud/[A-Za-z0-9._-]+")
SECRET_ENV_KEYS = {
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "HF_TOKEN",
    "SKYPILOT_DOCKER_PASSWORD",
    "NPA_REGISTRY_PASSWORD",
}


def required_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a mapping")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workflow", type=Path, default=Path("cloud/sky-shadow-dance.yaml"))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--registry", required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--submission-commit", required=True)
    parser.add_argument("--evidence-s3-uri", required=True)
    parser.add_argument("--hf-model-repo", default="")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-launchable", action="store_true")
    args = parser.parse_args()

    if not re.fullmatch(r"[A-Za-z0-9_.-]+", args.run_id):
        raise ValueError("run ID contains unsupported characters")
    if not re.fullmatch(r"[0-9a-fA-F]{40}", args.submission_commit):
        raise ValueError("submission commit must be a full 40-character Git SHA")
    registry = args.registry.rstrip("/")
    if not EXPECTED_REGISTRY_PATTERN.fullmatch(registry):
        raise ValueError("registry must be an eu-north1 Nebius container registry")
    expected_image = f"{registry}/npa-sonic@{EXPECTED_IMAGE_DIGEST}"
    if args.image != expected_image:
        raise ValueError("policy image must be the configured npa-sonic registry path and digest")
    parsed_s3 = urlparse(args.evidence_s3_uri)
    if parsed_s3.scheme != "s3" or not parsed_s3.netloc:
        raise ValueError("evidence destination must be an s3:// URI")
    if parsed_s3.path.rstrip("/").split("/")[-1] != args.run_id:
        raise ValueError("evidence S3 prefix must end with the run ID")

    try:
        from npa.workbench.sonic.workflow import (
            materialize_sonic_workflow,
            unresolved_submit_placeholders,
        )
    except ImportError as exc:
        raise SystemExit(
            "Run this with the pinned NPA environment; see docs/cloud-runbook.md"
        ) from exc

    eula_values = {
        "OMNI_KIT_ACCEPT_EULA": os.environ.get("OMNI_KIT_ACCEPT_EULA", "NOT_ACCEPTED"),
        "ISAACSIM_ACCEPT_EULA": os.environ.get("ISAACSIM_ACCEPT_EULA", "NOT_ACCEPTED"),
    }
    launchable = all(value == "YES" for value in eula_values.values())
    plan = materialize_sonic_workflow(
        args.workflow,
        run_id=args.run_id,
        registry=registry,
        image=args.image,
        registry_auth=False,
        gpu_target="l40s",
        s3_endpoint="https://storage.eu-north1.nebius.cloud",
        s3_bucket=parsed_s3.netloc,
        s3_prefix=parsed_s3.path.lstrip("/"),
        accelerators="L40S:1",
        cloud="nebius",
        region="eu-north1",
        use_spot=False,
        env_overrides={
            "POLICY_IMAGE": args.image,
            "SUBMISSION_COMMIT": args.submission_commit.lower(),
            "RUN_ID": args.run_id,
            "EVIDENCE_S3_URI": args.evidence_s3_uri.rstrip("/"),
            "HF_MODEL_REPO": args.hf_model_repo,
            **eula_values,
        },
    )
    unresolved = unresolved_submit_placeholders(plan.yaml_text)
    if unresolved:
        raise ValueError(f"materialized plan has unresolved submit tokens: {unresolved}")
    docs = [doc for doc in yaml.safe_load_all(plan.yaml_text) if doc is not None]
    if len(docs) != 1:
        raise ValueError("expected exactly one SkyPilot task document")
    task = required_mapping(docs[0], "task")
    resources = required_mapping(task.get("resources"), "resources")
    envs = required_mapping(task.get("envs"), "envs")
    expected_envs = {
        "POLICY_IMAGE": args.image,
        "SONIC_PAYLOAD_MODE": "direct",
        "SUBMISSION_REPO": "https://github.com/cristpierce/shadow-dance.git",
        "SUBMISSION_COMMIT": args.submission_commit.lower(),
        "RUN_ID": args.run_id,
        "EVIDENCE_S3_URI": args.evidence_s3_uri.rstrip("/"),
        "LADDER": "5,500,4000",
        "STAGE_WALLTIME_BUDGET_SECONDS": "5:900,500:3600,4000:21600",
        "TRAINING_TIMEOUT_SECONDS": "5:600,500:3000,4000:19800",
        "SUBMISSION_DEADLINE_UTC": "2026-08-17T06:59:00Z",
        "FINALIZATION_RESERVE_SECONDS": "7200",
        "PORTAL_RESERVE_SECONDS": "2700",
        "MAX_WALLTIME_SECONDS": "36000",
        "FINAL_TEST_SEEDS": "101,202,303",
        "MAX_WALLTIME": "10h",
        "SMOKE_NUM_ENVS": "64",
        "MAIN_NUM_ENVS": "512",
        "TRAIN_SEED": "42",
        "LEARNING_RATE": "2e-5",
        "REGULAR_SAVE_FREQUENCY": "1000000",
        "SAVE_LAST_FREQUENCY": "5",
        "RENDER_SEED": "303",
        "HF_MODEL_REPO": args.hf_model_repo,
        "HF_DATASET_REPO": "cristpierce/shadow-dip-v1",
        "S3_ENDPOINT_URL": "https://storage.eu-north1.nebius.cloud",
        **eula_values,
    }
    for key, expected in expected_envs.items():
        if envs.get(key) != expected:
            raise ValueError(f"materialized {key} differs from the requested value")
    if task.get("name") != "shadow-dance-supersonic":
        raise ValueError("materialized task name drifted")
    if resources.get("image_id") != f"docker:{args.image}":
        raise ValueError("materialized task does not use the exact direct runtime image")
    expected_resources = {
        "cloud": "nebius",
        "region": "eu-north1",
        "accelerators": "L40S:1",
        "cpus": 16,
        "memory": 64,
        "disk_size": 200,
        "use_spot": False,
    }
    for key, expected in expected_resources.items():
        if resources.get(key) != expected:
            raise ValueError(f"materialized resource {key} differs from {expected!r}")
    setup = task.get("setup")
    run = task.get("run")
    if not isinstance(setup, str) or not isinstance(run, str):
        raise ValueError("materialized setup and run commands must be strings")
    required_setup_fragments = (
        'git checkout --detach "${SUBMISSION_COMMIT}"',
        'test "$(git rev-parse HEAD)" = "${SUBMISSION_COMMIT}"',
        'test "${SONIC_REPO_REF:-}" = 0a87181c9106d0e49293400714b157676e0ec664',
        "scripts/verify_dataset_bundle.py",
    )
    required_run_fragments = (
        "timeout --signal=TERM --kill-after=15m",
        '"${MAX_WALLTIME}"',
        'export RUN_STARTED_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"',
        '"${deadline_remaining_seconds}s"',
        "bash scripts/cloud_pipeline.sh",
    )
    if not all(fragment in setup for fragment in required_setup_fragments):
        raise ValueError("materialized setup lost an immutable-input verification step")
    if not all(fragment in run for fragment in required_run_fragments):
        raise ValueError("materialized run lost the bounded cloud-pipeline invocation")
    leaked_secret_keys = sorted(SECRET_ENV_KEYS.intersection(envs))
    if leaked_secret_keys:
        raise ValueError(f"read-only plan unexpectedly materialized secrets: {leaked_secret_keys}")

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(plan.yaml_text, encoding="utf-8")
    summary = {
        "format": "shadow_dance_cloud_plan_v1",
        "operation": "read_only_materialization",
        "submitted": False,
        "registry_auth_minted": False,
        "run_id": plan.run_id,
        "cloud": plan.cloud,
        "region": plan.region,
        "accelerators": plan.accelerators,
        "policy_image": plan.policy_image,
        "submission_commit": args.submission_commit.lower(),
        "evidence_s3_uri": args.evidence_s3_uri.rstrip("/"),
        "launchable": launchable,
        "launch_blockers": [] if launchable else ["explicit NVIDIA EULA acceptance"],
        "output": str(args.output) if args.output else None,
    }
    print(json.dumps(summary, indent=2))
    if args.require_launchable and not launchable:
        return 78
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
