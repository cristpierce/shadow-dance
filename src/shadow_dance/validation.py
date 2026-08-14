"""Deterministic QA for Shadow Dance motion-library artifacts."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import joblib
import mujoco
import numpy as np

from .motion import JOINT_NAMES, sha256_file

# Isaac Lab simulation velocity limits from gear_sonic/envs/manager_env/robots/g1.py.
VELOCITY_LIMITS_RAD_S = np.asarray(
    [
        20,
        20,
        32,
        20,
        37,
        37,
        20,
        20,
        32,
        20,
        37,
        37,
        32,
        37,
        37,
        37,
        37,
        37,
        37,
        37,
        22,
        22,
        37,
        37,
        37,
        37,
        37,
        22,
        22,
    ],
    dtype=np.float64,
)

REQUIRED_KEYS = {
    "root_trans_offset",
    "pose_aa",
    "dof",
    "root_rot",
    "smpl_joints",
    "fps",
}

# Four collision/contact points per foot from the pinned G1 MJCF.
SOLE_POINTS_LOCAL = np.asarray(
    [
        [-0.05, 0.025, -0.03],
        [-0.05, -0.025, -0.03],
        [0.12, 0.03, -0.03],
        [0.12, -0.03, -0.03],
    ],
    dtype=np.float64,
)


def _convex_hull(points: np.ndarray) -> np.ndarray:
    unique = sorted({(float(x), float(y)) for x, y in points})
    if len(unique) <= 1:
        return np.asarray(unique)

    def cross(origin: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> float:
        return (a[0] - origin[0]) * (b[1] - origin[1]) - (a[1] - origin[1]) * (b[0] - origin[0])

    lower: list[tuple[float, float]] = []
    for point in unique:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)
    upper: list[tuple[float, float]] = []
    for point in reversed(unique):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)
    return np.asarray(lower[:-1] + upper[:-1], dtype=np.float64)


def _signed_polygon_margin(point: np.ndarray, polygon: np.ndarray) -> float:
    if len(polygon) < 3:
        return float("nan")
    margins = []
    for index in range(len(polygon)):
        start = polygon[index]
        end = polygon[(index + 1) % len(polygon)]
        edge = end - start
        relative = point - start
        signed_area = edge[0] * relative[1] - edge[1] * relative[0]
        margins.append(signed_area / np.linalg.norm(edge))
    return float(min(margins))


class MotionValidator:
    """Validate schema, kinematics, limits, support geometry, and skill semantics."""

    def __init__(self, mjcf_path: Path):
        self.mjcf_path = Path(mjcf_path)
        self.model = mujoco.MjModel.from_xml_path(str(self.mjcf_path))
        self.data = mujoco.MjData(self.model)
        self.joint_ids = np.asarray(
            [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, name) for name in JOINT_NAMES]
        )
        self.qpos_addr = self.model.jnt_qposadr[self.joint_ids]
        self.lower = self.model.jnt_range[self.joint_ids, 0]
        self.upper = self.model.jnt_range[self.joint_ids, 1]
        self.pelvis_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "pelvis")
        self.foot_body_ids = [
            mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, f"{side}_ankle_roll_link")
            for side in ("left", "right")
        ]

    def _set_frame(self, entry: dict[str, Any], frame: int) -> None:
        self.data.qpos[:] = 0.0
        self.data.qpos[:3] = entry["root_trans_offset"][frame]
        quat_xyzw = np.asarray(entry["root_rot"][frame])
        self.data.qpos[3:7] = quat_xyzw[[3, 0, 1, 2]]
        self.data.qpos[self.qpos_addr] = entry["dof"][frame]
        mujoco.mj_forward(self.model, self.data)

    def validate_entry(self, motion_id: str, entry: dict[str, Any]) -> dict[str, Any]:
        errors: list[str] = []
        warnings: list[str] = []
        missing = sorted(REQUIRED_KEYS - set(entry))
        if missing:
            return {"id": motion_id, "pass": False, "errors": [f"missing keys: {missing}"]}

        dof = np.asarray(entry["dof"])
        root = np.asarray(entry["root_trans_offset"])
        pose_aa = np.asarray(entry["pose_aa"])
        root_rot = np.asarray(entry["root_rot"])
        smpl = np.asarray(entry["smpl_joints"])
        fps = int(entry["fps"])
        frames = len(dof)

        expected_shapes = {
            "dof": (frames, 29),
            "root_trans_offset": (frames, 3),
            "pose_aa": (frames, 30, 3),
            "root_rot": (frames, 4),
            "smpl_joints": (frames, 24, 3),
        }
        actual = {
            "dof": dof.shape,
            "root_trans_offset": root.shape,
            "pose_aa": pose_aa.shape,
            "root_rot": root_rot.shape,
            "smpl_joints": smpl.shape,
        }
        for name, expected in expected_shapes.items():
            if actual[name] != expected:
                errors.append(f"{name} shape {actual[name]} != {expected}")
        if errors:
            return {"id": motion_id, "pass": False, "errors": errors}
        if fps != 50:
            errors.append(f"fps is {fps}; SONIC target is 50")
        if frames / fps < 3.0:
            errors.append("motion is shorter than 3 seconds")
        finite_arrays = (
            ("dof", dof),
            ("root", root),
            ("pose_aa", pose_aa),
            ("root_rot", root_rot),
        )
        for name, values in finite_arrays:
            if not np.isfinite(values).all():
                errors.append(f"{name} contains non-finite values")

        quat_norm_error = float(np.max(np.abs(np.linalg.norm(root_rot, axis=1) - 1.0)))
        if quat_norm_error > 1e-4:
            errors.append(f"root quaternion norm error is {quat_norm_error:.3g}")

        lower_violation = np.maximum(self.lower[None, :] - dof, 0.0)
        upper_violation = np.maximum(dof - self.upper[None, :], 0.0)
        max_limit_violation = float(max(lower_violation.max(), upper_violation.max()))
        if max_limit_violation > 1e-6:
            errors.append(f"joint-limit violation {max_limit_violation:.6f} rad")
        distances = np.minimum(dof - self.lower[None, :], self.upper[None, :] - dof)
        min_joint_margin = float(np.min(distances))

        dt = 1.0 / fps
        velocity = np.gradient(dof, dt, axis=0, edge_order=2)
        acceleration = np.gradient(velocity, dt, axis=0, edge_order=2)
        max_velocity_ratio = float(np.max(np.abs(velocity) / VELOCITY_LIMITS_RAD_S[None, :]))
        if max_velocity_ratio > 1.0:
            errors.append(f"joint velocity reaches {max_velocity_ratio:.3f}x simulation limit")

        foot_centers = np.zeros((frames, 2, 3), dtype=np.float64)
        foot_points = np.zeros((frames, 2, 4, 3), dtype=np.float64)
        com = np.zeros((frames, 3), dtype=np.float64)
        support_margin = np.full(frames, np.nan, dtype=np.float64)
        planted_count = np.zeros(frames, dtype=np.int32)
        self_contacts = np.zeros(frames, dtype=np.int32)
        for frame in range(frames):
            self._set_frame(entry, frame)
            com[frame] = self.data.subtree_com[self.pelvis_id]
            planted_points = []
            for foot, body_id in enumerate(self.foot_body_ids):
                position = self.data.xpos[body_id]
                rotation = self.data.xmat[body_id].reshape(3, 3)
                points = position[None, :] + SOLE_POINTS_LOCAL @ rotation.T
                foot_points[frame, foot] = points
                foot_centers[frame, foot] = points.mean(axis=0)
                if float(np.max(points[:, 2])) <= 0.018:
                    planted_points.extend(points[:, :2])
                    planted_count[frame] += 1
            if len(planted_points) >= 4:
                support_margin[frame] = _signed_polygon_margin(
                    com[frame, :2], _convex_hull(np.asarray(planted_points))
                )
            count = 0
            for contact_index in range(self.data.ncon):
                contact = self.data.contact[contact_index]
                body_a = self.model.geom_bodyid[contact.geom1]
                body_b = self.model.geom_bodyid[contact.geom2]
                if body_a != 0 and body_b != 0 and body_a != body_b:
                    count += 1
            self_contacts[frame] = count

        min_foot_height = float(foot_points[..., 2].min())
        if min_foot_height < -0.008:
            errors.append(f"foot penetrates floor by {-min_foot_height * 1000:.1f} mm")
        max_foot_height = float(foot_points[..., 2].max())
        foot_velocity = np.gradient(foot_centers, dt, axis=0, edge_order=2)
        planted = foot_centers[..., 2] < 0.018
        planted_speed = np.linalg.norm(foot_velocity[..., :2], axis=-1)[planted]
        p95_planted_speed = (
            float(np.percentile(planted_speed, 95)) if len(planted_speed) else math.nan
        )
        if p95_planted_speed > 0.08:
            warnings.append(f"p95 planted-foot speed is {p95_planted_speed:.3f} m/s")

        finite_margins = support_margin[np.isfinite(support_margin)]
        min_support_margin = float(np.min(finite_margins)) if len(finite_margins) else math.nan
        min_support_index = int(np.nanargmin(support_margin)) if len(finite_margins) else -1
        two_foot_margins = support_margin[(planted_count == 2) & np.isfinite(support_margin)]
        min_two_foot_margin = float(np.min(two_foot_margins)) if len(two_foot_margins) else math.nan
        deepest = root[:, 2] <= root[:, 2].min() + 0.003
        deepest_margins = support_margin[deepest & np.isfinite(support_margin)]
        min_deepest_margin = float(np.min(deepest_margins)) if len(deepest_margins) else math.nan
        if np.isfinite(min_support_margin) and min_support_margin < -0.03:
            warnings.append(
                f"dynamic-step COM leaves instantaneous support by {-min_support_margin:.3f} m"
            )
        if np.isfinite(min_deepest_margin) and min_deepest_margin < -0.01:
            errors.append(f"deepest hold COM leaves support polygon by {-min_deepest_margin:.3f} m")
        if int(self_contacts.max()) > 0:
            warnings.append(f"MuJoCo reports up to {int(self_contacts.max())} self contacts")

        endpoint_rms = float(np.sqrt(np.mean((dof[-1] - dof[0]) ** 2)))
        pelvis_drop = float(root[0, 2] - root[:, 2].min())
        waist_roll_peak = float(np.max(np.abs(dof[:, 13])))
        foot_excursion = float(np.max(np.linalg.norm(foot_centers - foot_centers[0:1], axis=-1)))
        is_hero = motion_id.startswith("shadow_dip")
        if is_hero:
            if pelvis_drop < 0.075:
                errors.append(f"hero pelvis drop too small: {pelvis_drop:.3f} m")
            if waist_roll_peak < 0.20:
                errors.append(f"hero waist roll too small: {waist_roll_peak:.3f} rad")
            if foot_excursion < 0.07:
                errors.append(f"hero step excursion too small: {foot_excursion:.3f} m")
            if endpoint_rms > 0.05:
                errors.append(
                    f"hero does not settle near start: endpoint RMS {endpoint_rms:.3f} rad"
                )

        return {
            "id": motion_id,
            "pass": not errors,
            "errors": errors,
            "warnings": warnings,
            "frames": frames,
            "duration_s": round((frames - 1) / fps, 3),
            "fps": fps,
            "metrics": {
                "root_quaternion_max_norm_error": quat_norm_error,
                "joint_limit_max_violation_rad": max_limit_violation,
                "joint_limit_min_margin_rad": min_joint_margin,
                "joint_velocity_max_ratio": max_velocity_ratio,
                "joint_acceleration_peak_rad_s2": float(np.max(np.abs(acceleration))),
                "pelvis_drop_m": pelvis_drop,
                "waist_roll_peak_rad": waist_roll_peak,
                "foot_excursion_m": foot_excursion,
                "foot_height_max_m": max_foot_height,
                "floor_penetration_max_m": max(0.0, -min_foot_height),
                "planted_foot_speed_p95_m_s": p95_planted_speed,
                "quasistatic_support_margin_min_m": min_support_margin,
                "quasistatic_support_margin_min_time_s": (
                    min_support_index / fps if min_support_index >= 0 else None
                ),
                "support_feet_at_minimum": (
                    int(planted_count[min_support_index]) if min_support_index >= 0 else 0
                ),
                "two_foot_support_margin_min_m": min_two_foot_margin,
                "deepest_hold_support_margin_min_m": min_deepest_margin,
                "self_contact_count_max": int(self_contacts.max()),
                "endpoint_joint_rms_rad": endpoint_rms,
            },
        }


def load_single_entry(path: Path) -> tuple[str, dict[str, Any]]:
    data = joblib.load(path)
    if not isinstance(data, dict) or len(data) != 1:
        raise ValueError(f"{path} must contain exactly one motion dictionary entry")
    motion_id = next(iter(data))
    return motion_id, data[motion_id]


def validate_dataset(
    dataset_dir: Path, mjcf_path: Path, report_path: Path, manifest_path: Path | None = None
) -> dict[str, Any]:
    validator = MotionValidator(mjcf_path)
    pkl_files = sorted(Path(dataset_dir).glob("**/*.pkl"))
    if not pkl_files:
        raise FileNotFoundError(f"No PKL files found below {dataset_dir}")
    results = []
    for path in pkl_files:
        motion_id, entry = load_single_entry(path)
        result = validator.validate_entry(motion_id, entry)
        result["file"] = str(path.relative_to(dataset_dir)).replace("\\", "/")
        result["sha256"] = sha256_file(path)
        results.append(result)

    manifest_checks: dict[str, Any] = {"checked": False}
    if manifest_path:
        manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        expected = {record["id"] for record in manifest["sequences"]}
        actual = {result["id"] for result in results}
        records_by_id = {record["id"]: record for record in manifest["sequences"]}
        artifact_failures: list[str] = []
        for result in results:
            record = records_by_id.get(result["id"])
            if record is None:
                continue
            checks = {
                "motion_path_matches": record["files"]["motion_lib"] == result["file"],
                "motion_sha256_matches": (record["files"]["motion_lib_sha256"] == result["sha256"]),
                "ik_position_within_8mm": record["ik_max_position_error_m"] <= 0.008,
                "ik_orientation_within_5deg": (record["ik_max_orientation_error_deg"] <= 5.0),
            }
            csv_path = Path(dataset_dir) / record["files"]["source_csv"]
            checks["source_csv_exists"] = csv_path.is_file()
            checks["source_csv_sha256_matches"] = (
                csv_path.is_file() and sha256_file(csv_path) == record["files"]["source_csv_sha256"]
            )
            result["manifest_checks"] = checks
            failed_checks = [name for name, passed in checks.items() if not passed]
            if failed_checks:
                result["errors"].append(f"manifest/artifact checks failed: {failed_checks}")
                result["pass"] = False
                artifact_failures.append(result["id"])
        manifest_checks = {
            "checked": True,
            "missing_from_files": sorted(expected - actual),
            "missing_from_manifest": sorted(actual - expected),
            "id_set_matches": expected == actual,
            "artifact_failures": artifact_failures,
            "artifact_checks_pass": not artifact_failures,
        }

    report = {
        "schema_version": 1,
        "dataset_dir": Path(dataset_dir).as_posix(),
        "mjcf": "gear_sonic/data/assets/robot_description/mjcf/g1_29dof_rev_1_0.xml",
        "sequence_count": len(results),
        "passed": sum(bool(result["pass"]) for result in results),
        "failed": sum(not result["pass"] for result in results),
        "warning_count": sum(len(result.get("warnings", [])) for result in results),
        "overall_pass": all(result["pass"] for result in results)
        and (
            not manifest_checks["checked"]
            or (manifest_checks["id_set_matches"] and manifest_checks["artifact_checks_pass"])
        ),
        "manifest": manifest_checks,
        "sequences": results,
    }
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(report, indent=2, allow_nan=False) + "\n")
    return report
