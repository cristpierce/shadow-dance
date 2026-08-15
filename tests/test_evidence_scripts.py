from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
MOTIONS = {
    "heldout": [
        "shadow_dip_left_heldout_19",
        "shadow_dip_right_heldout_20",
        "shadow_dip_left_heldout_21",
        "shadow_dip_right_heldout_22",
    ],
    "retention": [
        "retention_stand_left",
        "retention_squat_left",
        "retention_sway_left",
        "retention_sway_right",
        "retention_torso_turn_left",
        "retention_torso_turn_right",
        "retention_walk_left",
        "retention_walk_right",
        "retention_turn_left",
        "retention_turn_right",
    ],
    "test": [
        "shadow_dip_left_test_23",
        "shadow_dip_right_test_24",
        "shadow_dip_left_test_25",
        "shadow_dip_right_test_26",
    ],
}


def metric_payload(*, terminations: list[bool], mpjpe_l: float) -> dict:
    count = len(terminations)
    success_rate = 1.0 - sum(terminations) / count
    return {
        "eval/success/success_rate": success_rate,
        "eval/all/mpjpe_l": mpjpe_l,
        "eval/all/mpjpe_g": mpjpe_l * 2,
        "eval/all_metrics_dict": {
            "motion_keys": [f"motion_{index}" for index in range(count)],
            "terminated": terminations,
            "progress": [0.5 if failed else 1.0 for failed in terminations],
            "mpjpe_l": [mpjpe_l + index for index in range(count)],
        },
    }


def write_summary(
    tmp_path: Path,
    name: str,
    split: str,
    payload: dict,
    *,
    label: str | None = None,
    seed: int = 42,
) -> Path:
    payload = json.loads(json.dumps(payload))
    payload["eval/all_metrics_dict"]["motion_keys"] = MOTIONS[split]
    raw = tmp_path / f"{name}-raw.json"
    summary = tmp_path / f"{name}.json"
    raw.write_text(json.dumps(payload), encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "summarize_eval.py"),
            str(raw),
            "--label",
            label or name,
            "--split",
            split,
            "--seed",
            str(seed),
            "--output",
            str(summary),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return summary


def aggregate_summaries(output: Path, *, label: str, split: str, summaries: list[Path]) -> Path:
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "aggregate_eval.py"),
            *map(str, summaries),
            "--label",
            label,
            "--split",
            split,
            "--output",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return output


def test_eval_summary_and_checkpoint_selection(tmp_path: Path) -> None:
    stock_held = write_summary(
        tmp_path,
        "stock-heldout",
        "heldout",
        metric_payload(terminations=[True] * 4, mpjpe_l=80),
        label="stock",
    )
    stock_ret = write_summary(
        tmp_path,
        "stock-retention",
        "retention",
        metric_payload(terminations=[False] * 10, mpjpe_l=20),
        label="stock",
    )
    tuned_held = write_summary(
        tmp_path,
        "tuned-heldout",
        "heldout",
        metric_payload(terminations=[False] * 4, mpjpe_l=28),
        label="stage-500",
    )
    tuned_ret = write_summary(
        tmp_path,
        "tuned-retention",
        "retention",
        metric_payload(terminations=[False] * 10, mpjpe_l=21),
        label="stage-500",
    )
    novelty = tmp_path / "novelty.json"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "check_novelty.py"),
            str(stock_held),
            "--output",
            str(novelty),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(novelty.read_text(encoding="utf-8"))["novelty_gate_pass"]
    candidate_checkpoint = tmp_path / "stage-500-last.pt"
    candidate_checkpoint.write_bytes(b"candidate-checkpoint")
    output = tmp_path / "selection.json"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "select_checkpoint.py"),
            "--stock-heldout",
            str(stock_held),
            "--stock-retention",
            str(stock_ret),
            "--candidate",
            "stage-500",
            str(candidate_checkpoint),
            str(tuned_held),
            str(tuned_ret),
            "--output",
            str(output),
            "--require-eligible",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["novelty_gate_pass"]
    assert report["selected"]["label"] == "stage-500"
    assert (
        report["selected"]["checkpoint_sha256"]
        == hashlib.sha256(candidate_checkpoint.read_bytes()).hexdigest()
    )

    test_seeds = [101, 202, 303]
    stock_test_runs = [
        write_summary(
            tmp_path,
            f"stock-test-seed-{seed}",
            "test",
            metric_payload(terminations=[True] * 4, mpjpe_l=84),
            label="stock",
            seed=seed,
        )
        for seed in test_seeds
    ]
    tuned_test_runs = [
        write_summary(
            tmp_path,
            f"stage-500-test-seed-{seed}",
            "test",
            metric_payload(terminations=[False] * 4, mpjpe_l=30),
            label="stage-500",
            seed=seed,
        )
        for seed in test_seeds
    ]
    stock_test = aggregate_summaries(
        tmp_path / "stock-test-aggregate.json",
        label="stock",
        split="test",
        summaries=stock_test_runs,
    )
    tuned_test = aggregate_summaries(
        tmp_path / "stage-500-test-aggregate.json",
        label="stage-500",
        split="test",
        summaries=tuned_test_runs,
    )
    comparison = tmp_path / "final-comparison.json"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_final_comparison.py"),
            "--selection",
            str(output),
            "--stock-test",
            str(stock_test),
            "--selected-test",
            str(tuned_test),
            "--output",
            str(comparison),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    final_report = json.loads(comparison.read_text(encoding="utf-8"))
    assert final_report["used_for_checkpoint_selection"] is False
    assert final_report["selected_label"] == "stage-500"
    assert final_report["stock"]["trial_count"] == 12

    mismatched = json.loads(tuned_test.read_text(encoding="utf-8"))
    mismatched["motion_inventory"][0] = "different_test_motion"
    tuned_test.write_text(json.dumps(mismatched), encoding="utf-8")
    rejected = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_final_comparison.py"),
            "--selection",
            str(output),
            "--stock-test",
            str(stock_test),
            "--selected-test",
            str(tuned_test),
            "--output",
            str(comparison),
        ],
        capture_output=True,
        text=True,
    )
    assert rejected.returncode != 0
    assert "different motion inventories" in rejected.stderr


def test_committed_dataset_bundle_matches_manifest() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verify_dataset_bundle.py")],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def test_publisher_recomputes_summary_from_raw_metrics(tmp_path: Path) -> None:
    summary = write_summary(
        tmp_path,
        "stock-heldout-seed-42",
        "heldout",
        metric_payload(terminations=[True] * 4, mpjpe_l=80),
        label="stock",
    )
    forged = json.loads(summary.read_text(encoding="utf-8"))
    forged["motions"][0]["progress"] = 0.75
    summary.write_text(json.dumps(forged), encoding="utf-8")
    raw = tmp_path / "stock-heldout-seed-42-raw.json"
    script_dir = ROOT / "scripts"
    code = (
        "import json,sys,pathlib; "
        f"sys.path.insert(0, {str(script_dir)!r}); "
        "from publish_model import validate_summary_against_raw; "
        f"summary=json.loads(pathlib.Path({str(summary)!r}).read_text()); "
        f"validate_summary_against_raw(summary, pathlib.Path({str(raw)!r}), "
        "expected_label='stock', expected_split='heldout', expected_seed=42)"
    )
    rejected = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
    )
    assert rejected.returncode != 0
    assert "differs from recomputed raw metrics" in rejected.stderr


def test_model_publisher_dry_run_requires_valid_release(tmp_path: Path) -> None:
    release = tmp_path / "release" / "model"
    release.mkdir(parents=True)
    for name, content in {
        "last.pt": b"checkpoint",
        "config.yaml": b"config: test\n",
        "GEAR-SONIC-DUAL-LICENSE": b"license",
        "model_step_000500_smpl.onnx": b"smpl-onnx",
        "model_step_000500_g1.onnx": b"g1-onnx",
        "model_step_000500_teleop.onnx": b"teleop-onnx",
        "model_step_000500_encoder.onnx": b"encoder-onnx",
        "model_step_000500_decoder.onnx": b"decoder-onnx",
    }.items():
        (release / name).write_bytes(content)
    summaries = tmp_path / "summaries"
    summaries.mkdir()

    def bound_summary(name: str, label: str, split: str, payload: dict, *, seed: int = 42) -> Path:
        summary = write_summary(summaries, name, split, payload, label=label, seed=seed)
        raw_fixture = summaries / f"{name}-raw.json"
        raw_metrics = tmp_path / "eval" / name / "metrics_eval.json"
        raw_metrics.parent.mkdir(parents=True)
        raw_metrics.write_bytes(raw_fixture.read_bytes())
        return summary

    stock_heldout_summary = bound_summary(
        "stock-heldout-seed-42",
        "stock",
        "heldout",
        metric_payload(terminations=[True] * 4, mpjpe_l=80),
    )
    stock_retention_summary = bound_summary(
        "stock-retention-seed-42",
        "stock",
        "retention",
        metric_payload(terminations=[False] * 10, mpjpe_l=20),
    )
    selected_heldout_summary = bound_summary(
        "stage-500-heldout-seed-42",
        "stage-500",
        "heldout",
        metric_payload(terminations=[False] * 4, mpjpe_l=28),
    )
    selected_retention_summary = bound_summary(
        "stage-500-retention-seed-42",
        "stage-500",
        "retention",
        metric_payload(terminations=[False] * 10, mpjpe_l=21),
    )
    stage_5_heldout_summary = bound_summary(
        "stage-5-heldout-seed-42",
        "stage-5",
        "heldout",
        metric_payload(terminations=[True] * 4, mpjpe_l=79),
    )
    stage_5_retention_summary = bound_summary(
        "stage-5-retention-seed-42",
        "stage-5",
        "retention",
        metric_payload(terminations=[False] * 10, mpjpe_l=20),
    )
    stage_4000_heldout_summary = bound_summary(
        "stage-4000-heldout-seed-42",
        "stage-4000",
        "heldout",
        metric_payload(terminations=[False, True, True, True], mpjpe_l=70),
    )
    stage_4000_retention_summary = bound_summary(
        "stage-4000-retention-seed-42",
        "stage-4000",
        "retention",
        metric_payload(terminations=[False] * 8 + [True] * 2, mpjpe_l=25),
    )

    def candidate_record(
        label: str,
        *,
        checkpoint_bytes: bytes,
        heldout_successes: int,
        heldout_mpjpe: float,
        retention_successes: int,
        retention_mpjpe: float,
    ) -> dict:
        heldout_rate = heldout_successes / 4
        retention_rate = retention_successes / 10
        success_delta = heldout_rate
        mpjpe_improvement = 1.0 - heldout_mpjpe / 80.0
        retention_success_delta = retention_rate - 1.0
        retention_mpjpe_increase = retention_mpjpe / 20.0 - 1.0
        hero_improved = success_delta >= 0.25 or (
            success_delta >= 0.0 and mpjpe_improvement >= 0.10
        )
        retention_ok = retention_success_delta >= -(1 / 6) and retention_mpjpe_increase <= 0.15
        return {
            "label": label,
            "checkpoint": f"/cloud/checkpoints/{label}/last.pt",
            "checkpoint_size_bytes": len(checkpoint_bytes),
            "checkpoint_sha256": hashlib.sha256(checkpoint_bytes).hexdigest(),
            "heldout": {
                "motion_count": 4,
                "success_count": heldout_successes,
                "success_rate": heldout_rate,
                "mpjpe_l": heldout_mpjpe,
            },
            "retention": {
                "motion_count": 10,
                "success_count": retention_successes,
                "success_rate": retention_rate,
                "mpjpe_l": retention_mpjpe,
            },
            "hero_success_delta": success_delta,
            "hero_mpjpe_improvement_fraction": mpjpe_improvement,
            "retention_success_delta": retention_success_delta,
            "retention_mpjpe_increase_fraction": retention_mpjpe_increase,
            "hero_improved": hero_improved,
            "retention_ok": retention_ok,
            "eligible": hero_improved and retention_ok,
        }

    stage_5_candidate = candidate_record(
        "stage-5",
        checkpoint_bytes=b"stage-5-checkpoint",
        heldout_successes=0,
        heldout_mpjpe=79.0,
        retention_successes=10,
        retention_mpjpe=20.0,
    )
    candidate = candidate_record(
        "stage-500",
        checkpoint_bytes=(release / "last.pt").read_bytes(),
        heldout_successes=4,
        heldout_mpjpe=28.0,
        retention_successes=10,
        retention_mpjpe=21.0,
    )
    stage_4000_candidate = candidate_record(
        "stage-4000",
        checkpoint_bytes=b"stage-4000-checkpoint",
        heldout_successes=1,
        heldout_mpjpe=70.0,
        retention_successes=8,
        retention_mpjpe=25.0,
    )
    selection = {
        "format": "shadow_dance_checkpoint_selection_v1",
        "thresholds": {
            "max_stock_success": 0.75,
            "min_stock_mpjpe_l": 50.0,
            "min_hero_success_delta": 0.25,
            "min_hero_mpjpe_improvement": 0.10,
            "max_retention_success_drop": 1 / 6,
            "max_retention_mpjpe_increase": 0.15,
        },
        "stock_heldout": {
            "motion_count": 4,
            "success_count": 0,
            "success_rate": 0.0,
            "mpjpe_l": 80.0,
        },
        "stock_retention": {
            "motion_count": 10,
            "success_count": 10,
            "success_rate": 1.0,
            "mpjpe_l": 20.0,
        },
        "selection_seed": 42,
        "novelty_gate_pass": True,
        "candidates": [stage_5_candidate, candidate, stage_4000_candidate],
        "selected": candidate,
        "sources": {
            "stock_heldout": {
                "label": "stock",
                "split": "heldout",
                "path": "summaries/stock-heldout-seed-42.json",
                "sha256": hashlib.sha256(stock_heldout_summary.read_bytes()).hexdigest(),
            },
            "stock_retention": {
                "label": "stock",
                "split": "retention",
                "path": "summaries/stock-retention-seed-42.json",
                "sha256": hashlib.sha256(stock_retention_summary.read_bytes()).hexdigest(),
            },
            "candidates": {
                "stage-5": {
                    "heldout": {
                        "label": "stage-5",
                        "split": "heldout",
                        "path": "summaries/stage-5-heldout-seed-42.json",
                        "sha256": hashlib.sha256(stage_5_heldout_summary.read_bytes()).hexdigest(),
                    },
                    "retention": {
                        "label": "stage-5",
                        "split": "retention",
                        "path": "summaries/stage-5-retention-seed-42.json",
                        "sha256": hashlib.sha256(
                            stage_5_retention_summary.read_bytes()
                        ).hexdigest(),
                    },
                },
                "stage-500": {
                    "heldout": {
                        "label": "stage-500",
                        "split": "heldout",
                        "path": "summaries/stage-500-heldout-seed-42.json",
                        "sha256": hashlib.sha256(selected_heldout_summary.read_bytes()).hexdigest(),
                    },
                    "retention": {
                        "label": "stage-500",
                        "split": "retention",
                        "path": "summaries/stage-500-retention-seed-42.json",
                        "sha256": hashlib.sha256(
                            selected_retention_summary.read_bytes()
                        ).hexdigest(),
                    },
                },
                "stage-4000": {
                    "heldout": {
                        "label": "stage-4000",
                        "split": "heldout",
                        "path": "summaries/stage-4000-heldout-seed-42.json",
                        "sha256": hashlib.sha256(
                            stage_4000_heldout_summary.read_bytes()
                        ).hexdigest(),
                    },
                    "retention": {
                        "label": "stage-4000",
                        "split": "retention",
                        "path": "summaries/stage-4000-retention-seed-42.json",
                        "sha256": hashlib.sha256(
                            stage_4000_retention_summary.read_bytes()
                        ).hexdigest(),
                    },
                },
            },
        },
    }
    selection_path = tmp_path / "selection.json"
    selection_path.write_text(json.dumps(selection), encoding="utf-8")
    novelty_path = tmp_path / "novelty.json"
    novelty_path.write_text(
        json.dumps(
            {
                "format": "shadow_dance_novelty_gate_v1",
                "novelty_gate_pass": True,
                "stock_success_rate": 0.0,
                "stock_mpjpe_l": 80.0,
                "max_stock_success": 0.75,
                "min_stock_mpjpe_l": 50.0,
                "source": {
                    "path": "summaries/stock-heldout-seed-42.json",
                    "sha256": hashlib.sha256(stock_heldout_summary.read_bytes()).hexdigest(),
                },
            }
        ),
        encoding="utf-8",
    )
    test_seeds = [101, 202, 303]
    stock_sources = [
        bound_summary(
            f"stock-test-seed-{seed}",
            "stock",
            "test",
            metric_payload(terminations=[True] * 4, mpjpe_l=80),
            seed=seed,
        )
        for seed in test_seeds
    ]
    selected_sources = [
        bound_summary(
            f"stage-500-test-seed-{seed}",
            "stage-500",
            "test",
            metric_payload(terminations=[False] * 4, mpjpe_l=28),
            seed=seed,
        )
        for seed in test_seeds
    ]
    stock_test = aggregate_summaries(
        summaries / "stock-test-aggregate.json",
        label="stock",
        split="test",
        summaries=stock_sources,
    )
    selected_test = aggregate_summaries(
        summaries / "stage-500-test-aggregate.json",
        label="stage-500",
        split="test",
        summaries=selected_sources,
    )
    stock_aggregate = json.loads(stock_test.read_text(encoding="utf-8"))
    selected_aggregate = json.loads(selected_test.read_text(encoding="utf-8"))
    motion_ids = tuple(stock_aggregate["motion_inventory"])
    seed_ids = tuple(stock_aggregate["seeds"])

    def compact(payload: dict) -> dict:
        return {
            key: payload[key]
            for key in (
                "motion_count",
                "seed_count",
                "trial_count",
                "success_count",
                "success_rate",
                "mpjpe_l",
            )
        }

    comparison = {
        "format": "shadow_dance_final_comparison_v1",
        "split": "test",
        "used_for_checkpoint_selection": False,
        "selected_label": "stage-500",
        "selection_report_sha256": hashlib.sha256(selection_path.read_bytes()).hexdigest(),
        "stock": compact(stock_aggregate),
        "selected": compact(selected_aggregate),
        "success_rate_delta": (
            selected_aggregate["success_rate"] - stock_aggregate["success_rate"]
        ),
        "mpjpe_l_improvement_fraction": (
            1.0 - selected_aggregate["mpjpe_l"] / stock_aggregate["mpjpe_l"]
        ),
        "motion_inventory_sha256": hashlib.sha256(
            json.dumps(motion_ids, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "seed_inventory_sha256": hashlib.sha256(
            json.dumps(seed_ids, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "sources": {
            "stock_summary": {
                "path": "summaries/stock-test-aggregate.json",
                "sha256": hashlib.sha256(stock_test.read_bytes()).hexdigest(),
            },
            "selected_summary": {
                "path": "summaries/stage-500-test-aggregate.json",
                "sha256": hashlib.sha256(selected_test.read_bytes()).hexdigest(),
            },
        },
    }
    comparison_path = tmp_path / "final-comparison.json"
    comparison_path.write_text(json.dumps(comparison), encoding="utf-8")
    media = tmp_path / "media"
    (media / "stock").mkdir(parents=True)
    (media / "selected").mkdir(parents=True)

    def media_entry(path: Path) -> dict:
        return {
            "path": path.relative_to(media).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "fps": 30.0,
            "duration_seconds": 5.0,
        }

    stock_clips = []
    selected_clips = []
    for index in range(4):
        stock_clip = media / "stock" / f"{index:06d}.mp4"
        selected_clip = media / "selected" / f"{index:06d}.mp4"
        stock_clip.write_bytes(f"stock-video-{index}".encode())
        selected_clip.write_bytes(f"selected-video-{index}".encode())
        stock_clips.append({**media_entry(stock_clip), "motion": MOTIONS["test"][index]})
        selected_clips.append({**media_entry(selected_clip), "motion": MOTIONS["test"][index]})
    reference_video = media / "reference-kinematic.mp4"
    reference_video.write_bytes(b"reference-video")
    hero_video = media / "hero-before-after.mp4"
    hero_video.write_bytes(b"edited-video")
    hero_entry = media_entry(hero_video)
    hero_entry.update({"frame_count": 900, "duration_seconds": 30.0})
    (media / "video-manifest.json").write_text(
        json.dumps(
            {
                "format": "shadow_dance_video_manifest_v1",
                "edited_comparison": True,
                "reference_is_policy_output": False,
                "source_policy_runs_uncut": True,
                "selected_label": "stage-500",
                "render_seed": 303,
                "final_comparison": {
                    "path": "final-comparison.json",
                    "sha256": hashlib.sha256(comparison_path.read_bytes()).hexdigest(),
                },
                "reference": media_entry(reference_video),
                "stock": stock_clips,
                "selected": selected_clips,
                "output": hero_entry,
            }
        ),
        encoding="utf-8",
    )
    onnx_path = tmp_path / "onnx-report.json"
    onnx_artifacts = []
    for path in sorted(release.glob("*.onnx")):
        onnx_artifacts.append(
            {
                "file": path.name,
                "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "checker_pass": True,
                "inference": {"attempted": True, "passed": True},
            }
        )
    onnx_path.write_text(
        json.dumps(
            {
                "format": "shadow_dance_onnx_validation_v1",
                "overall_pass": True,
                "portal_nominee": "model_step_000500_g1.onnx",
                "bundle_prefix": "model_step_000500",
                "artifacts": onnx_artifacts,
            }
        ),
        encoding="utf-8",
    )
    for path in (novelty_path, selection_path, comparison_path, onnx_path):
        (release / path.name).write_bytes(path.read_bytes())
    checksum_lines = [
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  ./{path.name}"
        for path in sorted(release.iterdir())
    ]
    (release / "SHA256SUMS").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    report = tmp_path / "publish-report.json"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "publish_model.py"),
            "--run-root",
            str(tmp_path),
            "--repo-id",
            "example/shadow-dance",
            "--dry-run",
            "--report",
            str(report),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(report.read_text(encoding="utf-8"))["selected_label"] == "stage-500"

    video_manifest_path = media / "video-manifest.json"
    original_video_manifest = video_manifest_path.read_bytes()
    forged_video_manifest = json.loads(original_video_manifest)
    forged_video_manifest["selected_label"] = "stage-4000"
    video_manifest_path.write_text(json.dumps(forged_video_manifest), encoding="utf-8")
    failed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "publish_model.py"),
            "--run-root",
            str(tmp_path),
            "--repo-id",
            "example/shadow-dance",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
    )
    assert failed.returncode != 0
    assert "video evidence checkpoint label differs" in failed.stderr
    video_manifest_path.write_bytes(original_video_manifest)

    original_selection = selection_path.read_bytes()
    forged_selection = json.loads(original_selection)
    forged_selection["candidates"][0]["hero_success_delta"] = 0.5
    forged_selection["selected"]["hero_success_delta"] = 0.5
    selection_path.write_text(json.dumps(forged_selection), encoding="utf-8")
    (release / "selection.json").write_bytes(selection_path.read_bytes())
    failed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "publish_model.py"),
            "--run-root",
            str(tmp_path),
            "--repo-id",
            "example/shadow-dance",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
    )
    assert failed.returncode != 0
    assert "forged hero_success_delta" in failed.stderr
    selection_path.write_bytes(original_selection)
    (release / "selection.json").write_bytes(original_selection)

    original_stock_test = stock_test.read_bytes()
    stock_test.write_bytes(original_stock_test + b"\n")
    failed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "publish_model.py"),
            "--run-root",
            str(tmp_path),
            "--repo-id",
            "example/shadow-dance",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
    )
    assert failed.returncode != 0
    assert "does not match stock_summary" in failed.stderr
    stock_test.write_bytes(original_stock_test)

    raw_metrics = tmp_path / "eval" / stock_sources[0].stem / "metrics_eval.json"
    original_raw_metrics = raw_metrics.read_bytes()
    raw_metrics.write_bytes(original_raw_metrics + b"\n")
    failed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "publish_model.py"),
            "--run-root",
            str(tmp_path),
            "--repo-id",
            "example/shadow-dance",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
    )
    assert failed.returncode != 0
    assert "not bound to raw metrics" in failed.stderr
    raw_metrics.write_bytes(original_raw_metrics)

    stock_video = media / "stock" / "000000.mp4"
    original_stock_video = stock_video.read_bytes()
    stock_video.write_bytes(original_stock_video + b"tampered")
    failed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "publish_model.py"),
            "--run-root",
            str(tmp_path),
            "--repo-id",
            "example/shadow-dance",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
    )
    assert failed.returncode != 0
    assert "stock source video identity mismatch" in failed.stderr
    stock_video.write_bytes(original_stock_video)

    (release / "last.pt").write_bytes(b"tampered")
    failed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "publish_model.py"),
            "--run-root",
            str(tmp_path),
            "--repo-id",
            "example/shadow-dance",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
    )
    assert failed.returncode != 0
    assert "does not match the selected checkpoint identity" in failed.stderr
