from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_local_fallback_is_digest_pinned_licensed_and_local_only() -> None:
    script = (ROOT / "scripts" / "run_local_fallback.sh").read_text(encoding="utf-8")
    digest = "c9ba0996b28f54b013e36da689638b386a7ef9c0c8c4413fc4b3c72ff1a808bb"
    assert script.count(digest) == 2
    acceptance = script.index('ENTRANT_NVIDIA_EULA_ACCEPTED:-}" != "YES"')
    image_pull = script.index('docker pull "${POLICY_IMAGE}"')
    gpu_probe = script.index("assert torch.cuda.is_available()")
    docker_run = script.index("docker run --rm --gpus all")
    pipeline_run = script.rindex("docker run --rm --gpus all")
    assert acceptance < image_pull < docker_run < gpu_probe < pipeline_run
    assert "export ACCEPT_EULA" not in script
    assert "export ENTRANT_NVIDIA_EULA_ACCEPTED" not in script
    assert "--env LOCAL_ONLY=1" in script
    assert "--env EVIDENCE_S3_URI=" in script
    assert "shadow-dance-isaac-5-1-cache" in script
    assert "Windows 580.88 or newer" in script
    assert "git ls-files --others --exclude-standard" in script
    assert "outputs/cloud/${RUN_ID}" in script


def test_managed_workflow_cannot_inherit_local_only() -> None:
    workflow = (ROOT / "cloud" / "sky-shadow-dance.yaml").read_text(encoding="utf-8")
    materializer = (ROOT / "scripts" / "materialize_cloud_plan.py").read_text(encoding="utf-8")
    assert 'LOCAL_ONLY: "0"' in workflow
    assert workflow.count('test "${LOCAL_ONLY:-}" = 0') == 2
    assert '"LOCAL_ONLY": "0"' in materializer
