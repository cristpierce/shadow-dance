#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 CHECKPOINT [MOTION_DIR]" >&2
  exit 2
fi

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SONIC_ROOT="${SONIC_ROOT:-${PROJECT_ROOT}/../GR00T-WholeBodyControl}"
CHECKPOINT="$1"
MOTION_DIR="${2:-${PROJECT_ROOT}/data/generated-v2/heldout}"
SONIC_PYTHON="${SONIC_PYTHON:-python}"
OUTPUT_DIR="${OUTPUT_DIR:-$(dirname -- "${CHECKPOINT}")}"

if [[ ! -f "${CHECKPOINT}" ]]; then
  echo "Checkpoint does not exist: ${CHECKPOINT}" >&2
  exit 2
fi
mkdir -p "${OUTPUT_DIR}/hydra-export"

cd "${SONIC_ROOT}"
"${SONIC_PYTHON}" gear_sonic/eval_agent_trl.py \
  +checkpoint="${CHECKPOINT}" +headless=True ++num_envs=1 \
  +export_onnx_only=true \
  "++experiment_dir=${OUTPUT_DIR}" \
  "++manager_env.commands.motion.motion_lib_cfg.motion_file=${MOTION_DIR}" \
  "++manager_env.commands.motion.motion_lib_cfg.smpl_motion_file=dummy" \
  "hydra.run.dir=${OUTPUT_DIR}/hydra-export"
