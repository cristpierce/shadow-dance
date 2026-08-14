"""Command-line entry points for dataset generation, QA, and reference rendering."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .motion import generate_dataset
from .render import render_reference
from .validation import validate_dataset


def _default_mjcf(sonic_root: Path) -> Path:
    return (
        sonic_root
        / "gear_sonic"
        / "data"
        / "assets"
        / "robot_description"
        / "mjcf"
        / "g1_29dof_rev_1_0.xml"
    )


def generate_main() -> None:
    parser = argparse.ArgumentParser(description="Generate Shadow Partner Dip motion data")
    parser.add_argument("--sonic-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/generated"))
    parser.add_argument("--manifest", type=Path, default=Path("data/manifests/shadow-dip-v1.json"))
    args = parser.parse_args()
    manifest = generate_dataset(args.output, _default_mjcf(args.sonic_root), args.manifest)
    print(f"Generated {manifest['sequence_count']} sequences at {args.output}")


def validate_main() -> None:
    parser = argparse.ArgumentParser(description="Validate Shadow Dance motion data")
    parser.add_argument("--sonic-root", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, default=Path("data/generated"))
    parser.add_argument("--manifest", type=Path, default=Path("data/manifests/shadow-dip-v1.json"))
    parser.add_argument("--report", type=Path, default=Path("results/reference-validation.json"))
    args = parser.parse_args()
    report = validate_dataset(
        args.dataset, _default_mjcf(args.sonic_root), args.report, args.manifest
    )
    summary_keys = ("sequence_count", "passed", "failed", "overall_pass")
    print(json.dumps({key: report[key] for key in summary_keys}, indent=2))
    if not report["overall_pass"]:
        raise SystemExit(1)


def render_main() -> None:
    parser = argparse.ArgumentParser(description="Render a labelled kinematic reference")
    parser.add_argument("motion", type=Path)
    parser.add_argument("--sonic-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("media/reference.mp4"))
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    phases = None
    if args.manifest:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        motion_id = args.motion.stem
        record = next(record for record in manifest["sequences"] if record["id"] == motion_id)
        phases = record["phase_windows_s"]
    render_reference(args.motion, _default_mjcf(args.sonic_root), args.output, phases)
    print(f"Rendered {args.output}")
