#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 CHECKPOINT LABEL [MOTION_DIR]" >&2
  exit 2
fi

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SONIC_ROOT="${SONIC_ROOT:-${PROJECT_ROOT}/../GR00T-WholeBodyControl}"
CHECKPOINT="$1"
LABEL="$2"
MOTION_DIR="${3:-${PROJECT_ROOT}/data/generated/heldout}"
NUM_ENVS="${NUM_ENVS:-64}"
SEED="${SEED:-42}"
OUTPUT_DIR="${OUTPUT_DIR:-${PROJECT_ROOT}/results/raw/${LABEL}}"

mkdir -p "${OUTPUT_DIR}"
cd "${SONIC_ROOT}"

python gear_sonic/eval_agent_trl.py \
  +checkpoint="${CHECKPOINT}" +headless=True seed="${SEED}" \
  ++eval_callbacks=im_eval ++run_eval_loop=False ++num_envs="${NUM_ENVS}" \
  "+manager_env/terminations=tracking/eval" \
  "++manager_env.commands.motion.motion_lib_cfg.motion_file=${MOTION_DIR}" \
  "++manager_env.commands.motion.motion_lib_cfg.smpl_motion_file=dummy" \
  "++manager_env.commands.motion.motion_lib_cfg.max_unique_motions=64" \
  hydra.run.dir="${OUTPUT_DIR}" \
  2>&1 | tee "${OUTPUT_DIR}/eval.log"
