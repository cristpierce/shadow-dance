#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 CHECKPOINT [MOTION_DIR]" >&2
  exit 2
fi

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SONIC_ROOT="${SONIC_ROOT:-${PROJECT_ROOT}/../GR00T-WholeBodyControl}"
CHECKPOINT="$1"
MOTION_DIR="${2:-${PROJECT_ROOT}/data/generated/heldout}"

cd "${SONIC_ROOT}"
python gear_sonic/eval_agent_trl.py \
  +checkpoint="${CHECKPOINT}" +headless=True ++num_envs=1 \
  +export_onnx_only=true \
  "++manager_env.commands.motion.motion_lib_cfg.motion_file=${MOTION_DIR}" \
  "++manager_env.commands.motion.motion_lib_cfg.smpl_motion_file=dummy"
