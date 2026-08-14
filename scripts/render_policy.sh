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
NUM_ENVS="${NUM_ENVS:-4}"
OUTPUT_DIR="${OUTPUT_DIR:-${PROJECT_ROOT}/media/raw/${LABEL}}"

mkdir -p "${OUTPUT_DIR}"
cd "${SONIC_ROOT}"

python gear_sonic/eval_agent_trl.py \
  +checkpoint="${CHECKPOINT}" +headless=True ++run_eval_loop=False \
  ++eval_callbacks=im_eval ++num_envs="${NUM_ENVS}" \
  "++manager_env.commands.motion.motion_lib_cfg.motion_file=${MOTION_DIR}" \
  "++manager_env.commands.motion.motion_lib_cfg.smpl_motion_file=dummy" \
  ++manager_env.config.render_results=True \
  "++manager_env.config.save_rendering_dir=${OUTPUT_DIR}" \
  ++manager_env.config.env_spacing=10.0 \
  "~manager_env/recorders=empty" "+manager_env/recorders=render" \
  2>&1 | tee "${OUTPUT_DIR}/render.log"
