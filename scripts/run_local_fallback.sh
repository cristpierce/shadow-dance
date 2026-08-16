#!/usr/bin/env bash
set -euo pipefail

# Deadline-only fallback for a Linux host (including WSL2) with Docker and the NVIDIA
# Container Toolkit. It uses the same immutable runtime and pipeline as the managed
# route, but deliberately keeps evidence on the mounted repository instead of S3.
# This wrapper never supplies or defaults third-party licence acceptance.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd -- "${SCRIPT_DIR}/.." && pwd)}"
POLICY_IMAGE="${POLICY_IMAGE:-ghcr.io/nebius/nebius-physical-ai/npa-sonic@sha256:c9ba0996b28f54b013e36da689638b386a7ef9c0c8c4413fc4b3c72ff1a808bb}"
EXPECTED_IMAGE="ghcr.io/nebius/nebius-physical-ai/npa-sonic@sha256:c9ba0996b28f54b013e36da689638b386a7ef9c0c8c4413fc4b3c72ff1a808bb"
SUBMISSION_DEADLINE_UTC="${SUBMISSION_DEADLINE_UTC:-2026-08-17T06:59:00Z}"
PORTAL_RESERVE_SECONDS="${PORTAL_RESERVE_SECONDS:-2700}"
FINALIZATION_RESERVE_SECONDS="${FINALIZATION_RESERVE_SECONDS:-7200}"
LOCAL_MAX_WALLTIME_SECONDS="${LOCAL_MAX_WALLTIME_SECONDS:-21600}"
LOCAL_LADDER="${LOCAL_LADDER:-5,250}"
LOCAL_SMOKE_NUM_ENVS="${LOCAL_SMOKE_NUM_ENVS:-4}"
LOCAL_MAIN_NUM_ENVS="${LOCAL_MAIN_NUM_ENVS:-8}"
ISAAC_CACHE_VOLUME="${ISAAC_CACHE_VOLUME:-shadow-dance-isaac-5-1-cache}"
RUN_ID="${RUN_ID:-shadow-dance-local-$(date -u +%Y%m%dT%H%M%SZ)}"

if [[ "${ENTRANT_NVIDIA_EULA_ACCEPTED:-}" != "YES" || "${ACCEPT_EULA:-}" != "Y" ]]; then
  echo "Named entrant acceptance and ACCEPT_EULA=Y are required; refusing before Docker starts Isaac." >&2
  exit 78
fi
if [[ "${POLICY_IMAGE}" != "${EXPECTED_IMAGE}" ]]; then
  echo "POLICY_IMAGE must be the reviewed immutable SONIC image digest." >&2
  exit 2
fi
if ! [[ "${RUN_ID}" =~ ^[A-Za-z0-9_.-]+$ ]]; then
  echo "RUN_ID contains characters unsupported by the evidence layout." >&2
  exit 2
fi
for value in "${PORTAL_RESERVE_SECONDS}" "${FINALIZATION_RESERVE_SECONDS}" \
  "${LOCAL_MAX_WALLTIME_SECONDS}" "${LOCAL_SMOKE_NUM_ENVS}" "${LOCAL_MAIN_NUM_ENVS}"; do
  if ! [[ "${value}" =~ ^[1-9][0-9]*$ ]]; then
    echo "Local numeric controls must be positive integers." >&2
    exit 2
  fi
done
for command_name in date docker git timeout; do
  command -v "${command_name}" >/dev/null || {
    echo "Missing required local command: ${command_name}" >&2
    exit 2
  }
done

cd "${PROJECT_ROOT}"
SUBMISSION_COMMIT="${SUBMISSION_COMMIT:-$(git rev-parse HEAD)}"
if ! [[ "${SUBMISSION_COMMIT}" =~ ^[0-9a-f]{40}$ ]] || \
   [[ "$(git rev-parse HEAD)" != "${SUBMISSION_COMMIT}" ]]; then
  echo "SUBMISSION_COMMIT must be the full SHA of the checked-out commit." >&2
  exit 2
fi
if ! git diff --quiet || ! git diff --cached --quiet || \
   [[ -n "$(git ls-files --others --exclude-standard)" ]]; then
  echo "The local fallback requires a clean checkout so its recorded commit matches its code." >&2
  exit 2
fi

deadline_epoch="$(date -u -d "${SUBMISSION_DEADLINE_UTC}" +%s)"
usable_seconds="$((deadline_epoch - $(date -u +%s) - PORTAL_RESERVE_SECONDS))"
if [[ "${usable_seconds}" -le 0 ]]; then
  echo "The portal reserve has begun; refusing a local run that cannot be submitted." >&2
  exit 4
fi
if [[ "${LOCAL_MAX_WALLTIME_SECONDS}" -gt "${usable_seconds}" ]]; then
  LOCAL_MAX_WALLTIME_SECONDS="${usable_seconds}"
fi

if ! docker image inspect "${POLICY_IMAGE}" >/dev/null 2>&1; then
  echo "Pulling the reviewed public SONIC image; it contains no NVIDIA Isaac bytes."
  docker pull "${POLICY_IMAGE}"
fi
docker image inspect --format '{{range .RepoDigests}}{{println .}}{{end}}' "${POLICY_IMAGE}" \
  | grep -Fqx "${EXPECTED_IMAGE}" || {
    echo "The local SONIC image does not expose the expected repository digest." >&2
    exit 2
  }
if ! docker run --rm --gpus all \
  --entrypoint /opt/npa/venv/bin/python "${POLICY_IMAGE}" -c \
  'import torch; assert torch.cuda.is_available(); print(torch.cuda.get_device_name(0)); print(torch.ones(1, device="cuda").item())'; then
  echo "The pinned CUDA 13 SONIC image cannot allocate on this host. Update to a CUDA 13-compatible NVIDIA driver (Windows 580.88 or newer) or use the managed route." >&2
  exit 69
fi
docker volume create "${ISAAC_CACHE_VOLUME}" >/dev/null

echo "Starting local fallback ${RUN_ID}; evidence will remain in outputs/cloud/${RUN_ID}."
docker run --rm --gpus all --ipc=host \
  --name "${RUN_ID}" \
  --label shadow-dance.run-id="${RUN_ID}" \
  --volume "${PROJECT_ROOT}:/workspace/shadow-dance" \
  --volume "${ISAAC_CACHE_VOLUME}:/opt/isaac-cache" \
  --workdir /workspace/shadow-dance \
  --entrypoint /bin/bash \
  --env ACCEPT_EULA \
  --env ENTRANT_NVIDIA_EULA_ACCEPTED \
  --env POLICY_IMAGE="${POLICY_IMAGE}" \
  --env PROJECT_ROOT=/workspace/shadow-dance \
  --env SONIC_ROOT=/opt/sonic \
  --env SONIC_PYTHON=/isaac-sim/python.sh \
  --env NPA_IMAGE_PYTHON=/opt/npa/venv/bin/python \
  --env BASE_PYTHON=/opt/npa/venv/bin/python \
  --env LOCAL_ONLY=1 \
  --env EVIDENCE_S3_URI= \
  --env HF_MODEL_REPO= \
  --env SUBMISSION_COMMIT="${SUBMISSION_COMMIT}" \
  --env RUN_ID="${RUN_ID}" \
  --env LADDER="${LOCAL_LADDER}" \
  --env SMOKE_NUM_ENVS="${LOCAL_SMOKE_NUM_ENVS}" \
  --env MAIN_NUM_ENVS="${LOCAL_MAIN_NUM_ENVS}" \
  --env SUBMISSION_DEADLINE_UTC="${SUBMISSION_DEADLINE_UTC}" \
  --env FINALIZATION_RESERVE_SECONDS="${FINALIZATION_RESERVE_SECONDS}" \
  --env PORTAL_RESERVE_SECONDS="${PORTAL_RESERVE_SECONDS}" \
  --env MAX_WALLTIME_SECONDS="${LOCAL_MAX_WALLTIME_SECONDS}" \
  --env LOCAL_PIPELINE_TIMEOUT_SECONDS="${LOCAL_MAX_WALLTIME_SECONDS}" \
  "${POLICY_IMAGE}" -lc \
    'set -euo pipefail; nvidia-smi; timeout --signal=TERM --kill-after=15m "${LOCAL_PIPELINE_TIMEOUT_SECONDS}s" bash scripts/cloud_pipeline.sh'
