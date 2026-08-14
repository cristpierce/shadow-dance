#!/usr/bin/env python3
"""Upload an evidence file/tree to an S3 URI with SHA-256 metadata."""

from __future__ import annotations

import argparse
import hashlib
import mimetypes
import os
from pathlib import Path
from urllib.parse import urlparse


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def split_s3(uri: str) -> tuple[str, str]:
    parsed = urlparse(uri)
    if parsed.scheme != "s3" or not parsed.netloc:
        raise ValueError(f"expected s3://bucket/prefix, got {uri!r}")
    return parsed.netloc, parsed.path.lstrip("/")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination")
    args = parser.parse_args()

    import boto3
    from botocore.exceptions import ClientError

    source = args.source.resolve()
    if not source.exists():
        raise SystemExit(f"upload source does not exist: {source}")
    bucket, prefix = split_s3(args.destination)
    endpoint = os.environ.get("AWS_ENDPOINT_URL") or os.environ.get("S3_ENDPOINT_URL")
    client = boto3.client("s3", endpoint_url=endpoint)
    files = (
        [source]
        if source.is_file()
        else sorted(path for path in source.rglob("*") if path.is_file())
    )
    uploaded = 0
    skipped = 0
    for path in files:
        relative = path.name if source.is_file() else path.relative_to(source).as_posix()
        key = "/".join(part for part in (prefix.rstrip("/"), relative) if part)
        digest = sha256(path)
        try:
            remote = client.head_object(Bucket=bucket, Key=key)
        except ClientError as exc:
            code = str(exc.response.get("Error", {}).get("Code", ""))
            if code not in {"404", "NoSuchKey", "NotFound"}:
                raise
            remote = None
        if (
            remote
            and int(remote.get("ContentLength", -1)) == path.stat().st_size
            and remote.get("Metadata", {}).get("sha256") == digest
        ):
            skipped += 1
            continue
        extra = {"Metadata": {"sha256": digest}}
        content_type, _ = mimetypes.guess_type(path.name)
        if content_type:
            extra["ContentType"] = content_type
        client.upload_file(str(path), bucket, key, ExtraArgs=extra)
        uploaded += 1
    print(f"S3 evidence sync complete: uploaded={uploaded} unchanged={skipped}")


if __name__ == "__main__":
    main()
