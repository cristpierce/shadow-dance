#!/usr/bin/env bash
set -euo pipefail

# This script runs directly inside the npa-sonic SkyPilot image. The surrounding task
# supplies account-owned EULA and storage variables at launch time.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd -- "${SCRIPT_DIR}/.." && pwd)}"
SONIC_ROOT="${SONIC_ROOT:-/opt/sonic}"
BASE_PYTHON="${BASE_PYTHON:-/opt/npa/sim/venv/bin/python}"
SONIC_PYTHON="${SONIC_PYTHON:-/isaac-sim/python.sh}"
RUN_ID="${RUN_ID:-shadow-dance-$(date -u +%Y%m%dT%H%M%SZ)}"
EVIDENCE_S3_URI="${EVIDENCE_S3_URI:-}"
LADDER="${LADDER:-5,500,4000}"
FINAL_TEST_SEEDS="${FINAL_TEST_SEEDS:-101,202,303}"
SMOKE_NUM_ENVS="${SMOKE_NUM_ENVS:-64}"
MAIN_NUM_ENVS="${MAIN_NUM_ENVS:-512}"
TRAIN_SEED="${TRAIN_SEED:-42}"
LEARNING_RATE="${LEARNING_RATE:-2e-5}"
REGULAR_SAVE_FREQUENCY="${REGULAR_SAVE_FREQUENCY:-1000000}"
SAVE_LAST_FREQUENCY="${SAVE_LAST_FREQUENCY:-5}"
RENDER_SEED="${RENDER_SEED:-303}"
RUN_ROOT="${PROJECT_ROOT}/outputs/cloud/${RUN_ID}"
RUNTIME_ROOT="${PROJECT_ROOT}/.runtime/${RUN_ID}"
BASE_CHECKPOINT="${SONIC_ROOT}/sonic_release/last.pt"
BASE_CHECKPOINT_SHA256="e6bdab3f64a39336b3d41877d4f497d05f58af275f288ec0e6746c283ded8909"
BASE_CONFIG_SHA256="f08187795fa16a839a28bc1c18e0555d38d9420e03733744341cdcb56ab629c7"

if [[ "${OMNI_KIT_ACCEPT_EULA:-}" != "YES" || "${ISAACSIM_ACCEPT_EULA:-}" != "YES" ]]; then
  echo "Explicit NVIDIA EULA acceptance is required; refusing before any Isaac download." >&2
  exit 78
fi
if [[ -z "${EVIDENCE_S3_URI}" || "${EVIDENCE_S3_URI}" != s3://* ]]; then
  echo "EVIDENCE_S3_URI must be a run-scoped s3:// URI." >&2
  exit 2
fi
if [[ ! -x "${BASE_PYTHON}" || ! -x "${SONIC_PYTHON}" ]]; then
  echo "Expected npa-sonic interpreters are missing." >&2
  exit 2
fi

mkdir -p "${RUN_ROOT}" "${RUNTIME_ROOT}/retention"
cd "${PROJECT_ROOT}"

upload_path() {
  local source="$1"
  local suffix="$2"
  "${BASE_PYTHON}" scripts/upload_tree.py \
    "${source}" "${EVIDENCE_S3_URI%/}/${suffix#/}"
}

persist_failure() {
  local status="$?"
  if [[ "${status}" -eq 0 ]]; then
    return 0
  fi
  {
    echo "exit_status=${status}"
    echo "failed_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } > "${RUN_ROOT}/failure.txt"
  upload_path "${RUN_ROOT}/failure.txt" failure-recovery || true
  for directory in train checkpoints eval summaries; do
    if [[ -d "${RUN_ROOT}/${directory}" ]]; then
      upload_path "${RUN_ROOT}/${directory}" "${directory}" || true
    fi
  done
  if [[ -d "${RUN_ROOT}/release" ]]; then
    upload_path "${RUN_ROOT}/release" final/release || true
  fi
  if [[ -d "${RUN_ROOT}/media" ]]; then
    upload_path "${RUN_ROOT}/media" final/media || true
  fi
  for evidence_file in novelty.json selection.json final-comparison.json onnx-report.json; do
    if [[ -f "${RUN_ROOT}/${evidence_file}" ]]; then
      upload_path "${RUN_ROOT}/${evidence_file}" final || true
    fi
  done
  for identity_file in environment.txt base-model.sha256; do
    if [[ -f "${RUN_ROOT}/${identity_file}" ]]; then
      upload_path "${RUN_ROOT}/${identity_file}" evidence || true
    fi
  done
  return "${status}"
}
trap persist_failure EXIT

"${BASE_PYTHON}" scripts/verify_dataset_bundle.py
find "${PROJECT_ROOT}/data/generated/train" -maxdepth 1 -type f -name 'retention_*.pkl' \
  -exec ln -sf '{}' "${RUNTIME_ROOT}/retention/" \;
grep '^retention_' "${PROJECT_ROOT}/data/splits/train.txt" > "${RUNTIME_ROOT}/retention.txt"
if [[ "$(wc -l < "${RUNTIME_ROOT}/retention.txt")" -ne 10 ]]; then
  echo "Expected exactly ten retention motion keys." >&2
  exit 2
fi

{
  echo "run_id=${RUN_ID}"
  echo "started_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "submission_commit=${SUBMISSION_COMMIT:-unknown}"
  echo "runtime_sonic_commit=${SONIC_REPO_REF:-unknown}"
  echo "policy_image=${POLICY_IMAGE:-unknown}"
  echo "ladder=${LADDER}"
  echo "final_test_seeds=${FINAL_TEST_SEEDS}"
  echo "max_walltime=${MAX_WALLTIME:-not_wrapped}"
  echo "smoke_num_envs=${SMOKE_NUM_ENVS}"
  echo "main_num_envs=${MAIN_NUM_ENVS}"
  echo "train_seed=${TRAIN_SEED}"
  echo "actor_learning_rate=${LEARNING_RATE}"
  echo "regular_save_frequency=${REGULAR_SAVE_FREQUENCY}"
  echo "save_last_frequency=${SAVE_LAST_FREQUENCY}"
  echo "render_seed=${RENDER_SEED}"
  echo "project_head=$(git -C "${PROJECT_ROOT}" rev-parse HEAD)"
  nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
} > "${RUN_ROOT}/environment.txt"

if [[ -n "${SUBMISSION_COMMIT:-}" ]] && \
   [[ "$(git -C "${PROJECT_ROOT}" rev-parse HEAD)" != "${SUBMISSION_COMMIT}" ]]; then
  echo "Submission checkout does not match SUBMISSION_COMMIT." >&2
  exit 2
fi

export HF_HUB_DISABLE_XET=1
"${BASE_PYTHON}" scripts/download_base_model.py --output-dir "${SONIC_ROOT}"
actual_checkpoint_hash="$(sha256sum "${BASE_CHECKPOINT}" | cut -d' ' -f1)"
if [[ "${actual_checkpoint_hash}" != "${BASE_CHECKPOINT_SHA256}" ]]; then
  echo "Base checkpoint hash mismatch: ${actual_checkpoint_hash}" >&2
  exit 2
fi
actual_config_hash="$(sha256sum "${SONIC_ROOT}/sonic_release/config.yaml" | cut -d' ' -f1)"
if [[ "${actual_config_hash}" != "${BASE_CONFIG_SHA256}" ]]; then
  echo "Base config hash mismatch: ${actual_config_hash}" >&2
  exit 2
fi
{
  echo "${actual_checkpoint_hash}  ${BASE_CHECKPOINT}"
  echo "${actual_config_hash}  ${SONIC_ROOT}/sonic_release/config.yaml"
} > "${RUN_ROOT}/base-model.sha256"

# Cold start downloads Isaac into the mounted cache. The image refuses this call without
# both operator-supplied acceptance variables checked above.
"${SONIC_PYTHON}" -c \
  'import isaaclab, torch; print("Isaac bootstrap OK", torch.__version__, torch.cuda.get_device_name(0))'

run_eval() {
  local checkpoint="$1"
  local label="$2"
  local split="$3"
  local motion_dir="$4"
  local count="$5"
  local seed="$6"
  local motion_keys_file
  case "${split}" in
    heldout|test) motion_keys_file="${PROJECT_ROOT}/data/splits/${split}.txt" ;;
    retention) motion_keys_file="${RUNTIME_ROOT}/retention.txt" ;;
    *) echo "Unsupported evaluation split: ${split}" >&2; exit 2 ;;
  esac
  local output_dir="${RUN_ROOT}/eval/${label}-${split}-seed-${seed}"
  SONIC_ROOT="${SONIC_ROOT}" SONIC_PYTHON="${SONIC_PYTHON}" NUM_ENVS="${count}" \
    SEED="${seed}" MOTION_KEYS_FILE="${motion_keys_file}" \
    OUTPUT_DIR="${output_dir}" \
    bash scripts/evaluate.sh "${checkpoint}" "${label}-${split}-seed-${seed}" "${motion_dir}"
  "${BASE_PYTHON}" scripts/summarize_eval.py "${output_dir}/metrics_eval.json" \
    --label "${label}" --split "${split}" --seed "${seed}" \
    --expected-motion-dir "${motion_dir}" \
    --output "${RUN_ROOT}/summaries/${label}-${split}-seed-${seed}.json"
}

run_eval "${BASE_CHECKPOINT}" stock heldout "${PROJECT_ROOT}/data/generated/heldout" 4 42
upload_path "${RUN_ROOT}/eval/stock-heldout-seed-42" eval/stock-heldout-seed-42
upload_path "${RUN_ROOT}/summaries/stock-heldout-seed-42.json" summaries
run_eval "${BASE_CHECKPOINT}" stock retention "${RUNTIME_ROOT}/retention" 10 42
upload_path "${RUN_ROOT}/eval/stock-retention-seed-42" eval/stock-retention-seed-42
upload_path "${RUN_ROOT}/summaries/stock-retention-seed-42.json" summaries
novelty_status=0
"${BASE_PYTHON}" scripts/check_novelty.py \
  "${RUN_ROOT}/summaries/stock-heldout-seed-42.json" \
  --output "${RUN_ROOT}/novelty.json" || novelty_status="$?"
upload_path "${RUN_ROOT}" baseline
if [[ "${novelty_status}" -ne 0 ]]; then
  exit "${novelty_status}"
fi

package_checkpoint() {
  local train_root="$1"
  local label="$2"
  local checkpoint
  checkpoint="$(find "${train_root}" -type f -name last.pt -printf '%T@ %p\n' \
    | sort -nr | head -n1 | cut -d' ' -f2-)"
  if [[ -z "${checkpoint}" || ! -f "${checkpoint}" ]]; then
    echo "No last.pt found under ${train_root}" >&2
    exit 2
  fi
  local source_dir
  source_dir="$(dirname "${checkpoint}")"
  local config="${source_dir}/config.yaml"
  if [[ ! -f "${config}" ]]; then
    config="$(dirname "${source_dir}")/config.yaml"
  fi
  if [[ ! -f "${config}" ]]; then
    echo "No config.yaml found for ${checkpoint}" >&2
    exit 2
  fi
  local target="${RUN_ROOT}/checkpoints/${label}"
  mkdir -p "${target}"
  cp "${checkpoint}" "${target}/last.pt"
  cp "${config}" "${target}/config.yaml"
  sha256sum "${target}/last.pt" > "${target}/SHA256SUMS"
  printf '%s\n' "${target}/last.pt"
}

candidate_args=()
IFS=',' read -r -a ladder_values <<< "${LADDER}"
for iterations in "${ladder_values[@]}"; do
  if ! [[ "${iterations}" =~ ^[1-9][0-9]*$ ]]; then
    echo "Invalid LADDER value: ${iterations}" >&2
    exit 2
  fi
  label="stage-${iterations}"
  train_root="${RUN_ROOT}/train/${label}"
  env_count="${MAIN_NUM_ENVS}"
  if [[ "${iterations}" == "5" ]]; then
    env_count="${SMOKE_NUM_ENVS}"
  fi
  SONIC_ROOT="${SONIC_ROOT}" SONIC_PYTHON="${SONIC_PYTHON}" \
    MOTION_DIR="${PROJECT_ROOT}/data/generated/train" CHECKPOINT="${BASE_CHECKPOINT}" \
    NUM_ENVS="${env_count}" ITERATIONS="${iterations}" RUN_NAME="${label}" \
    SEED="${TRAIN_SEED}" LEARNING_RATE="${LEARNING_RATE}" \
    REGULAR_SAVE_FREQUENCY="${REGULAR_SAVE_FREQUENCY}" \
    SAVE_LAST_FREQUENCY="${SAVE_LAST_FREQUENCY}" \
    OUTPUT_ROOT="${train_root}" bash scripts/train.sh
  candidate_checkpoint="$(package_checkpoint "${train_root}" "${label}")"
  upload_path "${RUN_ROOT}/train/${label}" "train/${label}"
  upload_path "${RUN_ROOT}/checkpoints/${label}" "checkpoints/${label}"
  run_eval "${candidate_checkpoint}" "${label}" heldout \
    "${PROJECT_ROOT}/data/generated/heldout" 4 42
  upload_path "${RUN_ROOT}/eval/${label}-heldout-seed-42" \
    "eval/${label}-heldout-seed-42"
  upload_path "${RUN_ROOT}/summaries/${label}-heldout-seed-42.json" summaries
  run_eval "${candidate_checkpoint}" "${label}" retention \
    "${RUNTIME_ROOT}/retention" 10 42
  upload_path "${RUN_ROOT}/eval/${label}-retention-seed-42" \
    "eval/${label}-retention-seed-42"
  upload_path "${RUN_ROOT}/summaries/${label}-retention-seed-42.json" summaries
  candidate_args+=(
    --candidate "${label}" "${candidate_checkpoint}"
    "${RUN_ROOT}/summaries/${label}-heldout-seed-42.json"
    "${RUN_ROOT}/summaries/${label}-retention-seed-42.json"
  )
done

"${BASE_PYTHON}" scripts/select_checkpoint.py \
  --stock-heldout "${RUN_ROOT}/summaries/stock-heldout-seed-42.json" \
  --stock-retention "${RUN_ROOT}/summaries/stock-retention-seed-42.json" \
  "${candidate_args[@]}" --output "${RUN_ROOT}/selection.json" --require-eligible
selected_checkpoint="$("${BASE_PYTHON}" -c \
  'import json,sys; print(json.load(open(sys.argv[1]))["selected"]["checkpoint"])' \
  "${RUN_ROOT}/selection.json")"
selected_label="$("${BASE_PYTHON}" -c \
  'import json,sys; print(json.load(open(sys.argv[1]))["selected"]["label"])' \
  "${RUN_ROOT}/selection.json")"
upload_path "${RUN_ROOT}/selection.json" final

# The final test split is first evaluated only after the checkpoint winner is frozen.
stock_test_summaries=()
selected_test_summaries=()
IFS=',' read -r -a final_test_seeds <<< "${FINAL_TEST_SEEDS}"
if [[ "${#final_test_seeds[@]}" -lt 3 ]]; then
  echo "FINAL_TEST_SEEDS must contain at least three independent seeds." >&2
  exit 2
fi
declare -A seen_test_seeds=()
for test_seed in "${final_test_seeds[@]}"; do
  if ! [[ "${test_seed}" =~ ^[0-9]+$ ]]; then
    echo "Invalid final-test seed: ${test_seed}" >&2
    exit 2
  fi
  if [[ -n "${seen_test_seeds[${test_seed}]+present}" ]]; then
    echo "Duplicate final-test seed: ${test_seed}" >&2
    exit 2
  fi
  seen_test_seeds["${test_seed}"]=1
done
for test_seed in "${final_test_seeds[@]}"; do
  stock_summary="${RUN_ROOT}/summaries/stock-test-seed-${test_seed}.json"
  selected_summary="${RUN_ROOT}/summaries/${selected_label}-test-seed-${test_seed}.json"
  run_eval "${BASE_CHECKPOINT}" stock test \
    "${PROJECT_ROOT}/data/generated/test" 4 "${test_seed}"
  run_eval "${selected_checkpoint}" "${selected_label}" test \
    "${PROJECT_ROOT}/data/generated/test" 4 "${test_seed}"
  upload_path "${RUN_ROOT}/eval/stock-test-seed-${test_seed}" \
    "eval/stock-test-seed-${test_seed}"
  upload_path "${RUN_ROOT}/eval/${selected_label}-test-seed-${test_seed}" \
    "eval/${selected_label}-test-seed-${test_seed}"
  upload_path "${stock_summary}" summaries
  upload_path "${selected_summary}" summaries
  stock_test_summaries+=("${stock_summary}")
  selected_test_summaries+=("${selected_summary}")
done
"${BASE_PYTHON}" scripts/aggregate_eval.py "${stock_test_summaries[@]}" \
  --label stock --split test \
  --output "${RUN_ROOT}/summaries/stock-test-aggregate.json"
"${BASE_PYTHON}" scripts/aggregate_eval.py "${selected_test_summaries[@]}" \
  --label "${selected_label}" --split test \
  --output "${RUN_ROOT}/summaries/${selected_label}-test-aggregate.json"
"${BASE_PYTHON}" scripts/build_final_comparison.py \
  --selection "${RUN_ROOT}/selection.json" \
  --stock-test "${RUN_ROOT}/summaries/stock-test-aggregate.json" \
  --selected-test "${RUN_ROOT}/summaries/${selected_label}-test-aggregate.json" \
  --output "${RUN_ROOT}/final-comparison.json"
upload_path "${RUN_ROOT}/summaries/stock-test-aggregate.json" summaries
upload_path "${RUN_ROOT}/summaries/${selected_label}-test-aggregate.json" summaries
upload_path "${RUN_ROOT}/final-comparison.json" final

SONIC_ROOT="${SONIC_ROOT}" SONIC_PYTHON="${SONIC_PYTHON}" NUM_ENVS=4 \
  SEED="${RENDER_SEED}" MOTION_KEYS_FILE="${PROJECT_ROOT}/data/splits/test.txt" \
  OUTPUT_DIR="${RUN_ROOT}/media/stock" \
  bash scripts/render_policy.sh "${BASE_CHECKPOINT}" stock "${PROJECT_ROOT}/data/generated/test"
SONIC_ROOT="${SONIC_ROOT}" SONIC_PYTHON="${SONIC_PYTHON}" NUM_ENVS=4 \
  SEED="${RENDER_SEED}" MOTION_KEYS_FILE="${PROJECT_ROOT}/data/splits/test.txt" \
  OUTPUT_DIR="${RUN_ROOT}/media/selected" \
  bash scripts/render_policy.sh "${selected_checkpoint}" selected \
  "${PROJECT_ROOT}/data/generated/test"
cp "${PROJECT_ROOT}/media/reference-kinematic.mp4" \
  "${RUN_ROOT}/media/reference-kinematic.mp4"
"${BASE_PYTHON}" scripts/build_submission_video.py \
  --stock-dir "${RUN_ROOT}/media/stock" \
  --selected-dir "${RUN_ROOT}/media/selected" \
  --reference "${RUN_ROOT}/media/reference-kinematic.mp4" \
  --comparison "${RUN_ROOT}/final-comparison.json" \
  --motion-ids "${PROJECT_ROOT}/data/splits/test.txt" \
  --output "${RUN_ROOT}/media/hero-before-after.mp4" \
  --manifest "${RUN_ROOT}/media/video-manifest.json" \
  --render-seed "${RENDER_SEED}"

SONIC_ROOT="${SONIC_ROOT}" SONIC_PYTHON="${SONIC_PYTHON}" \
  OUTPUT_DIR="$(dirname -- "${selected_checkpoint}")" \
  bash scripts/export_onnx.sh "${selected_checkpoint}" "${PROJECT_ROOT}/data/generated/test"
exported_dir="$(dirname "${selected_checkpoint}")/exported"
if ! find "${exported_dir}" -maxdepth 1 -type f -name '*.onnx' -print -quit | grep -q .; then
  echo "ONNX export produced no graphs under ${exported_dir}" >&2
  exit 2
fi
verify_venv="${RUNTIME_ROOT}/onnx-verify-venv"
if [[ ! -x "${verify_venv}/bin/python" ]]; then
  "${BASE_PYTHON}" -m venv --system-site-packages "${verify_venv}"
fi
"${verify_venv}/bin/python" -m pip install --disable-pip-version-check -q \
  --only-binary=:all: --no-deps --require-hashes \
  -r requirements/cloud-onnx-runtime.txt
"${verify_venv}/bin/python" scripts/verify_artifacts.py "${exported_dir}" \
  --output "${RUN_ROOT}/onnx-report.json"

release_dir="${RUN_ROOT}/release"
mkdir -p "${release_dir}/model"
cp "${selected_checkpoint}" "${release_dir}/model/last.pt"
cp "$(dirname "${selected_checkpoint}")/config.yaml" "${release_dir}/model/config.yaml"
if [[ -f "$(dirname "${selected_checkpoint}")/model_config.yaml" ]]; then
  cp "$(dirname "${selected_checkpoint}")/model_config.yaml" "${release_dir}/model/"
fi
cp "${exported_dir}"/*.onnx "${release_dir}/model/"
cp "${RUN_ROOT}/onnx-report.json" "${RUN_ROOT}/novelty.json" "${RUN_ROOT}/selection.json" \
  "${RUN_ROOT}/final-comparison.json" "${release_dir}/model/"
cp "${SONIC_ROOT}/LICENSE" "${release_dir}/model/GEAR-SONIC-DUAL-LICENSE"
# A recovery run may reuse a partially populated run directory. Remove the old
# inventory before expanding the glob so SHA256SUMS can never hash itself.
rm -f "${release_dir}/model/SHA256SUMS"
(cd "${release_dir}/model" && sha256sum ./* > SHA256SUMS)
upload_path "${release_dir}" final/release
upload_path "${RUN_ROOT}/media" final/media
upload_path "${RUN_ROOT}/onnx-report.json" final
upload_path "${RUN_ROOT}/selection.json" final
upload_path "${RUN_ROOT}/final-comparison.json" final
if [[ -n "${HF_MODEL_REPO:-}" ]]; then
  if [[ -z "${HF_TOKEN:-}" ]]; then
    echo "HF_MODEL_REPO was set but HF_TOKEN was not supplied as a secret." >&2
    exit 2
  fi
  "${BASE_PYTHON}" scripts/publish_model.py \
    --run-root "${RUN_ROOT}" \
    --repo-id "${HF_MODEL_REPO}" \
    --dataset-repo "${HF_DATASET_REPO:-cristpierce/shadow-dip-v1}" \
    --report "${RUN_ROOT}/huggingface-model-publication.json"
  upload_path "${RUN_ROOT}/huggingface-model-publication.json" final
fi
echo "Shadow Dance cloud pipeline completed: ${RUN_ID}"
