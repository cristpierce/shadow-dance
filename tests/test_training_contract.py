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
    assert str(workflow["envs"]["LADDER"]) == expected_ladder
    assert str(workflow["envs"]["MAX_WALLTIME"]) == expected_walltime

    pipeline = (ROOT / "scripts" / "cloud_pipeline.sh").read_text(encoding="utf-8")
    materializer = (ROOT / "scripts" / "materialize_cloud_plan.py").read_text(
        encoding="utf-8"
    )
    assert f'LADDER="${{LADDER:-{expected_ladder}}}"' in pipeline
    assert f'"LADDER": "{expected_ladder}"' in materializer
    assert f'"MAX_WALLTIME": "{expected_walltime}"' in materializer

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
