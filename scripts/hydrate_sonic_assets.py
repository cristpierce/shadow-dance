#!/usr/bin/env python3
"""Restore and attest the pinned G1 assets omitted from the SONIC runtime image.

The immutable NPA image intentionally checks out the upstream repository with Git LFS
smudging disabled so gated model weights are not redistributed. That also leaves the
public G1 visual meshes as LFS pointer stubs. SONIC's released training config loads
the G1 URDF and those meshes, so fetch only that public, pinned asset subtree before
starting Isaac.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

SOURCE_REPO = "https://github.com/NVlabs/GR00T-WholeBodyControl.git"
SOURCE_REVISION = "0a87181c9106d0e49293400714b157676e0ec664"
ASSET_ROOTS = (
    Path("gear_sonic/data/assets/robot_description/meshes/g1"),
    Path("gear_sonic/data/assets/robot_description/urdf/g1"),
)
EXPECTED_FILE_COUNT = 69
EXPECTED_TOTAL_BYTES = 68_378_071
EXPECTED_MANIFEST_SHA256 = "79fa6310cefeaf819c103e5c83c9c40c55ef71b28aace7bf9f8c116d4966d0c7"
EXPECTED_URDF_MESH_REFERENCES = 67
COMMAND_TIMEOUT_SECONDS = 300
LFS_POINTER_MAGIC = b"version https://git-lfs.github.com/spec/v1"


@dataclass(frozen=True)
class AssetIdentity:
    file_count: int
    total_bytes: int
    manifest_sha256: str
    pointer_files: tuple[str, ...]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def asset_files(root: Path) -> list[Path]:
    files = [
        path
        for relative_root in ASSET_ROOTS
        for path in (root / relative_root).rglob("*")
        if path.is_file()
    ]
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def identify_assets(root: Path) -> AssetIdentity:
    records: list[str] = []
    pointers: list[str] = []
    total_bytes = 0
    for path in asset_files(root):
        relative = path.relative_to(root).as_posix()
        size = path.stat().st_size
        total_bytes += size
        with path.open("rb") as handle:
            if handle.read(len(LFS_POINTER_MAGIC)) == LFS_POINTER_MAGIC:
                pointers.append(relative)
        records.append(f"{_sha256(path)}  {size}  {relative}")
    manifest = ("\n".join(records) + ("\n" if records else "")).encode()
    return AssetIdentity(
        file_count=len(records),
        total_bytes=total_bytes,
        manifest_sha256=hashlib.sha256(manifest).hexdigest(),
        pointer_files=tuple(pointers),
    )


def validate_assets(root: Path) -> AssetIdentity:
    identity = identify_assets(root)
    problems: list[str] = []
    if identity.pointer_files:
        problems.append(f"{len(identity.pointer_files)} Git LFS pointer files remain")
    if identity.file_count != EXPECTED_FILE_COUNT:
        problems.append(f"file count is {identity.file_count}, expected {EXPECTED_FILE_COUNT}")
    if identity.total_bytes != EXPECTED_TOTAL_BYTES:
        problems.append(f"total bytes are {identity.total_bytes}, expected {EXPECTED_TOTAL_BYTES}")
    if identity.manifest_sha256 != EXPECTED_MANIFEST_SHA256:
        problems.append(
            "canonical manifest SHA256 is "
            f"{identity.manifest_sha256}, expected {EXPECTED_MANIFEST_SHA256}"
        )

    urdf = root / ASSET_ROOTS[1] / "main.urdf"
    if urdf.is_file():
        marker = "package://robot_description/meshes/g1/"
        references = [
            value.split('"', 1)[0] for value in urdf.read_text(encoding="utf-8").split(marker)[1:]
        ]
        if len(references) != EXPECTED_URDF_MESH_REFERENCES:
            problems.append(
                f"URDF has {len(references)} G1 mesh references, "
                f"expected {EXPECTED_URDF_MESH_REFERENCES}"
            )
        mesh_names = {
            path.relative_to(root / ASSET_ROOTS[0]).as_posix()
            for path in (root / ASSET_ROOTS[0]).rglob("*")
            if path.is_file()
        }
        missing = sorted(reference for reference in set(references) if reference not in mesh_names)
        if missing:
            problems.append(f"URDF references missing meshes: {', '.join(missing)}")
    else:
        problems.append(f"missing URDF: {(ASSET_ROOTS[1] / 'main.urdf').as_posix()}")

    if problems:
        raise ValueError("; ".join(problems))
    return identity


def _run(command: list[str], *, cwd: Path, env: dict[str, str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=True,
        timeout=COMMAND_TIMEOUT_SECONDS,
    )


def checkout_assets(destination: Path) -> None:
    env = os.environ.copy()
    env.pop("GIT_LFS_SKIP_SMUDGE", None)
    env.pop("GIT_LFS_SKIP_DOWNLOAD_ERRORS", None)
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GCM_INTERACTIVE"] = "Never"

    _run(
        ["git", "clone", "--quiet", "--filter=blob:none", "--no-checkout", SOURCE_REPO, "."],
        cwd=destination,
        env=env,
    )
    _run(["git", "lfs", "install", "--local"], cwd=destination, env=env)
    _run(["git", "sparse-checkout", "init", "--cone"], cwd=destination, env=env)
    _run(
        ["git", "sparse-checkout", "set", *(path.as_posix() for path in ASSET_ROOTS)],
        cwd=destination,
        env=env,
    )
    _run(
        ["git", "checkout", "--quiet", "--detach", SOURCE_REVISION],
        cwd=destination,
        env=env,
    )
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=destination,
        env=env,
        check=True,
        capture_output=True,
        text=True,
        timeout=COMMAND_TIMEOUT_SECONDS,
    ).stdout.strip()
    if head != SOURCE_REVISION:
        raise RuntimeError(f"asset checkout resolved to {head}, expected {SOURCE_REVISION}")


def copy_assets(source: Path, destination: Path) -> None:
    for source_file in asset_files(source):
        relative = source_file.relative_to(source)
        destination_file = destination / relative
        destination_file.parent.mkdir(parents=True, exist_ok=True)
        partial = destination_file.with_name(destination_file.name + ".shadow-dance.part")
        try:
            shutil.copy2(source_file, partial)
            partial.replace(destination_file)
        finally:
            partial.unlink(missing_ok=True)


def write_report(
    report_path: Path,
    *,
    identity: AssetIdentity | None,
    action: str,
    preflight_error: str | None,
    status: str = "verified",
    error: str | None = None,
) -> None:
    payload = {
        "format": "shadow_dance_sonic_assets_v1",
        "recorded_utc": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "status": status,
        "action": action,
        "source": {
            "repository": SOURCE_REPO,
            "revision": SOURCE_REVISION,
            "license": "Upstream dual license; runtime asset fetch excludes model weights",
            "license_file": "LICENSE",
            "asset_roots": [path.as_posix() for path in ASSET_ROOTS],
        },
        "identity": asdict(identity) if identity is not None else None,
        "expected_urdf_mesh_references": EXPECTED_URDF_MESH_REFERENCES,
        "preflight_error": preflight_error,
        "error": error,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sonic-root", type=Path, default=Path("/opt/sonic"))
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    preflight_error: str | None = None
    try:
        try:
            identity = validate_assets(args.sonic_root)
            action = "verified_cached"
        except ValueError as exc:
            preflight_error = str(exc)
            print(f"SONIC G1 assets require hydration: {preflight_error}", flush=True)
            with tempfile.TemporaryDirectory(prefix="shadow-dance-sonic-assets-") as temporary:
                checkout = Path(temporary)
                checkout_assets(checkout)
                validate_assets(checkout)
                copy_assets(checkout, args.sonic_root)
            identity = validate_assets(args.sonic_root)
            action = "hydrated_from_pinned_git_lfs"
    except Exception as exc:
        try:
            observed_identity = identify_assets(args.sonic_root)
        except Exception:
            observed_identity = None
        write_report(
            args.report,
            identity=observed_identity,
            action="hydration_failed",
            preflight_error=preflight_error,
            status="failed",
            error=f"{type(exc).__name__}: {exc}",
        )
        raise

    write_report(
        args.report,
        identity=identity,
        action=action,
        preflight_error=preflight_error,
    )
    print(
        f"SONIC G1 assets verified: {identity.file_count} files, "
        f"{identity.total_bytes} bytes, manifest {identity.manifest_sha256}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
