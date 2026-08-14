from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import numpy as np
import pytest

from shadow_dance.motion import G1Kinematics, SequenceSpec, generate_motion, write_motion_csv
from shadow_dance.validation import MotionValidator


def _mjcf() -> Path:
    root = os.environ.get("SONIC_ROOT")
    if not root:
        pytest.skip("SONIC_ROOT is not set")
    return (
        Path(root)
        / "gear_sonic"
        / "data"
        / "assets"
        / "robot_description"
        / "mjcf"
        / "g1_29dof_rev_1_0.xml"
    )


def test_generated_hero_passes_hard_validation() -> None:
    mjcf = _mjcf()
    spec = SequenceSpec(
        id="shadow_dip_test", split="test", amplitude=0.72, duration_s=3.2, hold_s=0.3
    )
    generated = generate_motion(spec, G1Kinematics(mjcf))
    result = MotionValidator(mjcf).validate_entry(spec.id, generated.entry)
    assert result["pass"], result["errors"]
    assert generated.ik_max_position_error_m < 0.006
    assert generated.ik_max_orientation_error_deg < 3.0


def test_csv_round_trip_matches_upstream_converter(tmp_path: Path) -> None:
    mjcf = _mjcf()
    spec = SequenceSpec(
        id="shadow_dip_roundtrip", split="test", amplitude=0.62, duration_s=3.0, hold_s=0.3
    )
    generated = generate_motion(spec, G1Kinematics(mjcf))
    csv_path = tmp_path / f"{spec.id}.csv"
    write_motion_csv(csv_path, generated.entry)

    converter_path = mjcf.parents[4] / "data_process" / "convert_soma_csv_to_motion_lib.py"
    module_spec = importlib.util.spec_from_file_location("sonic_converter", converter_path)
    assert module_spec and module_spec.loader
    converter = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(converter)
    converted = converter.convert_sequence(converter.load_bones_csv(str(csv_path)), fps=50)

    for field in ("root_trans_offset", "pose_aa", "dof", "root_rot", "smpl_joints"):
        assert np.allclose(converted[field], generated.entry[field], atol=2e-6), field
    assert converted["fps"] == generated.entry["fps"] == 50
