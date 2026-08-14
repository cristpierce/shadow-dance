from __future__ import annotations

import numpy as np

from shadow_dance.motion import JOINT_NAMES, mirror_pose, neutral_pose, smootherstep


def test_joint_contract_has_29_unique_names() -> None:
    assert len(JOINT_NAMES) == 29
    assert len(set(JOINT_NAMES)) == 29


def test_smootherstep_endpoints_and_monotonicity() -> None:
    values = smootherstep(np.linspace(0.0, 1.0, 101))
    assert values[0] == 0.0
    assert values[-1] == 1.0
    assert np.all(np.diff(values) >= 0.0)


def test_mirror_is_an_involution() -> None:
    pose = neutral_pose() + np.linspace(-0.2, 0.2, 29)
    assert np.allclose(mirror_pose(mirror_pose(pose)), pose)
