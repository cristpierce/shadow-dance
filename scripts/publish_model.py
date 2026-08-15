#!/usr/bin/env python3
"""Publish a selected Shadow Dance checkpoint, ONNX graphs, and evidence to HF."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import tempfile
from pathlib import Path
from typing import Any

from aggregate_eval import build_aggregate
from summarize_eval import summarize as summarize_raw_metrics

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SELECTION_SEED = 42
EXPECTED_TEST_SEEDS = (101, 202, 303)
EXPECTED_CANDIDATE_LABELS = {"stage-5", "stage-500", "stage-4000"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_expected_motion_ids() -> dict[str, tuple[str, ...]]:
    manifest = read_json(PROJECT_ROOT / "data" / "manifests" / "shadow-dip-v1.json")
    splits = manifest.get("splits")
    if not isinstance(splits, dict):
        raise ValueError("dataset manifest has no split inventory")
    heldout = tuple(str(value) for value in splits.get("heldout", []))
    test = tuple(str(value) for value in splits.get("test", []))
    retention = tuple(
        str(value) for value in splits.get("train", []) if str(value).startswith("retention_")
    )
    expected = {"heldout": heldout, "retention": retention, "test": test}
    if any(not values or len(set(values)) != len(values) for values in expected.values()):
        raise ValueError("dataset manifest contains an invalid evidence motion inventory")
    return expected


EXPECTED_MOTION_IDS = load_expected_motion_ids()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_summary_against_raw(
    summary: dict[str, Any],
    raw_metrics: Path,
    *,
    expected_label: str,
    expected_split: str,
    expected_seed: int,
) -> None:
    recomputed = summarize_raw_metrics(
        read_json(raw_metrics),
        label=expected_label,
        split=expected_split,
        seed=expected_seed,
    )
    keys = {
        "format",
        "label",
        "split",
        "seed",
        "motion_count",
        "success_count",
        "success_rate",
        "progress_mean",
        "aggregate",
        "motions",
    }
    if any(summary.get(key) != recomputed.get(key) for key in keys):
        raise ValueError(f"evaluation summary differs from recomputed raw metrics: {raw_metrics}")


def compact_single_summary(
    run_root: Path,
    entry: dict[str, Any],
    *,
    expected_label: str,
    expected_split: str,
    expected_seed: int,
) -> tuple[dict[str, float | int], tuple[str, ...]]:
    expected_relative = f"summaries/{expected_label}-{expected_split}-seed-{expected_seed}.json"
    if (
        entry.get("label") != expected_label
        or entry.get("split") != expected_split
        or entry.get("path") != expected_relative
    ):
        raise ValueError(f"invalid selection source entry: {entry}")
    summary_path = (run_root / expected_relative).resolve()
    if summary_path.parent != (run_root / "summaries").resolve():
        raise ValueError("selection source escapes summaries directory")
    if not summary_path.is_file() or entry.get("sha256") != sha256(summary_path):
        raise ValueError(f"selection source hash mismatch: {summary_path}")
    summary = read_json(summary_path)
    if (
        summary.get("format") != "shadow_dance_eval_summary_v1"
        or summary.get("label") != expected_label
        or summary.get("split") != expected_split
        or summary.get("seed") != expected_seed
    ):
        raise ValueError(f"invalid selection summary: {summary_path}")
    motions = summary.get("motions")
    count = int(summary.get("motion_count", 0))
    if not isinstance(motions, list) or count <= 0 or len(motions) != count:
        raise ValueError(f"invalid selection motion inventory: {summary_path}")
    identifiers = tuple(str(row["motion"]) for row in motions)
    if len(set(identifiers)) != len(identifiers):
        raise ValueError(f"duplicate selection motions: {summary_path}")
    if set(identifiers) != set(EXPECTED_MOTION_IDS[expected_split]):
        raise ValueError(
            f"selection motions differ from the committed {expected_split} inventory: "
            f"{summary_path}"
        )
    result: dict[str, float | int] = {
        "motion_count": count,
        "success_count": int(summary["success_count"]),
        "success_rate": float(summary["success_rate"]),
        "mpjpe_l": float(summary["aggregate"]["eval/all/mpjpe_l"]),
    }
    if not 0 <= result["success_count"] <= count:
        raise ValueError(f"invalid selection success count: {summary_path}")
    if not math.isclose(result["success_rate"], result["success_count"] / count, abs_tol=1e-9):
        raise ValueError(f"inconsistent selection success rate: {summary_path}")
    if not math.isfinite(result["mpjpe_l"]) or result["mpjpe_l"] <= 0:
        raise ValueError(f"invalid selection MPJPE: {summary_path}")
    raw_metrics = run_root / "eval" / summary_path.stem / "metrics_eval.json"
    raw_source = summary.get("source")
    if (
        not isinstance(raw_source, dict)
        or not raw_metrics.is_file()
        or raw_source.get("sha256") != sha256(raw_metrics)
    ):
        raise ValueError(f"selection summary is not bound to raw metrics: {summary_path}")
    validate_summary_against_raw(
        summary,
        raw_metrics,
        expected_label=expected_label,
        expected_split=expected_split,
        expected_seed=expected_seed,
    )
    return result, identifiers


def validate_selection_evidence(run_root: Path, selection: dict[str, Any]) -> None:
    seed = selection.get("selection_seed")
    sources = selection.get("sources")
    candidates = selection.get("candidates")
    if seed != EXPECTED_SELECTION_SEED or not isinstance(sources, dict):
        raise ValueError("selection report has no valid seed/source inventory")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("selection report has no candidate inventory")
    candidate_sources = sources.get("candidates")
    if not isinstance(candidate_sources, dict):
        raise ValueError("selection report has no candidate source inventory")

    stock_held, held_ids = compact_single_summary(
        run_root,
        sources.get("stock_heldout", {}),
        expected_label="stock",
        expected_split="heldout",
        expected_seed=seed,
    )
    stock_ret, retention_ids = compact_single_summary(
        run_root,
        sources.get("stock_retention", {}),
        expected_label="stock",
        expected_split="retention",
        expected_seed=seed,
    )
    if (
        selection.get("stock_heldout") != stock_held
        or selection.get("stock_retention") != stock_ret
    ):
        raise ValueError("selection stock metrics differ from their bound summaries")
    expected_thresholds = {
        "max_stock_success": 0.75,
        "min_stock_mpjpe_l": 50.0,
        "min_hero_success_delta": 0.25,
        "min_hero_mpjpe_improvement": 0.10,
        "max_retention_success_drop": 1 / 6,
        "max_retention_mpjpe_increase": 0.15,
    }
    thresholds = selection.get("thresholds")
    if not isinstance(thresholds, dict) or set(thresholds) != set(expected_thresholds):
        raise ValueError("selection report has the wrong threshold inventory")
    for name, expected in expected_thresholds.items():
        if not math.isclose(float(thresholds[name]), expected, abs_tol=1e-12):
            raise ValueError(f"selection threshold drifted: {name}")
    novelty = (
        stock_held["success_rate"] <= expected_thresholds["max_stock_success"]
        or stock_held["mpjpe_l"] >= expected_thresholds["min_stock_mpjpe_l"]
    )
    if selection.get("novelty_gate_pass") is not novelty:
        raise ValueError("selection novelty decision differs from stock metrics")

    labels = {str(candidate.get("label")) for candidate in candidates}
    if labels != EXPECTED_CANDIDATE_LABELS:
        raise ValueError("selection report has the wrong checkpoint-ladder inventory")
    if set(candidate_sources) != labels:
        raise ValueError("selection candidate/source labels differ")
    for candidate in candidates:
        label = str(candidate["label"])
        entries = candidate_sources[label]
        if not isinstance(entries, dict):
            raise ValueError(f"invalid source inventory for candidate {label}")
        held, candidate_held_ids = compact_single_summary(
            run_root,
            entries.get("heldout", {}),
            expected_label=label,
            expected_split="heldout",
            expected_seed=seed,
        )
        retention, candidate_ret_ids = compact_single_summary(
            run_root,
            entries.get("retention", {}),
            expected_label=label,
            expected_split="retention",
            expected_seed=seed,
        )
        if candidate.get("heldout") != held or candidate.get("retention") != retention:
            raise ValueError(f"candidate {label} metrics differ from bound summaries")
        if candidate_held_ids != held_ids or candidate_ret_ids != retention_ids:
            raise ValueError(f"candidate {label} uses different selection motions")
        success_delta = held["success_rate"] - stock_held["success_rate"]
        mpjpe_improvement = 1.0 - held["mpjpe_l"] / stock_held["mpjpe_l"]
        retention_success_delta = retention["success_rate"] - stock_ret["success_rate"]
        retention_mpjpe_increase = retention["mpjpe_l"] / stock_ret["mpjpe_l"] - 1.0
        hero_improved = success_delta >= expected_thresholds["min_hero_success_delta"] or (
            success_delta >= 0.0
            and mpjpe_improvement >= expected_thresholds["min_hero_mpjpe_improvement"]
        )
        retention_ok = (
            retention_success_delta >= -expected_thresholds["max_retention_success_drop"]
            and retention_mpjpe_increase <= expected_thresholds["max_retention_mpjpe_increase"]
        )
        expected_values = {
            "hero_success_delta": success_delta,
            "hero_mpjpe_improvement_fraction": mpjpe_improvement,
            "retention_success_delta": retention_success_delta,
            "retention_mpjpe_increase_fraction": retention_mpjpe_increase,
        }
        for name, expected in expected_values.items():
            if not math.isclose(float(candidate.get(name, math.nan)), expected, abs_tol=1e-12):
                raise ValueError(f"candidate {label} has a forged {name}")
        expected_booleans = {
            "hero_improved": hero_improved,
            "retention_ok": retention_ok,
            "eligible": novelty and hero_improved and retention_ok,
        }
        for name, expected in expected_booleans.items():
            if candidate.get(name) is not expected:
                raise ValueError(f"candidate {label} has a forged {name}")
        checkpoint_hash = candidate.get("checkpoint_sha256")
        if (
            not isinstance(checkpoint_hash, str)
            or len(checkpoint_hash) != 64
            or any(character not in "0123456789abcdef" for character in checkpoint_hash)
            or int(candidate.get("checkpoint_size_bytes", 0)) <= 0
        ):
            raise ValueError(f"candidate {label} has an invalid checkpoint identity")
    selected = selection.get("selected")
    if not isinstance(selected, dict):
        raise ValueError("selection report has no selected candidate")
    matching = [
        candidate for candidate in candidates if candidate.get("label") == selected.get("label")
    ]
    if len(matching) != 1 or matching[0] != selected:
        raise ValueError("selected checkpoint is not identical to its candidate record")
    eligible = [candidate for candidate in candidates if candidate["eligible"]]
    expected_selected = max(
        eligible,
        key=lambda item: (
            item["heldout"]["success_rate"],
            -item["heldout"]["mpjpe_l"],
            item["retention"]["success_rate"],
            -item["retention"]["mpjpe_l"],
        ),
        default=None,
    )
    if expected_selected != selected:
        raise ValueError("selected checkpoint is not the winner under the frozen ranking")


def validate_novelty_evidence(run_root: Path, selection: dict[str, Any]) -> None:
    novelty_path = run_root / "novelty.json"
    novelty = read_json(novelty_path)
    if novelty.get("format") != "shadow_dance_novelty_gate_v1":
        raise ValueError("unsupported or missing novelty gate report")
    seed = selection.get("selection_seed")
    summary_path = run_root / "summaries" / f"stock-heldout-seed-{seed}.json"
    source = novelty.get("source")
    if (
        not isinstance(source, dict)
        or source.get("path") != f"summaries/{summary_path.name}"
        or not summary_path.is_file()
        or source.get("sha256") != sha256(summary_path)
    ):
        raise ValueError("novelty gate is not bound to the stock heldout summary")
    stock = selection.get("stock_heldout", {})
    thresholds = selection.get("thresholds", {})
    success_rate = float(novelty.get("stock_success_rate", -1))
    mpjpe_l = float(novelty.get("stock_mpjpe_l", -1))
    max_success = float(novelty.get("max_stock_success", -1))
    min_mpjpe = float(novelty.get("min_stock_mpjpe_l", -1))
    expected_pass = success_rate <= max_success or mpjpe_l >= min_mpjpe
    if (
        success_rate != float(stock.get("success_rate", -2))
        or mpjpe_l != float(stock.get("mpjpe_l", -2))
        or max_success != float(thresholds.get("max_stock_success", -2))
        or min_mpjpe != float(thresholds.get("min_stock_mpjpe_l", -2))
        or novelty.get("novelty_gate_pass") is not expected_pass
        or not expected_pass
    ):
        raise ValueError("novelty gate metrics or thresholds differ from checkpoint selection")


def compact_test_aggregate(
    path: Path, *, expected_label: str, run_root: Path
) -> tuple[dict[str, float | int], tuple[str, ...], tuple[int, ...]]:
    summary = read_json(path)
    if summary.get("format") != "shadow_dance_eval_aggregate_v1":
        raise ValueError(f"unsupported test aggregate: {path}")
    if summary.get("split") != "test" or summary.get("label") != expected_label:
        raise ValueError(f"wrong split or label in test aggregate: {path}")
    motions = summary.get("motion_inventory")
    count = int(summary.get("motion_count", 0))
    if not isinstance(motions, list) or count <= 0 or len(motions) != count:
        raise ValueError(f"invalid motion inventory in test aggregate: {path}")
    identifiers = tuple(str(motion) for motion in motions)
    if len(set(identifiers)) != len(identifiers):
        raise ValueError(f"duplicate motions in test aggregate: {path}")
    if set(identifiers) != set(EXPECTED_MOTION_IDS["test"]):
        raise ValueError(f"test motions differ from the committed final-test inventory: {path}")
    seeds = summary.get("seeds")
    seed_count = int(summary.get("seed_count", 0))
    if not isinstance(seeds, list) or seed_count < 3 or len(seeds) != seed_count:
        raise ValueError(f"invalid seed inventory in test aggregate: {path}")
    seed_ids = tuple(int(seed) for seed in seeds)
    if len(set(seed_ids)) != len(seed_ids):
        raise ValueError(f"duplicate seeds in test aggregate: {path}")
    if seed_ids != EXPECTED_TEST_SEEDS:
        raise ValueError(f"test aggregate does not use the frozen seed inventory: {path}")
    trial_count = int(summary.get("trial_count", 0))
    result: dict[str, float | int] = {
        "motion_count": count,
        "seed_count": seed_count,
        "trial_count": trial_count,
        "success_count": int(summary["success_count"]),
        "success_rate": float(summary["success_rate"]),
        "mpjpe_l": float(summary["mpjpe_l"]),
    }
    if trial_count != count * seed_count:
        raise ValueError(f"invalid trial count in test aggregate: {path}")
    if not 0 <= result["success_count"] <= trial_count:
        raise ValueError(f"invalid success count in test aggregate: {path}")
    if not math.isclose(
        result["success_rate"], result["success_count"] / trial_count, abs_tol=1e-9
    ):
        raise ValueError(f"inconsistent success rate in test aggregate: {path}")
    if not math.isfinite(result["mpjpe_l"]) or result["mpjpe_l"] <= 0:
        raise ValueError(f"invalid MPJPE in test aggregate: {path}")
    sources = summary.get("sources")
    if not isinstance(sources, list) or len(sources) != seed_count:
        raise ValueError(f"invalid source inventory in test aggregate: {path}")
    observed_source_seeds = []
    source_paths: list[Path] = []
    source_payloads: list[dict[str, Any]] = []
    for entry in sources:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise ValueError(f"invalid source entry in test aggregate: {path}")
        source_path = (run_root / entry["path"]).resolve()
        if source_path.parent != (run_root / "summaries").resolve():
            raise ValueError(f"test aggregate source escapes summaries directory: {path}")
        if not source_path.is_file() or entry.get("sha256") != sha256(source_path):
            raise ValueError(f"test aggregate source hash mismatch: {source_path}")
        source_summary = read_json(source_path)
        if (
            source_summary.get("format") != "shadow_dance_eval_summary_v1"
            or source_summary.get("split") != "test"
            or source_summary.get("label") != expected_label
        ):
            raise ValueError(f"invalid source summary in test aggregate: {source_path}")
        source_ids = tuple(str(row["motion"]) for row in source_summary.get("motions", []))
        if source_ids != identifiers:
            raise ValueError(f"source summary motion inventory drifted: {source_path}")
        observed_source_seeds.append(int(source_summary["seed"]))
        raw_metrics = run_root / "eval" / source_path.stem / "metrics_eval.json"
        raw_source = source_summary.get("source")
        if (
            not isinstance(raw_source, dict)
            or not raw_metrics.is_file()
            or raw_source.get("sha256") != sha256(raw_metrics)
        ):
            raise ValueError(f"source summary is not bound to raw metrics: {source_path}")
        validate_summary_against_raw(
            source_summary,
            raw_metrics,
            expected_label=expected_label,
            expected_split="test",
            expected_seed=int(source_summary["seed"]),
        )
        source_paths.append(source_path)
        source_payloads.append(source_summary)
    if tuple(observed_source_seeds) != seed_ids:
        raise ValueError(f"source-summary seeds differ from test aggregate: {path}")
    recomputed_aggregate = build_aggregate(
        source_payloads,
        source_paths,
        label=expected_label,
        split="test",
    )
    if summary != recomputed_aggregate:
        raise ValueError(f"test aggregate differs from its recomputed source summaries: {path}")
    return result, identifiers, seed_ids


def verify_release_hashes(release: Path) -> None:
    manifest = release / "SHA256SUMS"
    expected_files = {
        path.name for path in release.iterdir() if path.is_file() and path != manifest
    }
    observed: set[str] = set()
    for line in manifest.read_text(encoding="utf-8").splitlines():
        digest, separator, raw_name = line.partition(" ")
        name = raw_name.strip().removeprefix("*").removeprefix("./")
        if not separator or len(digest) != 64 or not name:
            raise ValueError(f"invalid SHA256SUMS line: {line!r}")
        path = (release / name).resolve()
        if path.parent != release.resolve() or not path.is_file():
            raise ValueError(f"SHA256SUMS references an invalid file: {name!r}")
        if sha256(path) != digest.lower():
            raise ValueError(f"SHA-256 mismatch for release file: {name}")
        observed.add(name)
    if observed != expected_files:
        missing = sorted(expected_files - observed)
        extra = sorted(observed - expected_files)
        raise ValueError(f"SHA256SUMS inventory mismatch: missing={missing}, extra={extra}")


def validate_video_evidence(
    run_root: Path,
    comparison: dict[str, Any],
    *,
    motion_ids: tuple[str, ...],
    test_seeds: tuple[int, ...],
) -> None:
    media_root = (run_root / "media").resolve()
    manifest_path = media_root / "video-manifest.json"
    if not manifest_path.is_file():
        raise ValueError("release has no video evidence manifest")
    manifest = read_json(manifest_path)
    if manifest.get("format") != "shadow_dance_video_manifest_v1":
        raise ValueError("unsupported video evidence manifest")
    if (
        manifest.get("edited_comparison") is not True
        or manifest.get("reference_is_policy_output") is not False
        or manifest.get("source_policy_runs_uncut") is not True
    ):
        raise ValueError("video evidence does not preserve the target/source disclosure contract")
    if manifest.get("selected_label") != comparison.get("selected_label"):
        raise ValueError("video evidence checkpoint label differs from final comparison")
    render_seed = manifest.get("render_seed")
    if not isinstance(render_seed, int) or render_seed not in test_seeds:
        raise ValueError("video display seed is not in the final-test seed inventory")
    comparison_entry = manifest.get("final_comparison")
    if (
        not isinstance(comparison_entry, dict)
        or comparison_entry.get("path") != "final-comparison.json"
        or comparison_entry.get("sha256") != sha256(run_root / "final-comparison.json")
    ):
        raise ValueError("video evidence is not bound to the final comparison")

    def checked_media(entry: Any, *, label: str) -> Path:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise ValueError(f"invalid {label} video entry")
        path = (media_root / entry["path"]).resolve()
        if not path.is_relative_to(media_root) or not path.is_file():
            raise ValueError(f"{label} video path escapes media or is missing")
        if entry.get("bytes") != path.stat().st_size or entry.get("sha256") != sha256(path):
            raise ValueError(f"{label} video identity mismatch: {path.name}")
        if float(entry.get("fps", 0)) <= 0 or float(entry.get("duration_seconds", 0)) <= 0:
            raise ValueError(f"{label} video metadata is invalid: {path.name}")
        return path

    checked_media(manifest.get("reference"), label="reference")
    output = checked_media(manifest.get("output"), label="edited output")
    if output.name != "hero-before-after.mp4":
        raise ValueError("video evidence output has the wrong name")
    output_entry = manifest["output"]
    if int(output_entry.get("frame_count", 0)) <= 0:
        raise ValueError("video evidence output has no frames")

    inventories: dict[str, list[Path]] = {}
    for label in ("stock", "selected"):
        entries = manifest.get(label)
        if not isinstance(entries, list) or len(entries) != len(motion_ids):
            raise ValueError(f"video evidence has the wrong {label} clip count")
        if tuple(str(entry.get("motion")) for entry in entries) != motion_ids:
            raise ValueError(f"video evidence has the wrong {label} motion mapping")
        inventories[label] = [checked_media(entry, label=f"{label} source") for entry in entries]
    stock_names = [path.name for path in inventories["stock"]]
    selected_names = [path.name for path in inventories["selected"]]
    if stock_names != selected_names or len(set(stock_names)) != len(stock_names):
        raise ValueError("stock and selected video source inventories are not exactly paired")
    if comparison.get("stock", {}).get("motion_count") != len(stock_names):
        raise ValueError("video evidence motion count differs from final comparison")


def render_model_card(
    selection: dict[str, Any], comparison: dict[str, Any], dataset_repo: str
) -> str:
    selected = selection.get("selected")
    if not isinstance(selected, dict) or not selected.get("eligible"):
        raise ValueError("selection report has no eligible selected checkpoint")
    if comparison.get("format") != "shadow_dance_final_comparison_v1":
        raise ValueError("unsupported final comparison report")
    if comparison.get("split") != "test":
        raise ValueError("final comparison is not the test split")
    if comparison.get("used_for_checkpoint_selection") is not False:
        raise ValueError("final comparison does not prove an untouched test split")
    if comparison.get("selected_label") != selected.get("label"):
        raise ValueError("final comparison does not match the selected checkpoint")
    stock = comparison["stock"]
    adapted = comparison["selected"]
    stock_retention = selection["stock_retention"]
    adapted_retention = selected["retention"]
    stock_row = (
        f"| Stock SONIC | {stock['success_count']}/{stock['trial_count']} | "
        f"{stock['success_rate']:.1%} | {stock['mpjpe_l']:.3f} |"
    )
    adapted_row = (
        f"| Shadow Dance ({selected['label']}) | "
        f"{adapted['success_count']}/{adapted['trial_count']} | "
        f"{adapted['success_rate']:.1%} | {adapted['mpjpe_l']:.3f} |"
    )
    return f"""---
license: other
license_name: nvidia-open-model-license
tags:
- robotics
- humanoid
- unitree-g1
- reinforcement-learning
- onnx
datasets:
- {dataset_repo}
---

# Shadow Dance SONIC policy

This is Team SELTZER's simulation-validated Unitree G1 policy for the SuperSONIC
"Shadow Partner Dip." It is a fine-tuned derivative of NVIDIA GEAR-SONIC's
`sonic_release/last.pt`, not an official NVIDIA model.

## Untouched final-test result

| Policy | Completed trials | Success | Local MPJPE macro mean (mm) |
|---|---:|---:|---:|
{stock_row}
{adapted_row}

Retention success changed from {stock_retention["success_rate"]:.1%} to
{adapted_retention["success_rate"]:.1%}; retention local MPJPE changed from
{stock_retention["mpjpe_l"]:.3f} to {adapted_retention["mpjpe_l"]:.3f} mm.
The {stock["motion_count"]} final-test motions were first evaluated across
{stock["seed_count"]} independent simulator seeds only after checkpoint selection.
Selection itself used separate held-out validation plus the preregistered novelty,
improvement, and retention gates in `selection.json`; `final-comparison.json` binds the
test summaries to that already-selected checkpoint.

## Files and use

- `last.pt` and exported `.onnx` graphs are model weights; the graph ending in
  `_g1.onnx` is the deployable G1 portal nominee.
- `config.yaml`, `novelty.json`, `selection.json`, `final-comparison.json`,
  `onnx-report.json`, and `SHA256SUMS` preserve the training/evaluation contract and
  artifact identities.
- `training/` contains the stage logs and resolved text configs (intermediate weights
  are intentionally omitted). `evaluation/` contains compact frozen-split summaries.
  `media/` contains every matched uncut simulator source run,
  `hero-before-after.mp4`, and their hash manifest.
- Dataset: https://huggingface.co/datasets/{dataset_repo}
- Source: https://github.com/Durp06/shadow-dance

## Reproducibility identity

- Base: `nvidia/GEAR-SONIC@9c0ff22b4ffec27c5392e8e284eb2f2df7a5b4e2`
- Base checkpoint SHA-256:
  `e6bdab3f64a39336b3d41877d4f497d05f58af275f288ec0e6746c283ded8909`
- Selected checkpoint SHA-256: `{selected["checkpoint_sha256"]}`
- Runtime SONIC commit: `0a87181c9106d0e49293400714b157676e0ec664`
- L40S image digest:
  `sha256:bdf81f5b7f1c879ac920df53588a15129b2ac71d9492e8c2fc34ce636a5373fb`

The ONNX report records graph checking, ONNX Runtime loading, I/O names and shapes, and
a finite inference probe for every graph, substituting dimension 1 for dynamic input
axes. Validate the expected robot observation/action contract before deployment.

## License and safety

Code and team-authored motion data are Apache-2.0. The checkpoint and ONNX derivatives
remain under the NVIDIA Open Model License; the full upstream dual-license text is
included as `GEAR-SONIC-DUAL-LICENSE`. Licensed by NVIDIA Corporation under the NVIDIA
Open Model License.

Simulation only. No real-robot execution is claimed. A physical G1 deployment requires
vendor limits, an operator emergency stop, a clear fall zone, and independent safety
validation.

Challenge acknowledgement requested by the Ultimate Bots portal: **Motion Data by
Bones Studio.** No BONES-SEED motion or derived data is included in this release.
"""


def collect_files(run_root: Path, card: Path) -> list[tuple[Path, str]]:
    release_dir = run_root / "release" / "model"
    mappings: list[tuple[Path, str]] = [(card, "README.md")]
    mappings.extend((path, path.name) for path in sorted(release_dir.iterdir()) if path.is_file())
    summary_dir = run_root / "summaries"
    if summary_dir.is_dir():
        mappings.extend(
            (path, f"evaluation/{path.name}") for path in sorted(summary_dir.glob("*.json"))
        )
    eval_dir = run_root / "eval"
    if eval_dir.is_dir():
        mappings.extend(
            (path, f"raw-evaluation/{path.relative_to(eval_dir).as_posix()}")
            for path in sorted(eval_dir.rglob("*"))
            if path.is_file()
            and (path.name in {"metrics_eval.json", "eval.log"} or ".hydra" in path.parts)
        )
    train_dir = run_root / "train"
    if train_dir.is_dir():
        mappings.extend(
            (path, f"training/{path.relative_to(train_dir).as_posix()}")
            for path in sorted(train_dir.rglob("*"))
            if path.is_file() and path.suffix.lower() in {".log", ".yaml", ".yml", ".txt"}
        )
    for name in ("environment.txt", "base-model.sha256"):
        path = run_root / name
        if path.is_file():
            mappings.append((path, f"evidence/{name}"))
    media_dir = run_root / "media"
    if media_dir.is_dir():
        mappings.extend(
            (path, f"media/{path.relative_to(media_dir).as_posix()}")
            for path in sorted(media_dir.rglob("*"))
            if path.is_file()
        )
    return mappings


def validate_run(run_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    selection = read_json(run_root / "selection.json")
    if selection.get("format") != "shadow_dance_checkpoint_selection_v1":
        raise ValueError("unsupported or missing checkpoint selection report")
    if not selection.get("selected", {}).get("eligible"):
        raise ValueError("refusing to publish without an eligible selected checkpoint")
    validate_selection_evidence(run_root, selection)
    validate_novelty_evidence(run_root, selection)
    comparison = read_json(run_root / "final-comparison.json")
    if comparison.get("format") != "shadow_dance_final_comparison_v1":
        raise ValueError("unsupported or missing final comparison report")
    if comparison.get("split") != "test":
        raise ValueError("final comparison is not the test split")
    if comparison.get("used_for_checkpoint_selection") is not False:
        raise ValueError("final comparison was not marked as untouched test evidence")
    if comparison.get("selected_label") != selection["selected"].get("label"):
        raise ValueError("final comparison selected label does not match selection")
    if comparison.get("selection_report_sha256") != sha256(run_root / "selection.json"):
        raise ValueError("final comparison is not bound to this selection report")
    expected_sources = {
        "stock_summary": run_root / "summaries" / "stock-test-aggregate.json",
        "selected_summary": (
            run_root / "summaries" / f"{selection['selected']['label']}-test-aggregate.json"
        ),
    }
    sources = comparison.get("sources")
    if not isinstance(sources, dict):
        raise ValueError("final comparison has no source-summary inventory")
    for source_name, source_path in expected_sources.items():
        entry = sources.get(source_name)
        expected_relative = source_path.relative_to(run_root).as_posix()
        if not isinstance(entry, dict) or entry.get("path") != expected_relative:
            raise ValueError(f"final comparison has an invalid {source_name} path")
        if not source_path.is_file() or entry.get("sha256") != sha256(source_path):
            raise ValueError(f"final comparison does not match {source_name}")
    stock_compact, stock_ids, stock_seeds = compact_test_aggregate(
        expected_sources["stock_summary"], expected_label="stock", run_root=run_root
    )
    selected_compact, selected_ids, selected_seeds = compact_test_aggregate(
        expected_sources["selected_summary"],
        expected_label=selection["selected"]["label"],
        run_root=run_root,
    )
    if stock_ids != selected_ids:
        raise ValueError("published test summaries use different motion inventories")
    if stock_seeds != selected_seeds:
        raise ValueError("published test summaries use different seed inventories")
    inventory_hash = hashlib.sha256(
        json.dumps(stock_ids, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if comparison.get("motion_inventory_sha256") != inventory_hash:
        raise ValueError("final comparison has the wrong test motion inventory hash")
    seed_inventory_hash = hashlib.sha256(
        json.dumps(stock_seeds, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if comparison.get("seed_inventory_sha256") != seed_inventory_hash:
        raise ValueError("final comparison has the wrong test seed inventory hash")
    if comparison.get("stock") != stock_compact or comparison.get("selected") != selected_compact:
        raise ValueError("final comparison metrics differ from the bound test summaries")
    expected_success_delta = selected_compact["success_rate"] - stock_compact["success_rate"]
    expected_mpjpe_improvement = 1.0 - selected_compact["mpjpe_l"] / stock_compact["mpjpe_l"]
    if not math.isclose(
        float(comparison.get("success_rate_delta", math.nan)),
        expected_success_delta,
        abs_tol=1e-12,
    ) or not math.isclose(
        float(comparison.get("mpjpe_l_improvement_fraction", math.nan)),
        expected_mpjpe_improvement,
        abs_tol=1e-12,
    ):
        raise ValueError("final comparison deltas differ from the bound test summaries")
    validate_video_evidence(
        run_root,
        comparison,
        motion_ids=stock_ids,
        test_seeds=stock_seeds,
    )
    onnx_report = read_json(run_root / "onnx-report.json")
    if onnx_report.get("format") != "shadow_dance_onnx_validation_v1" or not onnx_report.get(
        "overall_pass"
    ):
        raise ValueError("refusing to publish because ONNX validation did not pass")
    release = run_root / "release" / "model"
    required = [
        release / "last.pt",
        release / "config.yaml",
        release / "novelty.json",
        release / "selection.json",
        release / "final-comparison.json",
        release / "onnx-report.json",
        release / "GEAR-SONIC-DUAL-LICENSE",
        release / "SHA256SUMS",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    release_onnx = {path.name: path for path in release.glob("*.onnx")}
    artifacts = onnx_report.get("artifacts")
    if not isinstance(artifacts, list) or len(artifacts) != 5:
        missing.append(str(release / "<exact-five-graph-sonic-bundle>"))
    if missing:
        raise ValueError(f"release is incomplete: {missing}")
    reported_onnx = {str(item.get("file")): item for item in artifacts}
    if set(reported_onnx) != set(release_onnx):
        raise ValueError("ONNX report and release graph inventories differ")
    nominee = onnx_report.get("portal_nominee")
    if nominee not in release_onnx or not str(nominee).endswith("_g1.onnx"):
        raise ValueError("ONNX report has no valid G1 portal nominee")
    for name, path in release_onnx.items():
        artifact = reported_onnx[name]
        if (
            artifact.get("bytes") != path.stat().st_size
            or artifact.get("sha256") != sha256(path)
            or artifact.get("checker_pass") is not True
            or artifact.get("inference", {}).get("passed") is not True
        ):
            raise ValueError(f"released ONNX graph differs from its validation: {name}")
    selected = selection["selected"]
    if selected.get("checkpoint_size_bytes") != (
        release / "last.pt"
    ).stat().st_size or selected.get("checkpoint_sha256") != sha256(release / "last.pt"):
        raise ValueError("released checkpoint does not match the selected checkpoint identity")
    for name in ("novelty.json", "selection.json", "final-comparison.json", "onnx-report.json"):
        if sha256(release / name) != sha256(run_root / name):
            raise ValueError(f"release copy differs from run evidence: {name}")
    verify_release_hashes(release)
    return selection, comparison


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--repo-id", required=True)
    parser.add_argument("--dataset-repo", default="cristpierce/shadow-dip-v1")
    parser.add_argument("--private", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    run_root = args.run_root.resolve()
    selection, comparison = validate_run(run_root)
    nominee = str(read_json(run_root / "onnx-report.json")["portal_nominee"])
    with tempfile.TemporaryDirectory(prefix="shadow-dance-model-card-") as temp:
        card = Path(temp) / "README.md"
        card.write_text(
            render_model_card(selection, comparison, args.dataset_repo), encoding="utf-8"
        )
        files = collect_files(run_root, card)
        targets = [target for _, target in files]
        if len(set(targets)) != len(targets):
            raise ValueError("model publication contains duplicate target paths")
        summary: dict[str, Any] = {
            "repo_id": args.repo_id,
            "private": args.private,
            "files": len(files),
            "bytes": sum(path.stat().st_size for path, _ in files),
            "selected_label": selection["selected"]["label"],
            "portal_nominee": nominee,
            "removed_stale_files": [],
            "commit_url": None,
            "commit_sha": None,
            "model_url": None,
            "onnx_url": None,
            "video_url": None,
            "results_url": None,
        }
        print(json.dumps(summary, indent=2))
        if not args.dry_run:
            from huggingface_hub import CommitOperationAdd, CommitOperationDelete, HfApi

            api = HfApi()
            api.create_repo(
                repo_id=args.repo_id,
                repo_type="model",
                private=args.private,
                exist_ok=True,
            )
            expected_targets = set(targets)
            preserved_targets = {".gitattributes"}
            existing_targets = set(api.list_repo_files(args.repo_id, repo_type="model"))
            stale_targets = sorted(existing_targets - expected_targets - preserved_targets)
            summary["removed_stale_files"] = stale_targets
            commit = api.create_commit(
                repo_id=args.repo_id,
                repo_type="model",
                operations=[
                    *[CommitOperationDelete(path_in_repo=target) for target in stale_targets],
                    *[
                        CommitOperationAdd(path_in_repo=target, path_or_fileobj=source)
                        for source, target in files
                    ],
                ],
                commit_message="Publish selected Shadow Dance SONIC policy",
                commit_description=(
                    "Selected on frozen validation/retention gates and reported on an "
                    "untouched final test split."
                ),
            )
            summary["commit_url"] = commit.commit_url
            summary["commit_sha"] = commit.oid
            resolve_root = f"https://huggingface.co/{args.repo_id}/resolve/{commit.oid}"
            summary["model_url"] = f"https://huggingface.co/{args.repo_id}/tree/{commit.oid}"
            summary["onnx_url"] = f"{resolve_root}/{nominee}"
            summary["video_url"] = f"{resolve_root}/media/hero-before-after.mp4"
            summary["results_url"] = (
                f"https://huggingface.co/{args.repo_id}/blob/{commit.oid}/final-comparison.json"
            )
            print(json.dumps(summary, indent=2))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
