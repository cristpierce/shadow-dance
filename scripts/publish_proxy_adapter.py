"""Validate and publish the experimental proxy adapter to Hugging Face.

This intentionally publishes as a public *model* repository with an explicit
``not-official`` name. It is separate from the official Isaac/PPO publication path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

from huggingface_hub import HfApi

REQUIRED_FILES = {
    "LICENSE",
    "NOTICE",
    "README.md",
    "adapter.json",
    "final-comparison.json",
    "manifest.json",
    "model_encoder.onnx",
    "observation_config.yaml",
    "onnx-validation.json",
    "selection.json",
    "shadow-dance-affine-proxy-decoder.onnx",
    "video-manifest.json",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_package(root: Path) -> dict[str, object]:
    root = root.resolve()
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError(f"missing package manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    package_flags = ("official_sonic_recipe", "official_wbt_bench", "isaac_result")
    if any(manifest.get(flag) is not False for flag in package_flags):
        raise ValueError("package disclaimer flags must all be false")

    entries = manifest.get("files")
    if not isinstance(entries, list) or len(entries) != 51:
        raise ValueError("package manifest must contain exactly 51 file entries")
    names: set[str] = set()
    for entry in entries:
        name = str(entry["name"])
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts or name in names:
            raise ValueError(f"unsafe or duplicate manifest path: {name}")
        names.add(name)
        path = (root / relative).resolve()
        if root not in path.parents or not path.is_file():
            raise ValueError(f"missing or unsafe package file: {name}")
        if path.stat().st_size != int(entry["bytes"]):
            raise ValueError(f"byte-length mismatch: {name}")
        if sha256(path) != entry["sha256"]:
            raise ValueError(f"SHA-256 mismatch: {name}")

    actual = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}
    if actual != names | {"manifest.json"}:
        raise ValueError("package inventory differs from its manifest")
    missing = REQUIRED_FILES - actual
    if missing:
        raise ValueError(f"required package files missing: {sorted(missing)}")

    comparison_path = root / "final-comparison.json"
    validation_path = root / "onnx-validation.json"
    video_path = root / "video-manifest.json"
    comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
    video = json.loads(video_path.read_text(encoding="utf-8"))
    if comparison["onnx_validation"]["sha256"] != sha256(validation_path):
        raise ValueError("comparison does not bind the bundled ONNX validation report")
    if video["comparison"]["sha256"] != sha256(comparison_path):
        raise ValueError("video manifest does not bind the bundled comparison report")
    comparison_flags = (
        "official_sonic_recipe",
        "official_wbt_bench",
        "isaac_result",
        "fine_tuned_ppo_checkpoint",
    )
    if any(comparison.get(flag) is not False for flag in comparison_flags):
        raise ValueError("comparison disclaimer flags must all be false")

    readme = (root / "README.md").read_text(encoding="utf-8")
    for required_text in (
        "Not the official SuperSONIC fine-tune",
        "Licensed by NVIDIA Corporation under the NVIDIA Open Model License",
        "Motion Data by Bones Studio",
    ):
        if required_text not in readme:
            raise ValueError(f"model card is missing required text: {required_text}")

    decoder = root / "shadow-dance-affine-proxy-decoder.onnx"
    return {
        "manifest_entries": len(entries),
        "manifest_sha256": sha256(manifest_path),
        "decoder_sha256": sha256(decoder),
        "decoder_bytes": decoder.stat().st_size,
        "comparison_sha256": sha256(comparison_path),
    }


def verify_anonymous(url: str) -> None:
    request = urllib.request.Request(
        url,
        headers={"Range": "bytes=0-0", "User-Agent": "shadow-dance-publication-check/1"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
        if response.status not in {200, 206}:
            raise RuntimeError(f"anonymous verification returned HTTP {response.status}")
        response.read(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-id", required=True)
    parser.add_argument("--source", type=Path, default=Path(".runtime/adapter-model"))
    parser.add_argument(
        "--report", type=Path, default=Path(".runtime/huggingface-proxy-adapter-publication.json")
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.repo_id.count("/") != 1 or not args.repo_id.endswith(
        "/shadow-dance-affine-proxy-adapter-not-official"
    ):
        raise ValueError("repo id must be NAMESPACE/shadow-dance-affine-proxy-adapter-not-official")

    validation = validate_package(args.source)
    if args.dry_run:
        print(json.dumps({"validated": True, **validation}, indent=2))
        return

    api = HfApi()
    identity = api.whoami()
    api.create_repo(args.repo_id, repo_type="model", private=False, exist_ok=True)
    api.update_repo_settings(args.repo_id, repo_type="model", private=False)
    api.upload_folder(
        repo_id=args.repo_id,
        repo_type="model",
        folder_path=args.source,
        path_in_repo=".",
        commit_message="Publish transparent experimental proxy adapter",
        commit_description=(
            "Not an Isaac/PPO fine-tune, WBT-Bench result, or official SuperSONIC score."
        ),
    )

    info = api.repo_info(args.repo_id, repo_type="model")
    if info.private:
        raise RuntimeError("published model unexpectedly remains private")
    commit_sha = str(info.sha)
    encoded_repo = quote(args.repo_id, safe="/")
    decoder_url = (
        f"https://huggingface.co/{encoded_repo}/resolve/{commit_sha}/"
        "shadow-dance-affine-proxy-decoder.onnx"
    )
    readme_url = f"https://huggingface.co/{encoded_repo}/resolve/{commit_sha}/README.md"
    last_error: Exception | None = None
    for _ in range(4):
        try:
            verify_anonymous(readme_url)
            verify_anonymous(decoder_url)
            last_error = None
            break
        except Exception as error:  # publication can take a few seconds to propagate
            last_error = error
            time.sleep(3)
    if last_error is not None:
        raise RuntimeError("immutable model files were not anonymously reachable") from last_error

    report = {
        "format": "shadow_dance_huggingface_proxy_publication_v1",
        "published_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "publisher": identity.get("name") or identity.get("fullname"),
        "repo_id": args.repo_id,
        "commit_sha": commit_sha,
        "model_url": f"https://huggingface.co/{encoded_repo}",
        "immutable_model_url": f"https://huggingface.co/{encoded_repo}/tree/{commit_sha}",
        "immutable_decoder_url": decoder_url,
        "anonymous_verification": True,
        "official_sonic_recipe": False,
        "official_wbt_bench": False,
        "isaac_result": False,
        **validation,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
