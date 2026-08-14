#!/usr/bin/env python3
"""Download the exact public SONIC base files and verify their identities."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
from pathlib import Path

REPO_ID = "nvidia/GEAR-SONIC"
REVISION = "9c0ff22b4ffec27c5392e8e284eb2f2df7a5b4e2"
FILES = {
    "sonic_release/last.pt": (
        469_418_283,
        "e6bdab3f64a39336b3d41877d4f497d05f58af275f288ec0e6746c283ded8909",
    ),
    "sonic_release/config.yaml": (
        28_331,
        "f08187795fa16a839a28bc1c18e0555d38d9420e03733744341cdcb56ab629c7",
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def valid(path: Path, size: int, expected_hash: str) -> bool:
    return path.is_file() and path.stat().st_size == size and sha256(path) == expected_hash


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    try:
        from huggingface_hub import hf_hub_download
    except ImportError as exc:  # pragma: no cover - the SONIC image provides this
        raise SystemExit("huggingface_hub is required") from exc

    for filename, (size, expected_hash) in FILES.items():
        destination = args.output_dir / filename
        if valid(destination, size, expected_hash):
            print(f"verified cached {filename}")
            continue
        cached = Path(
            hf_hub_download(
                repo_id=REPO_ID,
                filename=filename,
                revision=REVISION,
                token=os.environ.get("HF_TOKEN") or None,
            )
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        partial = destination.with_suffix(destination.suffix + ".part")
        shutil.copy2(cached, partial)
        if not valid(partial, size, expected_hash):
            partial.unlink(missing_ok=True)
            raise SystemExit(f"identity check failed for {filename}")
        partial.replace(destination)
        print(f"downloaded and verified {filename}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
