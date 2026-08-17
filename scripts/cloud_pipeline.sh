#!/usr/bin/env bash
set -euo pipefail

# This script runs directly inside the npa-sonic SkyPilot image. The surrounding task
# supplies account-owned EULA and storage variables at launch time.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd -- "${SCRIPT_DIR}/.." && pwd)}"
SONIC_ROOT="${SONIC_ROOT:-/opt/sonic}"
BASE_PYTHON="${BASE_PYTHON:-${NPA_IMAGE_PYTHON:-/opt/npa/venv/bin/python}}"
SONIC_PYTHON="${SONIC_PYTHON:-/isaac-sim/python.sh}"
RUN_ID="${RUN_ID:-shadow-dance-$(date -u +%Y%m%dT%H%M%SZ)}"
EVIDENCE_S3_URI="${EVIDENCE_S3_URI:-}"
LOCAL_ONLY="${LOCAL_ONLY:-0}"
LADDER="${LADDER:-5,250,500,2000,4000}"
STAGE_WALLTIME_BUDGET_SECONDS="${STAGE_WALLTIME_BUDGET_SECONDS:-5:900,250:1800,500:3600,2000:12600,4000:21600}"
TRAINING_TIMEOUT_SECONDS="${TRAINING_TIMEOUT_SECONDS:-5:600,250:1500,500:3000,2000:10800,4000:19800}"
SUBMISSION_DEADLINE_UTC="${SUBMISSION_DEADLINE_UTC:-2026-08-17T06:59:00Z}"
FINALIZATION_RESERVE_SECONDS="${FINALIZATION_RESERVE_SECONDS:-7200}"
PORTAL_RESERVE_SECONDS="${PORTAL_RESERVE_SECONDS:-2700}"
RUN_STARTED_UTC="${RUN_STARTED_UTC:-$(date -u +%Y-%m-%dT%H:%M:%SZ)}"
MAX_WALLTIME_SECONDS="${MAX_WALLTIME_SECONDS:-36000}"
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
DATASET_ROOT="${PROJECT_ROOT}/data/generated-v2"
SPLITS_ROOT="${PROJECT_ROOT}/data/splits-v2"

if [[ "${ENTRANT_NVIDIA_EULA_ACCEPTED:-}" != "YES" || "${ACCEPT_EULA:-}" != "Y" ]]; then
  echo "Named entrant acceptance and ACCEPT_EULA=Y are required; refusing before any Isaac download." >&2
  exit 78
fi
case "${LOCAL_ONLY}" in
  0)
    if [[ -z "${EVIDENCE_S3_URI}" || "${EVIDENCE_S3_URI}" != s3://* ]]; then
      echo "EVIDENCE_S3_URI must be a run-scoped s3:// URI for a managed run." >&2
      exit 2
    fi
    ;;
  1)
    echo "LOCAL_ONLY=1: retaining evidence under ${RUN_ROOT}; remote uploads are disabled."
    ;;
  *)
    echo "LOCAL_ONLY must be exactly 0 or 1." >&2
    exit 2
    ;;
esac
if [[ ! -x "${BASE_PYTHON}" || ! -x "${SONIC_PYTHON}" ]]; then
  echo "Expected npa-sonic interpreters are missing." >&2
  exit 2
fi

mkdir -p "${RUN_ROOT}" "${RUNTIME_ROOT}/retention"
cd "${PROJECT_ROOT}"

upload_path() {
  local source="$1"
  local suffix="$2"
  if [[ "${LOCAL_ONLY}" == "1" ]]; then
    return 0
  fi
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
  for evidence_file in novelty.json ladder-plan.json ladder-outcome.json selection.json \
    final-comparison.json onnx-report.json; do
    if [[ -f "${RUN_ROOT}/${evidence_file}" ]]; then
      upload_path "${RUN_ROOT}/${evidence_file}" final || true
    fi
  done
  for identity_file in environment.txt base-model.sha256 sonic-assets.json; do
    if [[ -f "${RUN_ROOT}/${identity_file}" ]]; then
      upload_path "${RUN_ROOT}/${identity_file}" evidence || true
    fi
  done
  return "${status}"
}
trap persist_failure EXIT

"${BASE_PYTHON}" scripts/verify_dataset_bundle.py --profile dance-v2
find "${DATASET_ROOT}/train" -maxdepth 1 -type f -name 'retention_*.pkl' \
  -exec ln -sf '{}' "${RUNTIME_ROOT}/retention/" \;
grep '^retention_' "${SPLITS_ROOT}/train.txt" > "${RUNTIME_ROOT}/retention.txt"
if [[ "$(wc -l < "${RUNTIME_ROOT}/retention.txt")" -ne 10 ]]; then
  echo "Expected exactly ten retention motion keys." >&2
  exit 2
fi

{
  echo "run_id=${RUN_ID}"
  echo "started_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "local_only=${LOCAL_ONLY}"
  echo "submission_commit=${SUBMISSION_COMMIT:-unknown}"
  echo "runtime_sonic_commit=${SONIC_REPO_REF:-unknown}"
  echo "policy_image=${POLICY_IMAGE:-unknown}"
  echo "base_python=${BASE_PYTHON}"
  echo "base_python_version=$("${BASE_PYTHON}" --version 2>&1)"
  echo "sonic_python=${SONIC_PYTHON}"
  echo "ladder=${LADDER}"
  echo "stage_walltime_budget_seconds=${STAGE_WALLTIME_BUDGET_SECONDS}"
  echo "training_timeout_seconds=${TRAINING_TIMEOUT_SECONDS}"
  echo "submission_deadline_utc=${SUBMISSION_DEADLINE_UTC}"
  echo "finalization_reserve_seconds=${FINALIZATION_RESERVE_SECONDS}"
  echo "portal_reserve_seconds=${PORTAL_RESERVE_SECONDS}"
  echo "run_started_utc=${RUN_STARTED_UTC}"
  echo "max_walltime_seconds=${MAX_WALLTIME_SECONDS}"
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
asset_parent="${SONIC_ROOT}/gear_sonic/data/assets/robot_description"
hydrate_args=(
  "${BASE_PYTHON}" scripts/hydrate_sonic_assets.py
  --sonic-root "${SONIC_ROOT}"
  --report "${RUN_ROOT}/sonic-assets.json"
)
if [[ -w "${asset_parent}" ]]; then
  "${hydrate_args[@]}"
else
  command -v sudo >/dev/null || {
    echo "SONIC assets need hydration but ${asset_parent} is not writable and sudo is absent." >&2
    exit 2
  }
  echo "Hydrating the root-owned, pinned SONIC asset subtree with non-interactive sudo."
  sudo --non-interactive "${hydrate_args[@]}"
fi
upload_path "${RUN_ROOT}/sonic-assets.json" evidence
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
    heldout|test) motion_keys_file="${SPLITS_ROOT}/${split}.txt" ;;
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

run_eval "${BASE_CHECKPOINT}" stock heldout "${DATASET_ROOT}/heldout" 8 42
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

ladder_plan_status=0
effective_ladder="$("${BASE_PYTHON}" scripts/plan_checkpoint_ladder.py \
  --ladder "${LADDER}" \
  --stage-budgets "${STAGE_WALLTIME_BUDGET_SECONDS}" \
  --training-timeouts "${TRAINING_TIMEOUT_SECONDS}" \
  --run-started-utc "${RUN_STARTED_UTC}" \
  --max-walltime-seconds "${MAX_WALLTIME_SECONDS}" \
  --deadline-utc "${SUBMISSION_DEADLINE_UTC}" \
  --finalization-reserve-seconds "${FINALIZATION_RESERVE_SECONDS}" \
  --portal-reserve-seconds "${PORTAL_RESERVE_SECONDS}" \
  --output "${RUN_ROOT}/ladder-plan.json" \
  --print-scheduled-csv)" || ladder_plan_status="$?"
upload_path "${RUN_ROOT}/ladder-plan.json" final
if [[ "${ladder_plan_status}" -ne 0 || -z "${effective_ladder}" ]]; then
  echo "No checkpoint candidate fits before the evidence and portal reserves." >&2
  exit 4
fi

declare -A training_timeout_by_iteration=()
IFS=',' read -r -a training_timeout_specs <<< "${TRAINING_TIMEOUT_SECONDS}"
for timeout_spec in "${training_timeout_specs[@]}"; do
  timeout_iteration="${timeout_spec%%:*}"
  timeout_seconds="${timeout_spec#*:}"
  if [[ "${timeout_iteration}" == "${timeout_spec}" ]] || \
     ! [[ "${timeout_iteration}" =~ ^[1-9][0-9]*$ ]] || \
     ! [[ "${timeout_seconds}" =~ ^[1-9][0-9]*$ ]] || \
     [[ -n "${training_timeout_by_iteration[${timeout_iteration}]+present}" ]]; then
    echo "Invalid TRAINING_TIMEOUT_SECONDS entry: ${timeout_spec}" >&2
    exit 2
  fi
  training_timeout_by_iteration["${timeout_iteration}"]="${timeout_seconds}"
done

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
completed_iterations=()
timed_out_iteration=""
IFS=',' read -r -a ladder_values <<< "${effective_ladder}"
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
  training_timeout="${training_timeout_by_iteration[${iterations}]:-}"
  if [[ -z "${training_timeout}" ]]; then
    echo "No training timeout was configured for ${iterations} iterations." >&2
    exit 2
  fi
  stage_save_last_frequency="${SAVE_LAST_FREQUENCY}"
  if [[ "${stage_save_last_frequency}" == "stage" ]]; then
    # A deadline run can preserve earlier completed candidates instead of rewriting a
    # roughly checkpoint-sized last.pt every few iterations. The smoke still saves at 5.
    stage_save_last_frequency="${iterations}"
  elif ! [[ "${stage_save_last_frequency}" =~ ^[1-9][0-9]*$ ]]; then
    echo "SAVE_LAST_FREQUENCY must be a positive integer or 'stage'." >&2
    exit 2
  fi
  train_status=0
  timeout --signal=TERM --kill-after=15m "${training_timeout}s" env \
    SONIC_ROOT="${SONIC_ROOT}" SONIC_PYTHON="${SONIC_PYTHON}" \
    MOTION_DIR="${DATASET_ROOT}/train" CHECKPOINT="${BASE_CHECKPOINT}" \
    NUM_ENVS="${env_count}" ITERATIONS="${iterations}" RUN_NAME="${label}" \
    SEED="${TRAIN_SEED}" LEARNING_RATE="${LEARNING_RATE}" \
    REGULAR_SAVE_FREQUENCY="${REGULAR_SAVE_FREQUENCY}" \
    SAVE_LAST_FREQUENCY="${stage_save_last_frequency}" \
    OUTPUT_ROOT="${train_root}" bash scripts/train.sh || train_status="$?"
  if [[ "${train_status}" -ne 0 ]]; then
    if [[ -d "${train_root}" ]]; then
      upload_path "${train_root}" "train/${label}-incomplete" || true
    fi
    if [[ "${train_status}" -eq 124 ]] && \
       [[ "${#completed_iterations[@]}" -gt 0 ]]; then
      timed_out_iteration="${iterations}"
      echo "Training ${label} exceeded its deadline budget; selecting from completed candidates." >&2
      break
    fi
    exit "${train_status}"
  fi
  candidate_checkpoint="$(package_checkpoint "${train_root}" "${label}")"
  upload_path "${RUN_ROOT}/train/${label}" "train/${label}"
  upload_path "${RUN_ROOT}/checkpoints/${label}" "checkpoints/${label}"
  run_eval "${candidate_checkpoint}" "${label}" heldout \
    "${DATASET_ROOT}/heldout" 8 42
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
  completed_iterations+=("${iterations}")
done

if [[ "${#completed_iterations[@]}" -eq 0 ]]; then
  echo "No checkpoint candidate completed." >&2
  exit 4
fi
completed_csv="$(IFS=,; echo "${completed_iterations[*]}")"
outcome_args=(
  --plan "${RUN_ROOT}/ladder-plan.json"
  --completed "${completed_csv}"
  --output "${RUN_ROOT}/ladder-outcome.json"
)
if [[ -n "${timed_out_iteration}" ]]; then
  outcome_args+=(--timed-out "${timed_out_iteration}")
fi
"${BASE_PYTHON}" scripts/record_ladder_outcome.py "${outcome_args[@]}"
upload_path "${RUN_ROOT}/ladder-outcome.json" final

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
    "${DATASET_ROOT}/test" 8 "${test_seed}"
  run_eval "${selected_checkpoint}" "${selected_label}" test \
    "${DATASET_ROOT}/test" 8 "${test_seed}"
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

SONIC_ROOT="${SONIC_ROOT}" SONIC_PYTHON="${SONIC_PYTHON}" NUM_ENVS=8 \
  SEED="${RENDER_SEED}" MOTION_KEYS_FILE="${SPLITS_ROOT}/test.txt" \
  OUTPUT_DIR="${RUN_ROOT}/media/stock" \
  bash scripts/render_policy.sh "${BASE_CHECKPOINT}" stock "${DATASET_ROOT}/test"
SONIC_ROOT="${SONIC_ROOT}" SONIC_PYTHON="${SONIC_PYTHON}" NUM_ENVS=8 \
  SEED="${RENDER_SEED}" MOTION_KEYS_FILE="${SPLITS_ROOT}/test.txt" \
  OUTPUT_DIR="${RUN_ROOT}/media/selected" \
  bash scripts/render_policy.sh "${selected_checkpoint}" selected \
  "${DATASET_ROOT}/test"
cp "${PROJECT_ROOT}/media/reference-kinematic.mp4" \
  "${RUN_ROOT}/media/reference-kinematic.mp4"
"${BASE_PYTHON}" scripts/build_submission_video.py \
  --stock-dir "${RUN_ROOT}/media/stock" \
  --selected-dir "${RUN_ROOT}/media/selected" \
  --reference "${RUN_ROOT}/media/reference-kinematic.mp4" \
  --comparison "${RUN_ROOT}/final-comparison.json" \
  --motion-ids "${SPLITS_ROOT}/test.txt" \
  --output "${RUN_ROOT}/media/hero-before-after.mp4" \
  --manifest "${RUN_ROOT}/media/video-manifest.json" \
  --render-seed "${RENDER_SEED}"

SONIC_ROOT="${SONIC_ROOT}" SONIC_PYTHON="${SONIC_PYTHON}" \
  OUTPUT_DIR="$(dirname -- "${selected_checkpoint}")" \
  bash scripts/export_onnx.sh "${selected_checkpoint}" "${DATASET_ROOT}/test"
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
  "${RUN_ROOT}/final-comparison.json" "${RUN_ROOT}/ladder-plan.json" \
  "${RUN_ROOT}/ladder-outcome.json" "${release_dir}/model/"
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
    --dataset-repo "${HF_DATASET_REPO:-cristpierce/shadow-dance-v2}" \
    --report "${RUN_ROOT}/huggingface-model-publication.json"
  upload_path "${RUN_ROOT}/huggingface-model-publication.json" final
fi
echo "Shadow Dance cloud pipeline completed: ${RUN_ID}"
