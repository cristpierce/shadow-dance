"""Generate physically constrained Unitree G1 motion-library references.

The generator deliberately targets the exact 29-DOF MuJoCo ordering used by
GR00T-WholeBodyControl.  Foot trajectories are solved against NVIDIA's pinned G1
MJCF instead of being inferred from a third-party human-motion dataset.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import joblib
import mujoco
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

DATASET_VERSION = "shadow-dip-v1"
UPSTREAM_COMMIT = "c374bae5b9039cd0ee71377e654d11ce1bc69e1d"
FPS = 50

# MuJoCo actuator order in g1_29dof_rev_1_0.xml. This is also the `dof` order
# expected by SONIC's motion-lib converter.
JOINT_NAMES = [
    "left_hip_pitch_joint",
    "left_hip_roll_joint",
    "left_hip_yaw_joint",
    "left_knee_joint",
    "left_ankle_pitch_joint",
    "left_ankle_roll_joint",
    "right_hip_pitch_joint",
    "right_hip_roll_joint",
    "right_hip_yaw_joint",
    "right_knee_joint",
    "right_ankle_pitch_joint",
    "right_ankle_roll_joint",
    "waist_yaw_joint",
    "waist_roll_joint",
    "waist_pitch_joint",
    "left_shoulder_pitch_joint",
    "left_shoulder_roll_joint",
    "left_shoulder_yaw_joint",
    "left_elbow_joint",
    "left_wrist_roll_joint",
    "left_wrist_pitch_joint",
    "left_wrist_yaw_joint",
    "right_shoulder_pitch_joint",
    "right_shoulder_roll_joint",
    "right_shoulder_yaw_joint",
    "right_elbow_joint",
    "right_wrist_roll_joint",
    "right_wrist_pitch_joint",
    "right_wrist_yaw_joint",
]

DOF_AXIS = np.asarray(
    [
        [0, 1, 0],
        [1, 0, 0],
        [0, 0, 1],
        [0, 1, 0],
        [0, 1, 0],
        [1, 0, 0],
        [0, 1, 0],
        [1, 0, 0],
        [0, 0, 1],
        [0, 1, 0],
        [0, 1, 0],
        [1, 0, 0],
        [0, 0, 1],
        [1, 0, 0],
        [0, 1, 0],
        [0, 1, 0],
        [1, 0, 0],
        [0, 0, 1],
        [0, 1, 0],
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
        [0, 1, 0],
        [1, 0, 0],
        [0, 0, 1],
        [0, 1, 0],
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
    ],
    dtype=np.float32,
)

LEFT_LEG = np.arange(0, 6)
RIGHT_LEG = np.arange(6, 12)
LEFT_ARM = np.arange(15, 22)
RIGHT_ARM = np.arange(22, 29)


@dataclass(frozen=True)
class SequenceSpec:
    """One independently generated motion sequence."""

    id: str
    split: str
    kind: str = "shadow_dip"
    direction: str = "left"
    amplitude: float = 1.0
    duration_s: float = 5.0
    step_back_m: float = 0.14
    step_width_m: float = 0.05
    hold_s: float = 0.50
    seed: int = 0


@dataclass
class GeneratedMotion:
    """A SONIC motion-lib entry plus generation diagnostics."""

    entry: dict[str, Any]
    ik_max_position_error_m: float
    ik_max_orientation_error_deg: float
    phase_windows: dict[str, list[float]]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def smootherstep(value: np.ndarray | float) -> np.ndarray | float:
    """C2-continuous interpolation curve on [0, 1]."""

    x = np.clip(value, 0.0, 1.0)
    return x**3 * (x * (x * 6.0 - 15.0) + 10.0)


def _interpolate_keyframes(
    times: np.ndarray, key_times: np.ndarray, values: np.ndarray
) -> np.ndarray:
    result = np.empty((len(times),) + values.shape[1:], dtype=np.float64)
    for frame, time_s in enumerate(times):
        index = int(np.searchsorted(key_times, time_s, side="right") - 1)
        index = min(max(index, 0), len(key_times) - 2)
        span = key_times[index + 1] - key_times[index]
        alpha = 0.0 if span <= 0 else float((time_s - key_times[index]) / span)
        blend = smootherstep(alpha)
        result[frame] = values[index] * (1.0 - blend) + values[index + 1] * blend
    return result


def neutral_pose() -> np.ndarray:
    """Return a slightly flexed, controller-friendly 29-DOF stance."""

    pose = np.zeros(29, dtype=np.float64)
    for offset in (0, 6):
        pose[offset + 0] = -0.20
        pose[offset + 3] = 0.42
        pose[offset + 4] = -0.22
    pose[15:22] = [0.10, 0.24, 0.0, 0.48, 0.0, 0.0, 0.0]
    pose[22:29] = [0.10, -0.24, 0.0, 0.48, 0.0, 0.0, 0.0]
    return pose


def mirror_pose(pose: np.ndarray) -> np.ndarray:
    """Mirror a G1 pose across its sagittal plane."""

    mirrored = np.asarray(pose, dtype=np.float64).copy()
    mirrored[..., LEFT_LEG] = pose[..., RIGHT_LEG]
    mirrored[..., RIGHT_LEG] = pose[..., LEFT_LEG]
    mirrored[..., LEFT_ARM] = pose[..., RIGHT_ARM]
    mirrored[..., RIGHT_ARM] = pose[..., LEFT_ARM]
    # Axial rotations about X (roll) and Z (yaw) change sign under reflection.
    sign_flip = [1, 2, 5, 7, 8, 11, 12, 13, 16, 17, 19, 21, 23, 24, 26, 28]
    mirrored[..., sign_flip] *= -1.0
    return mirrored


def _hero_upper_body_keyframes(amplitude: float, direction: str) -> np.ndarray:
    neutral = neutral_pose()
    frame = neutral.copy()
    frame[12:15] = [-0.08, 0.06, 0.05]
    frame[15:22] = [-0.42, 0.62, -0.30, 0.80, -0.18, 0.08, -0.10]
    frame[22:29] = [-0.75, -0.55, 0.32, 1.00, 0.18, -0.10, 0.12]

    pivot = frame.copy()
    pivot[12:15] = [-0.20, 0.12, -0.10]
    pivot[15:22] += [-0.12, 0.10, -0.18, 0.08, -0.08, 0.06, -0.08]
    pivot[22:29] += [-0.07, -0.07, 0.10, 0.10, 0.08, -0.06, 0.08]

    dip = pivot.copy()
    dip[12:15] = [-0.28, 0.43, -0.45]
    dip[15:22] = [-0.78, 0.92, -0.58, 1.08, -0.35, 0.22, -0.25]
    dip[22:29] = [-0.90, -0.60, 0.50, 1.15, 0.30, -0.20, 0.30]

    # Preserve a readable arm frame even in the shallow curriculum examples.
    arm_floor = 0.62
    scale = np.ones(29)
    scale[12:15] = amplitude
    scale[15:29] = arm_floor + (1.0 - arm_floor) * amplitude
    frame = neutral + (frame - neutral) * scale
    pivot = neutral + (pivot - neutral) * scale
    dip = neutral + (dip - neutral) * scale

    keyframes = np.stack([neutral, frame, pivot, dip, dip, frame, neutral])
    if direction == "right":
        keyframes = mirror_pose(keyframes)
    return keyframes


def _retention_keyframes(spec: SequenceSpec) -> np.ndarray:
    neutral = neutral_pose()
    target = neutral.copy()
    if spec.kind == "squat":
        for offset in (0, 6):
            target[offset + 0] = -0.40
            target[offset + 3] = 0.84
            target[offset + 4] = -0.44
        target[15] = target[22] = 0.25
    elif spec.kind == "sway":
        target[13] = 0.14 if spec.direction == "left" else -0.14
        target[16] = 0.38
        target[23] = -0.38
    elif spec.kind == "torso_turn":
        sign = 1.0 if spec.direction == "left" else -1.0
        target[12] = 0.34 * sign
        target[17] = -0.22 * sign
        target[24] = 0.22 * sign
    elif spec.kind != "stand":
        raise ValueError(f"Unsupported sequence kind: {spec.kind}")
    return np.stack([neutral, neutral, target, target, target, neutral, neutral])


class G1Kinematics:
    """Small MuJoCo-backed inverse-kinematics helper for planted feet."""

    def __init__(self, mjcf_path: Path):
        self.mjcf_path = Path(mjcf_path)
        self.model = mujoco.MjModel.from_xml_path(str(self.mjcf_path))
        self.data = mujoco.MjData(self.model)
        self.qpos_addr = np.asarray(
            [
                self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, n)]
                for n in JOINT_NAMES
            ],
            dtype=np.int32,
        )
        self.joint_ids = np.asarray(
            [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, n) for n in JOINT_NAMES],
            dtype=np.int32,
        )
        self.lower = self.model.jnt_range[self.joint_ids, 0].copy() + 0.02
        self.upper = self.model.jnt_range[self.joint_ids, 1].copy() - 0.02
        self.foot_body_ids = {
            side: mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, f"{side}_ankle_roll_link")
            for side in ("left", "right")
        }
        self.base_qpos = np.zeros(self.model.nq, dtype=np.float64)
        self.base_qpos[:3] = [0.0, 0.0, 0.793]
        self.base_qpos[3:7] = [1.0, 0.0, 0.0, 0.0]

    def set_state(self, root_xyz: np.ndarray, joints: np.ndarray) -> None:
        self.data.qpos[:] = self.base_qpos
        self.data.qpos[:3] = root_xyz
        self.data.qpos[self.qpos_addr] = joints
        mujoco.mj_forward(self.model, self.data)

    def foot_transform(self, side: str) -> tuple[np.ndarray, np.ndarray]:
        body_id = self.foot_body_ids[side]
        return self.data.xpos[body_id].copy(), self.data.xmat[body_id].reshape(3, 3).copy()

    def neutral_geometry(
        self, joints: np.ndarray
    ) -> tuple[np.ndarray, dict[str, tuple[np.ndarray, np.ndarray]]]:
        root = np.asarray([0.0, 0.0, 0.793], dtype=np.float64)
        self.set_state(root, joints)
        feet = {side: self.foot_transform(side) for side in ("left", "right")}
        # The collision points in the official MJCF are 3 cm below the ankle-roll origin.
        sole_z = min(position[2] - 0.03 for position, _ in feet.values())
        root[2] -= sole_z
        self.set_state(root, joints)
        feet = {side: self.foot_transform(side) for side in ("left", "right")}
        return root, feet

    def solve_leg(
        self,
        side: str,
        root_xyz: np.ndarray,
        all_joints: np.ndarray,
        target_position: np.ndarray,
        target_rotation: np.ndarray,
        initial: np.ndarray,
    ) -> tuple[np.ndarray, float, float]:
        indices = LEFT_LEG if side == "left" else RIGHT_LEG

        def residual(candidate: np.ndarray) -> np.ndarray:
            pose = all_joints.copy()
            pose[indices] = candidate
            self.set_state(root_xyz, pose)
            position, rotation = self.foot_transform(side)
            position_error = position - target_position
            orientation_error = Rotation.from_matrix(target_rotation.T @ rotation).as_rotvec()
            return np.concatenate([position_error * 16.0, orientation_error * 4.0])

        def solve(seed: np.ndarray):
            return least_squares(
                residual,
                np.clip(seed, self.lower[indices], self.upper[indices]),
                bounds=(self.lower[indices], self.upper[indices]),
                xtol=1e-9,
                ftol=1e-9,
                gtol=1e-9,
                max_nfev=100,
            )

        result = solve(initial)
        # A large step can place the previous frame on a different IK branch. Retry
        # from the authored nominal pose and keep the lower-residual solution.
        nominal = all_joints[indices]
        if result.cost > 1e-5 and not np.allclose(initial, nominal, atol=1e-4):
            alternate = solve(nominal)
            if alternate.cost < result.cost:
                result = alternate
        solved = result.x
        pose = all_joints.copy()
        pose[indices] = solved
        self.set_state(root_xyz, pose)
        position, rotation = self.foot_transform(side)
        pos_error = float(np.linalg.norm(position - target_position))
        orientation_delta = Rotation.from_matrix(target_rotation.T @ rotation).as_rotvec()
        ori_error = float(np.degrees(np.linalg.norm(orientation_delta)))
        return solved, pos_error, ori_error


def _phase_contract(spec: SequenceSpec) -> tuple[np.ndarray, dict[str, list[float]]]:
    duration = spec.duration_s
    hold_fraction = spec.hold_s / duration
    deepest_start = 0.48
    deepest_end = min(deepest_start + hold_fraction, 0.66)
    fractions = np.asarray([0.0, 0.12, 0.28, deepest_start, deepest_end, 0.86, 1.0])
    windows = {
        "establish_frame": [0.0, round(0.12 * duration, 3)],
        "step_and_pivot": [round(0.12 * duration, 3), round(0.28 * duration, 3)],
        "descend": [round(0.28 * duration, 3), round(deepest_start * duration, 3)],
        "hold": [round(deepest_start * duration, 3), round(deepest_end * duration, 3)],
        "recover": [round(deepest_end * duration, 3), round(0.86 * duration, 3)],
        "settle": [round(0.86 * duration, 3), round(duration, 3)],
    }
    return fractions * duration, windows


def generate_motion(
    spec: SequenceSpec, kinematics: G1Kinematics, fps: int = FPS
) -> GeneratedMotion:
    """Generate one motion and solve its leg trajectories against planted-foot targets."""

    if spec.direction not in {"left", "right"}:
        raise ValueError("direction must be 'left' or 'right'")
    if not 0.45 <= spec.amplitude <= 1.05:
        raise ValueError("amplitude must be between 0.45 and 1.05")

    times = np.linspace(0.0, spec.duration_s, int(round(spec.duration_s * fps)) + 1)
    key_times, phase_windows = _phase_contract(spec)
    if spec.kind == "shadow_dip":
        keyframes = _hero_upper_body_keyframes(spec.amplitude, spec.direction)
    else:
        keyframes = _retention_keyframes(spec)
    joints = _interpolate_keyframes(times, key_times, keyframes)

    neutral_root, neutral_feet = kinematics.neutral_geometry(neutral_pose())
    sign = 1.0 if spec.direction == "left" else -1.0

    root_keys = np.repeat(neutral_root[None, :], 7, axis=0)
    left_targets = np.repeat(neutral_feet["left"][0][None, :], 7, axis=0)
    right_targets = np.repeat(neutral_feet["right"][0][None, :], 7, axis=0)
    left_rotations = np.repeat(neutral_feet["left"][1][None, :, :], 7, axis=0)
    right_rotations = np.repeat(neutral_feet["right"][1][None, :, :], 7, axis=0)

    if spec.kind == "shadow_dip":
        depth = 0.140 * spec.amplitude
        lateral = 0.047 * spec.amplitude * sign
        # Shift above the planted stance foot before lifting the other foot. The
        # lateral transfer is part of the choreography and keeps the single-support
        # interval physically interpretable instead of relying on kinematic foot lift.
        root_keys[1] += [0.0, 0.097 * sign, -0.070]
        root_keys[2] += [0.005, 0.097 * sign, -0.070]
        root_keys[3:5] += [-0.030 * spec.amplitude, lateral, -depth]
        root_keys[5] += [-0.005, 0.097 * sign, -0.070]

        # The foot opposite the dip direction steps back/out, then plants for the hold.
        moving_side = "right" if spec.direction == "left" else "left"
        target_array = right_targets if moving_side == "right" else left_targets
        rotation_array = right_rotations if moving_side == "right" else left_rotations
        target_array[2:6, 0] -= spec.step_back_m * spec.amplitude
        target_array[2:6, 1] -= spec.step_width_m * sign * spec.amplitude
        yaw = -math.radians(11.0) * sign * spec.amplitude
        yaw_rotation = Rotation.from_euler("z", yaw).as_matrix()
        rotation_array[2:6] = yaw_rotation @ rotation_array[2:6]
    elif spec.kind == "squat":
        root_keys[2:5, 2] -= 0.105 * spec.amplitude
    elif spec.kind == "sway":
        root_keys[2:5, 1] += 0.025 * sign

    roots = _interpolate_keyframes(times, key_times, root_keys)
    left_position_series = _interpolate_keyframes(times, key_times, left_targets)
    right_position_series = _interpolate_keyframes(times, key_times, right_targets)
    moving_side = None
    return_landing = None
    if spec.kind == "shadow_dip":
        moving_side = "right" if spec.direction == "left" else "left"
        moving_series = right_position_series if moving_side == "right" else left_position_series
        return_start, return_end = key_times[5], key_times[6]
        return_landing = return_start + 0.45 * (return_end - return_start)
        for frame, time_s in enumerate(times):
            if return_start <= time_s <= return_landing:
                progress = (time_s - return_start) / (return_landing - return_start)
                blend = float(smootherstep(progress))
                moving_series[frame] = (
                    moving_series[np.searchsorted(times, return_start)] * (1.0 - blend)
                    + neutral_feet[moving_side][0] * blend
                )
                roots[frame] = root_keys[5]
            elif time_s > return_landing:
                moving_series[frame] = neutral_feet[moving_side][0]
                progress = (time_s - return_landing) / (return_end - return_landing)
                blend = float(smootherstep(progress))
                roots[frame] = root_keys[5] * (1.0 - blend) + root_keys[6] * blend

    # Rotations only vary for the step/pivot. Slerp one interval at a time.
    rotations: dict[str, list[np.ndarray]] = {"left": [], "right": []}
    for time_s in times:
        index = int(np.searchsorted(key_times, time_s, side="right") - 1)
        index = min(max(index, 0), len(key_times) - 2)
        span = key_times[index + 1] - key_times[index]
        alpha = 0.0 if span <= 0 else float((time_s - key_times[index]) / span)
        blend = float(smootherstep(alpha))
        for side, key_rots in (("left", left_rotations), ("right", right_rotations)):
            rotation_start = key_rots[index]
            rotation_end = key_rots[index + 1]
            if (
                side == moving_side
                and return_landing is not None
                and key_times[5] <= time_s <= return_landing
            ):
                progress = (time_s - key_times[5]) / (return_landing - key_times[5])
                blend = float(smootherstep(progress))
                rotation_start = key_rots[5]
                rotation_end = key_rots[6]
            elif side == moving_side and return_landing is not None and time_s > return_landing:
                blend = 1.0
                rotation_start = key_rots[5]
                rotation_end = key_rots[6]
            relative = Rotation.from_matrix(rotation_start.T @ rotation_end).as_rotvec()
            interpolated = rotation_start @ Rotation.from_rotvec(relative * blend).as_matrix()
            rotations[side].append(interpolated)

    # A smooth swing-foot arc prevents the back-step from being represented as floor skating.
    if spec.kind == "shadow_dip":
        start, end = key_times[1], key_times[2]
        moving_series = right_position_series if spec.direction == "left" else left_position_series
        for frame, time_s in enumerate(times):
            lift = 0.0
            if start <= time_s <= end:
                progress = (time_s - start) / (end - start)
                lift = 0.050 * spec.amplitude * 16.0 * progress**2 * (1.0 - progress) ** 2
            elif return_landing is not None and return_start <= time_s <= return_landing:
                progress = (time_s - return_start) / (return_landing - return_start)
                lift = 0.040 * spec.amplitude * 16.0 * progress**2 * (1.0 - progress) ** 2
            moving_series[frame, 2] += lift

    max_pos_error = 0.0
    max_ori_error = 0.0
    previous = joints[0].copy()
    for frame in range(len(times)):
        pose = joints[frame].copy()
        for side, indices, target_positions in (
            ("left", LEFT_LEG, left_position_series),
            ("right", RIGHT_LEG, right_position_series),
        ):
            solved, pos_error, ori_error = kinematics.solve_leg(
                side,
                roots[frame],
                pose,
                target_positions[frame],
                rotations[side][frame],
                previous[indices],
            )
            pose[indices] = solved
            previous[indices] = solved
            max_pos_error = max(max_pos_error, pos_error)
            max_ori_error = max(max_ori_error, ori_error)
        joints[frame] = pose
        previous = pose

    pose_aa = np.zeros((len(times), 30, 3), dtype=np.float32)
    pose_aa[:, 1:, :] = DOF_AXIS[None, :, :] * joints[:, :, None]
    root_rot = np.zeros((len(times), 4), dtype=np.float32)
    root_rot[:, 3] = 1.0  # xyzw identity
    entry = {
        "root_trans_offset": roots.astype(np.float32),
        "pose_aa": pose_aa,
        "dof": joints.astype(np.float32),
        "root_rot": root_rot,
        "smpl_joints": np.zeros((len(times), 24, 3), dtype=np.float32),
        "fps": fps,
    }
    return GeneratedMotion(entry, max_pos_error, max_ori_error, phase_windows)


def default_specs() -> list[SequenceSpec]:
    """Return frozen train/validation specifications for dataset v1."""

    specs: list[SequenceSpec] = []
    amplitudes = [0.62, 0.76, 0.88, 1.0]
    durations = [5.7, 5.2, 4.8]
    counter = 1
    for direction in ("left", "right"):
        for amplitude, duration in zip(amplitudes[:3], durations, strict=True):
            specs.append(
                SequenceSpec(
                    id=f"shadow_dip_{direction}_train_{counter:02d}",
                    split="train",
                    direction=direction,
                    amplitude=amplitude,
                    duration_s=duration,
                    step_back_m=0.11 + 0.03 * amplitude,
                    hold_s=0.42 + 0.10 * amplitude,
                    seed=counter,
                )
            )
            counter += 1
    # Six additional hero variants alter timing and geometry without duplicating frames.
    for direction, amplitude, duration, step, hold in [
        ("left", 0.70, 4.5, 0.12, 0.38),
        ("right", 0.70, 4.6, 0.12, 0.40),
        ("left", 0.94, 5.5, 0.16, 0.62),
        ("right", 0.94, 5.4, 0.16, 0.60),
        ("left", 0.94, 5.0, 0.15, 0.52),
        ("right", 0.94, 5.1, 0.15, 0.54),
    ]:
        specs.append(
            SequenceSpec(
                id=f"shadow_dip_{direction}_train_{counter:02d}",
                split="train",
                direction=direction,
                amplitude=amplitude,
                duration_s=duration,
                step_back_m=step,
                hold_s=hold,
                seed=counter,
            )
        )
        counter += 1

    for kind, direction in [
        ("stand", "left"),
        ("squat", "left"),
        ("sway", "left"),
        ("sway", "right"),
        ("torso_turn", "left"),
        ("torso_turn", "right"),
    ]:
        specs.append(
            SequenceSpec(
                id=f"retention_{kind}_{direction}",
                split="train",
                kind=kind,
                direction=direction,
                amplitude=0.72,
                duration_s=4.0,
                step_back_m=0.0,
                step_width_m=0.0,
                hold_s=0.5,
                seed=counter,
            )
        )
        counter += 1

    for direction, amplitude, duration, step, hold in [
        ("left", 0.82, 4.65, 0.135, 0.47),
        ("right", 0.82, 4.75, 0.135, 0.49),
        ("left", 0.95, 5.25, 0.155, 0.58),
        ("right", 0.95, 5.35, 0.155, 0.60),
    ]:
        specs.append(
            SequenceSpec(
                id=f"shadow_dip_{direction}_heldout_{counter:02d}",
                split="heldout",
                direction=direction,
                amplitude=amplitude,
                duration_s=duration,
                step_back_m=step,
                hold_s=hold,
                seed=counter,
            )
        )
        counter += 1
    return specs


def write_motion_csv(path: Path, entry: dict[str, Any]) -> None:
    """Write a transparent Bones-compatible source CSV (degrees and centimetres)."""

    path.parent.mkdir(parents=True, exist_ok=True)
    header = [
        "Frame",
        "root_translateX",
        "root_translateY",
        "root_translateZ",
        "root_rotateX",
        "root_rotateY",
        "root_rotateZ",
        *[f"{name}_dof" for name in JOINT_NAMES],
    ]
    root_cm = np.asarray(entry["root_trans_offset"]) * 100.0
    joints_deg = np.degrees(np.asarray(entry["dof"]))
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(header)
        for frame in range(len(joints_deg)):
            writer.writerow(
                [frame, *root_cm[frame].round(7), 0.0, 0.0, 0.0, *joints_deg[frame].round(7)]
            )


def generate_dataset(
    output_dir: Path,
    mjcf_path: Path,
    manifest_path: Path,
    specs: list[SequenceSpec] | None = None,
) -> dict[str, Any]:
    """Generate all frozen sequences, their source CSVs, PKLs, splits, and manifest."""

    specs = specs or default_specs()
    output_dir = Path(output_dir)
    manifest_path = Path(manifest_path)
    kinematics = G1Kinematics(mjcf_path)
    records: list[dict[str, Any]] = []

    for spec in specs:
        generated = generate_motion(spec, kinematics)
        split_dir = output_dir / spec.split
        split_dir.mkdir(parents=True, exist_ok=True)
        pkl_path = split_dir / f"{spec.id}.pkl"
        csv_path = output_dir / "csv" / spec.split / f"{spec.id}.csv"
        joblib.dump({spec.id: generated.entry}, pkl_path, compress=3)
        write_motion_csv(csv_path, generated.entry)
        records.append(
            {
                **asdict(spec),
                "robot": "unitree_g1_29dof",
                "source": "team-authored procedural keyframes plus MuJoCo foot IK",
                "source_license": "Apache-2.0",
                "performer_consent": "not_applicable_synthetic",
                "upstream_mjcf_commit": UPSTREAM_COMMIT,
                "fps": generated.entry["fps"],
                "frames": int(len(generated.entry["dof"])),
                "smpl": "dummy",
                "phase_windows_s": generated.phase_windows,
                "ik_max_position_error_m": generated.ik_max_position_error_m,
                "ik_max_orientation_error_deg": generated.ik_max_orientation_error_deg,
                "files": {
                    "motion_lib": str(pkl_path.relative_to(output_dir)).replace("\\", "/"),
                    "source_csv": str(csv_path.relative_to(output_dir)).replace("\\", "/"),
                    "motion_lib_sha256": sha256_file(pkl_path),
                    "source_csv_sha256": sha256_file(csv_path),
                },
            }
        )

    manifest = {
        "dataset": DATASET_VERSION,
        "created_by": "Team SELTZER",
        "generator": "shadow-dance",
        "generator_version": "0.1.0",
        "upstream": {
            "repository": "https://github.com/NVlabs/GR00T-WholeBodyControl",
            "commit": UPSTREAM_COMMIT,
            "mjcf": "gear_sonic/data/assets/robot_description/mjcf/g1_29dof_rev_1_0.xml",
        },
        "license": "Apache-2.0",
        "contains_bones_seed": False,
        "sequence_count": len(records),
        "splits": {
            split: [record["id"] for record in records if record["split"] == split]
            for split in sorted({record["split"] for record in records})
        },
        "sequences": records,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(manifest, indent=2) + "\n")
    split_dir = manifest_path.parent.parent / "splits"
    split_dir.mkdir(parents=True, exist_ok=True)
    for split, identifiers in manifest["splits"].items():
        with (split_dir / f"{split}.txt").open("w", encoding="utf-8", newline="\n") as stream:
            stream.write("\n".join(identifiers) + "\n")
    return manifest
