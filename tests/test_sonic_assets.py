from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    import hydrate_sonic_assets as assets
finally:
    sys.path.pop(0)


def _configure_tiny_identity(monkeypatch: pytest.MonkeyPatch, root: Path) -> None:
    monkeypatch.setattr(assets, "ASSET_ROOTS", (Path("meshes"), Path("urdf")))
    monkeypatch.setattr(assets, "EXPECTED_URDF_MESH_REFERENCES", 1)
    (root / "meshes").mkdir(parents=True)
    (root / "urdf").mkdir(parents=True)
    (root / "meshes" / "pelvis.STL").write_bytes(b"solid pelvis\nendsolid pelvis\n")
    (root / "urdf" / "main.urdf").write_text(
        '<mesh filename="package://robot_description/meshes/g1/pelvis.STL" />\n',
        encoding="utf-8",
    )
    identity = assets.identify_assets(root)
    monkeypatch.setattr(assets, "EXPECTED_FILE_COUNT", identity.file_count)
    monkeypatch.setattr(assets, "EXPECTED_TOTAL_BYTES", identity.total_bytes)
    monkeypatch.setattr(assets, "EXPECTED_MANIFEST_SHA256", identity.manifest_sha256)


def test_asset_identity_is_canonical_and_rejects_lfs_pointers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configure_tiny_identity(monkeypatch, tmp_path)
    identity = assets.validate_assets(tmp_path)
    assert identity.file_count == 2
    assert identity.pointer_files == ()

    (tmp_path / "meshes" / "pelvis.STL").write_bytes(
        assets.LFS_POINTER_MAGIC
        + b"\noid sha256:5ba6bbc888e630550140d3c26763f10206da8c8bd30ed886b8ede41c61f57a31\n"
        + b"size 1060884\n"
    )
    with pytest.raises(ValueError, match="Git LFS pointer"):
        assets.validate_assets(tmp_path)


def test_checkout_is_pinned_sparse_and_forces_lfs_smudging(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    commands: list[tuple[list[str], dict[str, str]]] = []

    def fake_run(command: list[str], *, cwd: Path, env: dict[str, str]) -> None:
        assert cwd == tmp_path
        commands.append((command, env))

    monkeypatch.setenv("GIT_LFS_SKIP_SMUDGE", "1")
    monkeypatch.setenv("GIT_LFS_SKIP_DOWNLOAD_ERRORS", "1")
    monkeypatch.setattr(assets, "_run", fake_run)
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(stdout=assets.SOURCE_REVISION + "\n"),
    )

    assets.checkout_assets(tmp_path)

    flattened = [command for command, _ in commands]
    assert flattened[0] == [
        "git",
        "clone",
        "--quiet",
        "--filter=blob:none",
        "--no-checkout",
        assets.SOURCE_REPO,
        ".",
    ]
    assert flattened[-1] == [
        "git",
        "checkout",
        "--quiet",
        "--detach",
        assets.SOURCE_REVISION,
    ]
    sparse = next(command for command in flattened if command[1:3] == ["sparse-checkout", "set"])
    assert sparse[3:] == [path.as_posix() for path in assets.ASSET_ROOTS]
    assert all("GIT_LFS_SKIP_SMUDGE" not in env for _, env in commands)
    assert all("GIT_LFS_SKIP_DOWNLOAD_ERRORS" not in env for _, env in commands)
    assert all(env["GIT_TERMINAL_PROMPT"] == "0" for _, env in commands)


def test_pinned_asset_contract_matches_runtime_and_precedes_isaac() -> None:
    config = yaml.safe_load(
        (ROOT / "configs" / "shadow_dip_finetune.yaml").read_text(encoding="utf-8")
    )
    assert config["runtime_sonic_commit"] == assets.SOURCE_REVISION
    assert assets.EXPECTED_FILE_COUNT == 69
    assert assets.EXPECTED_TOTAL_BYTES == 68_378_071
    assert assets.EXPECTED_MANIFEST_SHA256 == (
        "79fa6310cefeaf819c103e5c83c9c40c55ef71b28aace7bf9f8c116d4966d0c7"
    )

    pipeline = (ROOT / "scripts" / "cloud_pipeline.sh").read_text(encoding="utf-8")
    hydration = pipeline.index("scripts/hydrate_sonic_assets.py")
    base_model = pipeline.index("scripts/download_base_model.py")
    isaac = pipeline.index("# Cold start downloads Isaac")
    assert hydration < base_model < isaac
    assert "base-model.sha256 sonic-assets.json" in pipeline


def test_asset_report_records_pinned_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configure_tiny_identity(monkeypatch, tmp_path)
    identity = assets.validate_assets(tmp_path)
    report = tmp_path / "report.json"
    assets.write_report(
        report,
        identity=identity,
        action="verified_cached",
        preflight_error=None,
    )
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["format"] == "shadow_dance_sonic_assets_v1"
    assert payload["status"] == "verified"
    assert payload["error"] is None
    assert payload["source"]["revision"] == assets.SOURCE_REVISION
    assert payload["identity"]["pointer_files"] == []
    canonical = hashlib.sha256(
        (
            f"{assets._sha256(tmp_path / 'meshes' / 'pelvis.STL')}  "
            f"{(tmp_path / 'meshes' / 'pelvis.STL').stat().st_size}  meshes/pelvis.STL\n"
            f"{assets._sha256(tmp_path / 'urdf' / 'main.urdf')}  "
            f"{(tmp_path / 'urdf' / 'main.urdf').stat().st_size}  urdf/main.urdf\n"
        ).encode()
    ).hexdigest()
    assert payload["identity"]["manifest_sha256"] == canonical


def test_failed_hydration_leaves_a_forensic_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    report = tmp_path / "report.json"
    sonic_root = tmp_path / "sonic"
    sonic_root.mkdir()

    def fail_checkout(_: Path) -> None:
        raise RuntimeError("offline")

    monkeypatch.setattr(assets, "checkout_assets", fail_checkout)
    monkeypatch.setattr(
        sys,
        "argv",
        ["hydrate_sonic_assets.py", "--sonic-root", str(sonic_root), "--report", str(report)],
    )

    with pytest.raises(RuntimeError, match="offline"):
        assets.main()

    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["status"] == "failed"
    assert payload["action"] == "hydration_failed"
    assert payload["error"] == "RuntimeError: offline"
    assert payload["identity"]["file_count"] == 0
