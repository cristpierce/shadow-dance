"""Create a hash inventory for the experimental proxy-adapter model package."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

root = Path(".runtime/adapter-model")
manifest_path = root / "manifest.json"
files = []
for path in sorted(root.rglob("*")):
    if path.is_file() and path != manifest_path:
        files.append(
            {
                "name": path.relative_to(root).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
manifest = {
    "format": "shadow_dance_proxy_adapter_package_v1",
    "generated_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    "official_sonic_recipe": False,
    "official_wbt_bench": False,
    "isaac_result": False,
    "files": files,
}
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"file_count": len(files), "manifest": manifest_path.as_posix()}))
