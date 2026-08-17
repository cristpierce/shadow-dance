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
MOTION_DIR="${3:-${PROJECT_ROOT}/data/generated-v2/heldout}"
NUM_ENVS="${NUM_ENVS:-4}"
SEED="${SEED:-303}"
OUTPUT_DIR="${OUTPUT_DIR:-${PROJECT_ROOT}/media/raw/${LABEL}}"
SONIC_PYTHON="${SONIC_PYTHON:-python}"
MOTION_KEYS_FILE="${MOTION_KEYS_FILE:-}"

motion_filter_args=()
if [[ -n "${MOTION_KEYS_FILE}" ]]; then
  if [[ ! -f "${MOTION_KEYS_FILE}" ]]; then
    echo "Motion-key inventory does not exist: ${MOTION_KEYS_FILE}" >&2
    exit 2
  fi
  mapfile -t motion_keys < <(sed '/^[[:space:]]*$/d' "${MOTION_KEYS_FILE}")
  if [[ "${#motion_keys[@]}" -eq 0 ]]; then
    echo "Motion-key inventory is empty: ${MOTION_KEYS_FILE}" >&2
    exit 2
  fi
  for key in "${motion_keys[@]}"; do
    if [[ ! "${key}" =~ ^[A-Za-z0-9_.-]+$ ]]; then
      echo "Unsupported motion key in ${MOTION_KEYS_FILE}: ${key}" >&2
      exit 2
    fi
  done
  motion_filter="$(IFS=,; printf '[%s]' "${motion_keys[*]}")"
  motion_filter_args+=(
    "++manager_env.commands.motion.motion_lib_cfg.filter_motion_keys=${motion_filter}"
  )
fi

mkdir -p "${OUTPUT_DIR}"
cd "${SONIC_ROOT}"

"${SONIC_PYTHON}" gear_sonic/eval_agent_trl.py \
  +checkpoint="${CHECKPOINT}" +headless=True seed="${SEED}" ++run_eval_loop=False \
  ++eval_callbacks=im_eval ++num_envs="${NUM_ENVS}" \
  "+manager_env/terminations=tracking/eval" \
  "++manager_env.observations.policy.enable_corruption=False" \
  "++manager_env.observations.tokenizer.enable_corruption=False" \
  "${motion_filter_args[@]}" \
  "++manager_env.commands.motion.motion_lib_cfg.motion_file=${MOTION_DIR}" \
  "++manager_env.commands.motion.motion_lib_cfg.smpl_motion_file=dummy" \
  ++manager_env.config.render_results=True \
  "++manager_env.config.save_rendering_dir=${OUTPUT_DIR}" \
  ++manager_env.config.env_spacing=10.0 \
  "~manager_env/recorders=empty" \
  "+manager_env/recorders=render" \
  2>&1 | tee "${OUTPUT_DIR}/render.log"
