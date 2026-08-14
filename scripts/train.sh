#!/usr/bin/env bash
set -euo pipefail

# Run from this repository. Override every value through the environment so the exact
# invocation is preserved in cloud logs without editing the script.
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SONIC_ROOT="${SONIC_ROOT:-${PROJECT_ROOT}/../GR00T-WholeBodyControl}"
MOTION_DIR="${MOTION_DIR:-${PROJECT_ROOT}/data/generated/train}"
CHECKPOINT="${CHECKPOINT:-${SONIC_ROOT}/sonic_release/last.pt}"
NUM_ENVS="${NUM_ENVS:-1024}"
ITERATIONS="${ITERATIONS:-25}"
SEED="${SEED:-42}"
LEARNING_RATE="${LEARNING_RATE:-2e-5}"
REGULAR_SAVE_FREQUENCY="${REGULAR_SAVE_FREQUENCY:-1000000}"
SAVE_LAST_FREQUENCY="${SAVE_LAST_FREQUENCY:-5}"
RUN_NAME="${RUN_NAME:-shadow_dip_stage_${ITERATIONS}}"
OUTPUT_ROOT="${OUTPUT_ROOT:-${PROJECT_ROOT}/outputs}"
SONIC_PYTHON="${SONIC_PYTHON:-python}"

mkdir -p "${OUTPUT_ROOT}"
cd "${SONIC_ROOT}"

"${SONIC_PYTHON}" gear_sonic/train_agent_trl.py \
  +exp=manager/universal_token/all_modes/sonic_release \
  +checkpoint="${CHECKPOINT}" \
  seed="${SEED}" num_envs="${NUM_ENVS}" headless=True use_wandb=false \
  base_dir="${OUTPUT_ROOT}" exp_var="${RUN_NAME}" \
  ++manager_env.commands.motion.motion_lib_cfg.motion_file="${MOTION_DIR}" \
  ++manager_env.commands.motion.motion_lib_cfg.smpl_motion_file=dummy \
  ++manager_env.commands.motion.cat_upper_body_poses=false \
  ++manager_env.commands.motion.teleop_sample_prob_when_smpl=0.0 \
  ++algo.config.actor_learning_rate="${LEARNING_RATE}" \
  ++algo.config.num_learning_iterations="${ITERATIONS}" \
  ++callbacks.model_save.save_frequency="${REGULAR_SAVE_FREQUENCY}" \
  ++callbacks.model_save.save_last_frequency="${SAVE_LAST_FREQUENCY}" \
  2>&1 | tee "${OUTPUT_ROOT}/${RUN_NAME}.log"
