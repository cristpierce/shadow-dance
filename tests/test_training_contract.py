from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[1]


def test_frozen_training_contract_is_consistent() -> None:
    expected_iterations = [5, 500, 4000]
    expected_ladder = ",".join(map(str, expected_iterations))
    expected_labels = {f"stage-{iteration}" for iteration in expected_iterations}
    expected_walltime = "10h"

    config = yaml.safe_load(
        (ROOT / "configs" / "shadow_dip_finetune.yaml").read_text(encoding="utf-8")
    )
    workflow = yaml.safe_load(
        (ROOT / "cloud" / "sky-shadow-dance.yaml").read_text(encoding="utf-8")
    )
    assert config["checkpoint_ladder_iterations"] == expected_iterations
    assert config["max_walltime"] == expected_walltime
    assert config["stage_walltime_budget_seconds"] == {5: 900, 500: 3600, 4000: 21600}
    assert config["training_timeout_seconds"] == {5: 600, 500: 3000, 4000: 19800}
    assert config["submission_deadline_utc"] == "2026-08-17T06:59:00Z"
    assert config["finalization_reserve_seconds"] == 7200
    assert config["portal_reserve_seconds"] == 2700
    assert config["max_walltime_seconds"] == 36000
    assert str(workflow["envs"]["LADDER"]) == expected_ladder
    assert str(workflow["envs"]["MAX_WALLTIME"]) == expected_walltime
    assert workflow["envs"]["STAGE_WALLTIME_BUDGET_SECONDS"] == (
        "5:900,500:3600,4000:21600"
    )
    assert workflow["envs"]["TRAINING_TIMEOUT_SECONDS"] == "5:600,500:3000,4000:19800"
    assert workflow["envs"]["SUBMISSION_DEADLINE_UTC"] == "2026-08-17T06:59:00Z"
    assert str(workflow["envs"]["FINALIZATION_RESERVE_SECONDS"]) == "7200"
    assert str(workflow["envs"]["PORTAL_RESERVE_SECONDS"]) == "2700"
    assert str(workflow["envs"]["MAX_WALLTIME_SECONDS"]) == "36000"

    pipeline = (ROOT / "scripts" / "cloud_pipeline.sh").read_text(encoding="utf-8")
    materializer = (ROOT / "scripts" / "materialize_cloud_plan.py").read_text(
        encoding="utf-8"
    )
    assert f'LADDER="${{LADDER:-{expected_ladder}}}"' in pipeline
    assert f'"LADDER": "{expected_ladder}"' in materializer
    assert f'"MAX_WALLTIME": "{expected_walltime}"' in materializer
    assert '"SUBMISSION_DEADLINE_UTC": "2026-08-17T06:59:00Z"' in materializer

    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from build_submission_video import (
            EXPECTED_CANDIDATE_LABELS as VIDEO_EXPECTED_CANDIDATE_LABELS,
        )
        from publish_model import EXPECTED_CANDIDATE_LABELS
    finally:
        sys.path.pop(0)
    assert expected_labels == EXPECTED_CANDIDATE_LABELS
    assert expected_labels == VIDEO_EXPECTED_CANDIDATE_LABELS
