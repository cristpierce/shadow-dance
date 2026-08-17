"""Account-free stock/adapted SONIC MuJoCo deployment probe.

This intentionally produces a *proxy* deployment result, not an Isaac/WBT-Bench
result.  It follows NVIDIA's public C++ deployment observation ordering, action
mapping, PD gains, and 50 Hz control cadence while executing the released ONNX
encoder and decoder with ONNX Runtime.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import deque
from pathlib import Path

import imageio.v2 as imageio
import joblib
import mujoco
import numpy as np
import onnxruntime as ort
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial.transform import Rotation

DEFAULT_ANGLES = np.asarray(
    [
        -0.312, 0.0, 0.0, 0.669, -0.363, 0.0,
        -0.312, 0.0, 0.0, 0.669, -0.363, 0.0,
        0.0, 0.0, 0.0,
        0.2, 0.2, 0.0, 0.6, 0.0, 0.0, 0.0,
        0.2, -0.2, 0.0, 0.6, 0.0, 0.0, 0.0,
    ],
    dtype=np.float64,
)

# For each MuJoCo/hardware-order joint, select the corresponding IsaacLab action.
ISAACLAB_TO_MUJOCO = np.asarray(
    [0, 3, 6, 9, 13, 17, 1, 4, 7, 10, 14, 18, 2, 5, 8,
     11, 15, 19, 21, 23, 25, 27, 12, 16, 20, 22, 24, 26, 28],
    dtype=np.int64,
)

# For each IsaacLab-order state element, select the MuJoCo/hardware-order joint.
MUJOCO_TO_ISAACLAB = np.asarray(
    [0, 6, 12, 1, 7, 13, 2, 8, 14, 3, 9, 15, 22, 4, 10,
     16, 23, 5, 11, 17, 24, 18, 25, 19, 26, 20, 27, 21, 28],
    dtype=np.int64,
)

ARMATURE_5020 = 0.003609725
ARMATURE_7520_14 = 0.010177520
ARMATURE_7520_22 = 0.025101925
ARMATURE_4010 = 0.00425
NATURAL_FREQ = 10.0 * 2.0 * np.pi
DAMPING_RATIO = 2.0


def stiffness(armature: float) -> float:
    return armature * NATURAL_FREQ**2


def damping(armature: float) -> float:
    return 2.0 * DAMPING_RATIO * armature * NATURAL_FREQ


S_5020 = stiffness(ARMATURE_5020)
S_7520_14 = stiffness(ARMATURE_7520_14)
S_7520_22 = stiffness(ARMATURE_7520_22)
S_4010 = stiffness(ARMATURE_4010)
D_5020 = damping(ARMATURE_5020)
D_7520_14 = damping(ARMATURE_7520_14)
D_7520_22 = damping(ARMATURE_7520_22)
D_4010 = damping(ARMATURE_4010)

KPS = np.asarray(
    [
        S_7520_22, S_7520_22, S_7520_14, S_7520_22, 2*S_5020, 2*S_5020,
        S_7520_22, S_7520_22, S_7520_14, S_7520_22, 2*S_5020, 2*S_5020,
        S_7520_14, 2*S_5020, 2*S_5020,
        S_5020, S_5020, S_5020, S_5020, S_5020, S_4010, S_4010,
        S_5020, S_5020, S_5020, S_5020, S_5020, S_4010, S_4010,
    ],
    dtype=np.float64,
)
KDS = np.asarray(
    [
        D_7520_22, D_7520_22, D_7520_14, D_7520_22, 2*D_5020, 2*D_5020,
        D_7520_22, D_7520_22, D_7520_14, D_7520_22, 2*D_5020, 2*D_5020,
        D_7520_14, 2*D_5020, 2*D_5020,
        D_5020, D_5020, D_5020, D_5020, D_5020, D_4010, D_4010,
        D_5020, D_5020, D_5020, D_5020, D_5020, D_4010, D_4010,
    ],
    dtype=np.float64,
)
ACTION_SCALE = np.asarray(
    [
        0.25*139/S_7520_22, 0.25*139/S_7520_22, 0.25*88/S_7520_14,
        0.25*139/S_7520_22, 0.25*25/S_5020, 0.25*25/S_5020,
        0.25*139/S_7520_22, 0.25*139/S_7520_22, 0.25*88/S_7520_14,
        0.25*139/S_7520_22, 0.25*25/S_5020, 0.25*25/S_5020,
        0.25*88/S_7520_14, 0.25*25/S_5020, 0.25*25/S_5020,
        0.25*25/S_5020, 0.25*25/S_5020, 0.25*25/S_5020, 0.25*25/S_5020,
        0.25*25/S_5020, 0.25*5/S_4010, 0.25*5/S_4010,
        0.25*25/S_5020, 0.25*25/S_5020, 0.25*25/S_5020, 0.25*25/S_5020,
        0.25*25/S_5020, 0.25*5/S_4010, 0.25*5/S_4010,
    ],
    dtype=np.float64,
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def quat_mul_wxyz(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return np.asarray(
        [
            aw*bw - ax*bx - ay*by - az*bz,
            aw*bx + ax*bw + ay*bz - az*by,
            aw*by - ax*bz + ay*bw + az*bx,
            aw*bz + ax*by - ay*bx + az*bw,
        ],
        dtype=np.float64,
    )


def quat_conj_wxyz(q: np.ndarray) -> np.ndarray:
    return np.asarray([q[0], -q[1], -q[2], -q[3]], dtype=np.float64)


def heading_wxyz(q: np.ndarray) -> np.ndarray:
    yaw = Rotation.from_quat(q[[1, 2, 3, 0]]).as_euler("xyz")[2]
    xyzw = Rotation.from_euler("z", yaw).as_quat()
    return xyzw[[3, 0, 1, 2]]


def quat_to_6d_wxyz(q: np.ndarray) -> np.ndarray:
    matrix = Rotation.from_quat(q[[1, 2, 3, 0]]).as_matrix()
    return matrix[:, :2].reshape(-1)


def rotate_inverse_wxyz(q: np.ndarray, vector: np.ndarray) -> np.ndarray:
    return Rotation.from_quat(q[[1, 2, 3, 0]]).inv().apply(vector)


def zero_state() -> dict[str, np.ndarray]:
    return {
        "base_ang_vel": np.zeros(3),
        "body_q": np.zeros(29),
        "body_dq": np.zeros(29),
        "last_action": np.zeros(29),
        "gravity": np.zeros(3),
    }


def get_state(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    qpos_addr: np.ndarray,
    dof_addr: np.ndarray,
    gyro_addr: int,
    last_action: np.ndarray,
) -> dict[str, np.ndarray]:
    q_mujoco = np.asarray(data.qpos[qpos_addr]).copy()
    dq_mujoco = np.asarray(data.qvel[dof_addr]).copy()
    base_quat = np.asarray(data.qpos[3:7]).copy()
    return {
        "base_ang_vel": np.asarray(data.sensordata[gyro_addr:gyro_addr+3]).copy(),
        "body_q": q_mujoco[MUJOCO_TO_ISAACLAB] - DEFAULT_ANGLES[MUJOCO_TO_ISAACLAB],
        "body_dq": dq_mujoco[MUJOCO_TO_ISAACLAB],
        "last_action": last_action.copy(),
        "gravity": rotate_inverse_wxyz(base_quat, np.asarray([0.0, 0.0, -1.0])),
    }


def build_encoder_input(
    frame: int,
    dof: np.ndarray,
    dof_vel: np.ndarray,
    root_wxyz: np.ndarray,
    base_wxyz: np.ndarray,
    apply_delta_heading: np.ndarray,
) -> np.ndarray:
    future = np.minimum(frame + np.arange(10) * 5, len(dof) - 1)
    anchors = []
    for index in future:
        new_ref = quat_mul_wxyz(apply_delta_heading, root_wxyz[index])
        relative = quat_mul_wxyz(quat_conj_wxyz(base_wxyz), new_ref)
        anchors.append(quat_to_6d_wxyz(relative))
    parts = [
        np.zeros(4),                         # encoder_mode_4; G1 mode ID is 0
        dof[future].reshape(-1),             # 290
        dof_vel[future].reshape(-1),         # 290
        np.zeros(10),                        # unused G1-mode root-z horizon
        np.zeros(1),                         # unused root-z
        np.zeros(6),                         # unused single anchor
        np.asarray(anchors).reshape(-1),     # 60, required G1 anchor horizon
        np.zeros(120),                       # unused teleop lower-body positions
        np.zeros(120),                       # unused teleop lower-body velocities
        np.zeros(9),                         # unused VR positions
        np.zeros(12),                        # unused VR orientations
        np.zeros(720),                       # unused SMPL joints
        np.zeros(60),                        # unused SMPL anchors
        np.zeros(60),                        # unused SMPL wrist positions
    ]
    result = np.concatenate(parts).astype(np.float32)[None, :]
    assert result.shape == (1, 1762)
    return result


def build_decoder_input(token: np.ndarray, history: deque[dict[str, np.ndarray]]) -> np.ndarray:
    padded = [zero_state() for _ in range(max(0, 10 - len(history)))] + list(history)[-10:]
    parts = [
        token.reshape(-1),
        np.concatenate([state["base_ang_vel"] for state in padded]),
        np.concatenate([state["body_q"] for state in padded]),
        np.concatenate([state["body_dq"] for state in padded]),
        np.concatenate([state["last_action"] for state in padded]),
        np.concatenate([state["gravity"] for state in padded]),
    ]
    result = np.concatenate(parts).astype(np.float32)[None, :]
    assert result.shape == (1, 994)
    return result


def local_body_positions(data: mujoco.MjData, body_ids: np.ndarray) -> np.ndarray:
    pelvis = np.asarray(data.xpos[body_ids[0]])
    root_q = np.asarray(data.xquat[body_ids[0]])
    return Rotation.from_quat(root_q[[1, 2, 3, 0]]).inv().apply(
        np.asarray(data.xpos[body_ids]) - pelvis
    )


def load_entry(path: Path) -> tuple[str, dict[str, object]]:
    payload = joblib.load(path)
    if not isinstance(payload, dict) or len(payload) != 1:
        raise ValueError(f"Expected one motion in {path}")
    return next(iter(payload.items()))


def run_motion(
    motion_path: Path,
    mjcf_path: Path,
    encoder_path: Path,
    decoder_path: Path,
    video_path: Path | None,
    motion_order: str,
    action_gain: float | np.ndarray = 1.0,
    action_bias: float | np.ndarray = 0.0,
) -> dict[str, object]:
    motion_id, entry = load_entry(motion_path)
    fps = int(entry["fps"])
    if fps != 50:
        raise ValueError(f"Deployment contract requires 50 Hz, got {fps}")
    raw_dof = np.asarray(entry["dof"], dtype=np.float64)
    if motion_order == "mujoco":
        dof_mujoco = raw_dof
        dof_encoder = raw_dof[:, MUJOCO_TO_ISAACLAB]
    elif motion_order == "isaaclab":
        dof_encoder = raw_dof
        dof_mujoco = raw_dof[:, ISAACLAB_TO_MUJOCO]
    else:
        raise ValueError(f"Unsupported motion order: {motion_order}")
    dof_encoder_vel = np.gradient(dof_encoder, 1.0/fps, axis=0, edge_order=2)
    root_xyzw = np.asarray(entry["root_rot"], dtype=np.float64)
    root_wxyz = root_xyzw[:, [3, 0, 1, 2]]
    root_pos = np.asarray(entry["root_trans_offset"], dtype=np.float64)
    gain = np.broadcast_to(np.asarray(action_gain, dtype=np.float64), (29,)).copy()
    bias = np.broadcast_to(np.asarray(action_bias, dtype=np.float64), (29,)).copy()
    if not np.isfinite(gain).all() or not np.isfinite(bias).all():
        raise ValueError("Action adapter contains non-finite values")

    model = mujoco.MjModel.from_xml_path(str(mjcf_path))
    model.opt.timestep = 0.005
    data = mujoco.MjData(model)
    reference = mujoco.MjData(model)
    joint_ids = np.asarray([
        mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
        for name in (
            "left_hip_pitch_joint", "left_hip_roll_joint", "left_hip_yaw_joint",
            "left_knee_joint", "left_ankle_pitch_joint", "left_ankle_roll_joint",
            "right_hip_pitch_joint", "right_hip_roll_joint", "right_hip_yaw_joint",
            "right_knee_joint", "right_ankle_pitch_joint", "right_ankle_roll_joint",
            "waist_yaw_joint", "waist_roll_joint", "waist_pitch_joint",
            "left_shoulder_pitch_joint", "left_shoulder_roll_joint",
            "left_shoulder_yaw_joint", "left_elbow_joint", "left_wrist_roll_joint",
            "left_wrist_pitch_joint", "left_wrist_yaw_joint",
            "right_shoulder_pitch_joint", "right_shoulder_roll_joint",
            "right_shoulder_yaw_joint", "right_elbow_joint", "right_wrist_roll_joint",
            "right_wrist_pitch_joint", "right_wrist_yaw_joint",
        )
    ])
    qpos_addr = model.jnt_qposadr[joint_ids]
    dof_addr = model.jnt_dofadr[joint_ids]
    body_ids = np.concatenate((
        [mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "pelvis")],
        model.jnt_bodyid[joint_ids],
    ))
    gyro_id = -1
    for sensor_name in ("imu-pelvis-angular-velocity", "imu_gyro"):
        gyro_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SENSOR, sensor_name)
        if gyro_id >= 0:
            break
    if gyro_id < 0:
        raise ValueError("Deployment MJCF has no supported pelvis gyroscope sensor")
    gyro_addr = int(model.sensor_adr[gyro_id])
    torque_limits = np.abs(model.jnt_actfrcrange[joint_ids, 1])

    data.qpos[:3] = root_pos[0]
    data.qpos[3:7] = root_wxyz[0]
    data.qpos[qpos_addr] = dof_mujoco[0]
    data.qvel[:] = 0.0
    mujoco.mj_forward(model, data)

    encoder = ort.InferenceSession(str(encoder_path), providers=["CPUExecutionProvider"])
    decoder = ort.InferenceSession(str(decoder_path), providers=["CPUExecutionProvider"])
    apply_delta_heading = quat_mul_wxyz(
        heading_wxyz(np.asarray(data.qpos[3:7])),
        quat_conj_wxyz(heading_wxyz(root_wxyz[0])),
    )

    last_action = np.zeros(29, dtype=np.float64)
    history: deque[dict[str, np.ndarray]] = deque(maxlen=10)
    initial_state = get_state(model, data, qpos_addr, dof_addr, gyro_addr, last_action)
    for _ in range(10):
        history.append({key: value.copy() for key, value in initial_state.items()})

    local_errors_mm: list[float] = []
    global_errors_mm: list[float] = []
    root_errors_mm: list[float] = []
    joint_errors_deg: list[float] = []
    joint_error_vectors_rad: list[np.ndarray] = []
    stock_actions: list[np.ndarray] = []
    desired_actions: list[np.ndarray] = []
    pelvis_heights: list[float] = []
    action_abs_max = 0.0
    writer = None
    renderer = None
    camera = None
    if video_path is not None:
        video_path.parent.mkdir(parents=True, exist_ok=True)
        writer = imageio.get_writer(video_path, fps=fps, codec="libx264", quality=8)
        renderer = mujoco.Renderer(model, height=480, width=480)
        camera = mujoco.MjvCamera()
        camera.lookat[:] = [0.0, 0.0, 0.72]
        camera.distance = 2.55
        camera.azimuth = 132
        camera.elevation = -9

    try:
        for frame in range(len(dof_mujoco)):
            state = get_state(model, data, qpos_addr, dof_addr, gyro_addr, last_action)
            history.append(state)
            enc_obs = build_encoder_input(
                frame,
                dof_encoder,
                dof_encoder_vel,
                root_wxyz,
                np.asarray(data.qpos[3:7]),
                apply_delta_heading,
            )
            token = encoder.run(None, {"obs_dict": enc_obs})[0]
            dec_obs = build_decoder_input(token, history)
            stock_action = decoder.run(None, {"obs_dict": dec_obs})[0][0].astype(np.float64)
            if not np.isfinite(stock_action).all():
                raise RuntimeError(f"Non-finite stock action at frame {frame}")
            action = stock_action * gain + bias
            desired_mujoco = (dof_mujoco[frame] - DEFAULT_ANGLES) / ACTION_SCALE
            desired_isaaclab = np.empty(29, dtype=np.float64)
            desired_isaaclab[ISAACLAB_TO_MUJOCO] = desired_mujoco
            stock_actions.append(stock_action.copy())
            desired_actions.append(desired_isaaclab)
            action_abs_max = max(action_abs_max, float(np.max(np.abs(action))))
            target = DEFAULT_ANGLES + action[ISAACLAB_TO_MUJOCO] * ACTION_SCALE
            last_action = action

            for _ in range(4):
                q = np.asarray(data.qpos[qpos_addr])
                dq = np.asarray(data.qvel[dof_addr])
                torque = KPS*(target-q) - KDS*dq
                data.ctrl[:] = np.clip(torque, -torque_limits, torque_limits)
                mujoco.mj_step(model, data)

            reference.qpos[:] = 0.0
            reference.qpos[:3] = root_pos[frame]
            reference.qpos[3:7] = root_wxyz[frame]
            reference.qpos[qpos_addr] = dof_mujoco[frame]
            mujoco.mj_forward(model, reference)

            sim_local = local_body_positions(data, body_ids)
            ref_local = local_body_positions(reference, body_ids)
            local_errors_mm.append(float(np.linalg.norm(sim_local-ref_local, axis=1).mean()*1000))
            global_errors_mm.append(
                float(
                    np.linalg.norm(
                        np.asarray(data.xpos[body_ids]) - np.asarray(reference.xpos[body_ids]),
                        axis=1,
                    ).mean()
                    * 1000
                )
            )
            root_errors_mm.append(float(np.linalg.norm(data.qpos[:3]-root_pos[frame])*1000))
            joint_errors_deg.append(
                float(
                    np.degrees(
                        np.sqrt(np.mean((data.qpos[qpos_addr]-dof_mujoco[frame])**2))
                    )
                )
            )
            joint_error_vectors_rad.append(
                np.asarray(data.qpos[qpos_addr] - dof_mujoco[frame]).copy()
            )
            pelvis_heights.append(float(data.qpos[2]))

            if writer is not None and renderer is not None and camera is not None:
                renderer.update_scene(reference, camera=camera)
                target_pixels = renderer.render().copy()
                renderer.update_scene(data, camera=camera)
                stock_pixels = renderer.render().copy()
                canvas = Image.fromarray(np.concatenate((target_pixels, stock_pixels), axis=1))
                draw = ImageDraw.Draw(canvas)
                font = ImageFont.load_default(size=20)
                small = ImageFont.load_default(size=16)
                draw.rectangle((0, 0, 960, 72), fill=(8, 12, 20))
                draw.text((18, 10), "KINEMATIC TARGET", fill=(255, 210, 64), font=font)
                draw.text((500, 10), "STOCK SONIC", fill=(100, 210, 255), font=font)
                draw.text(
                    (18, 42),
                    "MuJoCo deployment proxy | not Isaac/WBT-Bench | no fine-tuned claim",
                    fill="white",
                    font=small,
                )
                writer.append_data(np.asarray(canvas))
    finally:
        if writer is not None:
            writer.close()
        if renderer is not None:
            renderer.close()

    local = np.asarray(local_errors_mm)
    global_error = np.asarray(global_errors_mm)
    root = np.asarray(root_errors_mm)
    joint = np.asarray(joint_errors_deg)
    joint_vectors = np.asarray(joint_error_vectors_rad)
    stock_action_matrix = np.asarray(stock_actions)
    desired_action_matrix = np.asarray(desired_actions)
    pelvis = np.asarray(pelvis_heights)
    return {
        "format": "shadow_dance_stock_mujoco_proxy_v1",
        "motion_id": motion_id,
        "motion_path": motion_path.as_posix(),
        "motion_sha256": sha256(motion_path),
        "frames": int(len(dof_mujoco)),
        "fps": fps,
        "source_motion_joint_order": motion_order,
        "encoder_motion_joint_order": "isaaclab",
        "simulator_motion_joint_order": "mujoco",
        "model": "NVIDIA GEAR-SONIC default deployment encoder/decoder",
        "action_adapter": {
            "gain": gain.tolist(),
            "bias": bias.tolist(),
            "identity": bool(
                np.array_equal(gain, np.ones(29))
                and np.array_equal(bias, np.zeros(29))
            ),
        },
        "simulator": "MuJoCo 3.x; Python port of public deployment observation/action contract",
        "official_wbt_bench": False,
        "isaac_result": False,
        "proxy_limitations": [
            "This is not the organizer WBT-Bench package.",
            "This is not Isaac Lab evaluation and is not used as a final challenge score.",
            "CPU ONNX Runtime replaces the upstream TensorRT execution backend.",
            "The initial history is prefilled from the frozen first reference pose.",
        ],
        "metrics": {
            "mpjpe_local_mean_mm": float(local.mean()),
            "mpjpe_local_p95_mm": float(np.percentile(local, 95)),
            "mpjpe_global_mean_mm": float(global_error.mean()),
            "mpjpe_global_p95_mm": float(np.percentile(global_error, 95)),
            "root_position_mean_mm": float(root.mean()),
            "root_position_p95_mm": float(np.percentile(root, 95)),
            "joint_rmse_mean_deg": float(joint.mean()),
            "joint_rmse_p95_deg": float(np.percentile(joint, 95)),
            "per_joint_rmse_deg_mujoco_order": np.degrees(
                np.sqrt(np.mean(joint_vectors**2, axis=0))
            ).tolist(),
            "pelvis_height_min_m": float(pelvis.min()),
            "finite_action_abs_max": float(action_abs_max),
            "completed_without_fall": bool(pelvis.min() >= 0.35),
            "sonic_guide_local_mpjpe_under_30mm": bool(local.mean() < 30.0),
        },
        "adapter_fit_sufficient_statistics": {
            "frames": int(len(stock_action_matrix)),
            "sum_x": stock_action_matrix.sum(axis=0).tolist(),
            "sum_y": desired_action_matrix.sum(axis=0).tolist(),
            "sum_xx": (stock_action_matrix**2).sum(axis=0).tolist(),
            "sum_xy": (stock_action_matrix * desired_action_matrix).sum(axis=0).tolist(),
        },
        "artifacts": {
            "encoder": {"path": encoder_path.as_posix(), "sha256": sha256(encoder_path)},
            "decoder": {"path": decoder_path.as_posix(), "sha256": sha256(decoder_path)},
            "mjcf": {"path": mjcf_path.as_posix(), "sha256": sha256(mjcf_path)},
            "video": (
                {"path": video_path.as_posix(), "sha256": sha256(video_path)}
                if video_path is not None else None
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("motion", type=Path)
    parser.add_argument("--mjcf", type=Path, required=True)
    parser.add_argument("--encoder", type=Path, required=True)
    parser.add_argument("--decoder", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--video", type=Path)
    parser.add_argument("--motion-order", choices=("mujoco", "isaaclab"), default="mujoco")
    parser.add_argument("--action-gain", type=float, default=1.0)
    parser.add_argument("--action-bias", type=float, default=0.0)
    parser.add_argument("--adapter-json", type=Path)
    args = parser.parse_args()
    adapter = (
        json.loads(args.adapter_json.read_text(encoding="utf-8"))
        if args.adapter_json is not None
        else {"gain": args.action_gain, "bias": args.action_bias}
    )
    report = run_motion(
        args.motion,
        args.mjcf,
        args.encoder,
        args.decoder,
        args.video,
        args.motion_order,
        adapter["gain"],
        adapter["bias"],
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
