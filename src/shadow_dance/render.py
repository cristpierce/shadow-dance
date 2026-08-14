"""Render a clearly labelled kinematic-reference video with MuJoCo."""

from __future__ import annotations

from pathlib import Path

import imageio.v2 as imageio
import mujoco
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .motion import JOINT_NAMES
from .validation import load_single_entry


def _phase_at(time_s: float, phases: dict[str, list[float]] | None) -> str:
    if not phases:
        return "reference motion"
    for name, (start, end) in phases.items():
        if start <= time_s <= end:
            return name.replace("_", " ")
    return "settle"


def render_reference(
    motion_path: Path,
    mjcf_path: Path,
    output_path: Path,
    phases: dict[str, list[float]] | None = None,
    width: int = 640,
    height: int = 480,
) -> None:
    motion_id, entry = load_single_entry(motion_path)
    model = mujoco.MjModel.from_xml_path(str(mjcf_path))
    data = mujoco.MjData(model)
    joint_ids = [mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name) for name in JOINT_NAMES]
    qpos_addr = model.jnt_qposadr[joint_ids]
    camera = mujoco.MjvCamera()
    camera.lookat[:] = [0.0, 0.0, 0.72]
    camera.distance = 2.55
    camera.azimuth = 132
    camera.elevation = -9
    renderer = mujoco.Renderer(model, height=height, width=width)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    writer = imageio.get_writer(output_path, fps=int(entry["fps"]), codec="libx264", quality=8)
    try:
        for frame in range(len(entry["dof"])):
            data.qpos[:] = 0.0
            data.qpos[:3] = entry["root_trans_offset"][frame]
            xyzw = np.asarray(entry["root_rot"][frame])
            data.qpos[3:7] = xyzw[[3, 0, 1, 2]]
            data.qpos[qpos_addr] = entry["dof"][frame]
            mujoco.mj_forward(model, data)
            renderer.update_scene(data, camera=camera)
            pixels = renderer.render()
            image = Image.fromarray(pixels)
            draw = ImageDraw.Draw(image)
            font = ImageFont.load_default(size=22)
            small = ImageFont.load_default(size=18)
            draw.rectangle((0, 0, width, 78), fill=(8, 12, 20, 220))
            draw.text(
                (20, 12),
                "KINEMATIC REFERENCE | NOT POLICY OUTPUT",
                fill=(255, 210, 64),
                font=font,
            )
            phase = _phase_at(frame / int(entry["fps"]), phases)
            draw.text((20, 46), f"{motion_id}  |  {phase}", fill="white", font=small)
            writer.append_data(np.asarray(image))
    finally:
        writer.close()
        renderer.close()
