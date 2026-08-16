# Shadow Dance cloud execution and publication runbook

**Prepared:** 2026-08-13 PT; runtime route corrected 2026-08-16 PT
**Target:** Nebius RTX PRO 6000 Managed Kubernetes, public NPA runtime-fetch SONIC
image, frozen Shadow Dance commit
**Rule:** do not start paid compute until the immutable inputs, storage, and licences
below all pass.

This is the operator handoff for the stock baseline, novelty gate, 5/250/500/4,000 checkpoint
ladder, selection-validation and retention evaluation, untouched final testing, policy
renders, ONNX validation, S3 evidence, and optional Hugging Face model publication. The
final test repeats all four motions under three independent simulator seeds for each
policy. The job is intentionally one serial task so the checkpoint and evidence chain
cannot drift across machines.

## The six things only the entrant can do

1. **Accept NVIDIA's terms in your own name.** Read the
   [current Omniverse/AI product-specific terms](https://www.nvidia.com/en-us/agreements/enterprise-software/product-specific-terms-for-ai-products/),
   [Isaac Sim Additional Software and Materials Licence](https://docs.isaacsim.omniverse.nvidia.com/latest/common/license-isaac-sim-additional.html),
   and [NVIDIA Software Licence Agreement](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-software-license-agreement/).
   Then send this exact statement to the project operator:

   > I accept the NVIDIA Omniverse Licence Agreement, NVIDIA Isaac Sim Additional
   > Software and Materials Licence, and NVIDIA Software Licence Agreement for this
   > SuperSONIC project, and authorize ACCEPT_EULA=Y and
   > ENTRANT_NVIDIA_EULA_ACCEPTED=YES for this run.

   General permission to work on the project is not legal acceptance of named
   third-party agreements. The pipeline exits `78` before downloading Isaac unless the
   run-scoped values are exactly `ACCEPT_EULA=Y` and
   `ENTRANT_NVIDIA_EULA_ACCEPTED=YES`. The second marker is deliberately project-owned:
   unlike NPA's product default, it cannot be synthesized by the workflow materializer.

2. **Complete interactive Nebius login and confirm usable credit/quota.** The portal's
   "applied" state is not proof that the $50 credit has posted. In WSL, run
   `cd /home/crist/npa-shadow-operator && .venv/bin/npa configure`, select a
   `us-central1` project, and confirm RTX PRO 6000 Managed Kubernetes quota. The
   supported cluster provisioning command is in section 1; dry-run it before creating
   the GPU node.

3. **Complete Hugging Face login locally.** Never paste a token into chat, Git, YAML, or
   a shell command argument. Run `.venv\Scripts\hf.exe auth login` interactively in the
   Windows project, and let WSL `npa configure` store/resolve `HF_TOKEN` through its
   protected credential prompt for cloud publication. Use a token authorized to create
   and update the two public repositories (a download-only token is insufficient).
   Confirm the intended Hugging Face handle; no public `cristpierce` profile or repos
   were visible through the public API on August 14. If that namespace is created, the
   dataset and final model defaults are `cristpierce/shadow-dip-v1` and
   `cristpierce/shadow-dance-sonic`.

4. **Have the teammate merge the canonical GitHub PR and confirm their registered
   name.** The
   current account has read-only access to `Durp06/shadow-dance`; the working changes are
   in [PR #1](https://github.com/Durp06/shadow-dance/pull/1). A registered team member
   must confirm whether the portal displays `Myles`, `Myles Shetty`, or another exact
   registered form before the final copy is frozen. The repository and historical
   handoff identify the teammate as Myles Shetty (`Durp06`).

5. **Obtain the organizer's WBT-Bench package.** The public challenge page says it
   opened in late July, but no package or command appears in the supplied portal
   resources or the current public NVIDIA/Nebius repositories. Send this in the
   challenge Discord help desk:

   > Team SELTZER is submitting Shadow Dance in Performance Arts. Could an organizer
   > share the current Trial 03 WBT-Bench package, exact scoring command, and accepted
   > report format? The public brief says it opened in late July, but the portal resource
   > cards currently expose Studio, SONIC, the training guide, BONES-SEED, and Nebius
   > without a WBT-Bench link. We will label our owned walk/turn retention suite as a
   > proxy unless we can run the official package.

6. **Publish the real policy comparison and submit the portal entry.** A signed-in team
   member must upload the final hash-verified simulator video to YouTube if the portal
   requires that host, check every public link while logged out, and change the Ultimate
   Bots entry from `DRAFT` to submitted. The kinematic reference video is not a substitute.

Everything else in this runbook is automated or already prepared.

### Local GPU contingency

This workstation exposes an RTX 5070 Ti Laptop GPU with 12,227 MiB VRAM to WSL2, but
the WSL VM has 15 GiB RAM. NVIDIA's current
[Isaac Lab requirements](https://isaac-sim.github.io/IsaacLab/develop/source/setup/installation/index.html#system-requirements)
recommend at least 32 GB RAM and 16 GB GPU VRAM for full Isaac Sim workflows, with more
for training. The laptop is therefore below the supported floor. After the named EULA
acceptance, it may be used only as a best-effort 16-environment headless smoke fallback;
do not plan the 500/4,000-iteration evidence run around it or download Isaac beforehand.

## 1. Install the operator environment in WSL2

NPA supports Windows through WSL2, not native Windows. Keep its checkout under the
Linux home directory for performance.

```bash
cd ~
git clone https://github.com/nebius/nebius-physical-ai.git npa-shadow-operator
cd npa-shadow-operator
git checkout 43ffee689b02a117ff4eb2c32f7057b39bcef030

~/.local/bin/uv venv .venv
source .venv/bin/activate
~/.local/bin/uv pip install -e npa

curl -fsSL https://storage.eu-north1.nebius.cloud/cli/install.sh \
  | NEBIUS_CLI_VERSION=0.12.254 bash
export PATH="${HOME}/.nebius/bin:${PATH}"

npa --version
npa configure
npa skypilot bootstrap
npa skypilot status
npa skypilot verify
npa workbench health preflight --json
```

On this machine Ubuntu's system Python lacks `ensurepip`, so the ordinary SkyPilot
bootstrap cannot create its nested venv. The following no-sudo fallback was verified;
NPA then recognizes the exact environment, writes its marker, and passes `verify`:

```bash
export PATH="${HOME}/.local/bin:${PATH}"
uv venv "${HOME}/.npa/skypilot-venv"
uv pip install \
  --python "${HOME}/.npa/skypilot-venv/bin/python" \
  --constraint \
    "${HOME}/npa-shadow-operator/npa/src/npa/cli/skypilot/constraints-0.12.2.txt" \
  'skypilot[nebius,kubernetes]==0.12.2'
cd "${HOME}/npa-shadow-operator"
.venv/bin/npa skypilot bootstrap
.venv/bin/npa skypilot verify
```

If the pinned NPA commit is no longer reachable, stop and record the replacement commit;
do not silently train against a moving checkout. `npa configure` is interactive and may
open a browser. Its project/storage credentials remain in the user's WSL home.

Local state on August 14: the exact 83,198,114-byte Linux/amd64 binary reports `Nebius
CLI 0.12.254 2026-07-31T13-50-18Z`. The CLI has no `~/.nebius/config.yaml` profile yet,
so it cannot access or create cloud resources until the entrant completes the
interactive profile/login step.

Resolve the non-secret launch values from that configuration. The active SONIC image is
public on GHCR, so no account-specific registry or image-pull secret is needed:

```bash
export NPA_PROJECT=default  # replace if npa configure used another alias
export NPA_STORAGE_URI="$(python -c \
  'from npa.clients.config import resolve_project_storage; print(resolve_project_storage().checkpoint_bucket)')"
export NPA_S3_BUCKET="$(python -c \
  'import os; from urllib.parse import urlparse; value=os.environ["NPA_STORAGE_URI"]; parsed=urlparse(value if "://" in value else "s3://" + value); print(parsed.netloc)')"
export NPA_S3_BASE_PREFIX="$(python -c \
  'import os; from urllib.parse import urlparse; value=os.environ["NPA_STORAGE_URI"]; parsed=urlparse(value if "://" in value else "s3://" + value); print(parsed.path.strip("/"))')"
export NPA_S3_ENDPOINT="$(python -c \
  'from npa.clients.config import resolve_project_storage; print(resolve_project_storage().endpoint_url)')"
export NPA_REGISTRY=ghcr.io/nebius/nebius-physical-ai
export POLICY_IMAGE="${NPA_REGISTRY}/npa-sonic@sha256:c9ba0996b28f54b013e36da689638b386a7ef9c0c8c4413fc4b3c72ff1a808bb"

printf 'project=%s\nregistry=%s\nstorage_uri=%s\nbucket=%s\nbase_prefix=%s\nendpoint=%s\nimage=%s\n' \
  "$NPA_PROJECT" "$NPA_REGISTRY" "$NPA_STORAGE_URI" "$NPA_S3_BUCKET" \
  "$NPA_S3_BASE_PREFIX" "$NPA_S3_ENDPOINT" "$POLICY_IMAGE"
test -n "$NPA_S3_BUCKET"
test -n "$NPA_S3_ENDPOINT"
case "$POLICY_IMAGE" in
  ghcr.io/nebius/nebius-physical-ai/npa-sonic@sha256:c9ba0996b28f54b013e36da689638b386a7ef9c0c8c4413fc4b3c72ff1a808bb) ;;
  *) echo "Unexpected SONIC image: $POLICY_IMAGE" >&2; exit 2 ;;
esac
```

The exact tag and digest were anonymously resolved from GHCR on August 16. Current NPA
marks the former baked L40S digest as quarantined and rejects it; do not restore that
route. The active image contains no Isaac bytes and depends on GPU Operator driver
mounts, so it must run on the supported RTX PRO 6000 Kubernetes target.

After visible credit and quota are confirmed, provision only the minimal supported
cluster. The dry run is mandatory; the second command creates billable nodes:

```bash
npa provision-if-absent --project "$NPA_PROJECT" \
  --cpu-nodes 1 --cpu-platform cpu-d3 --cpu-preset 8vcpu-32gb \
  --gpu-nodes 1 --gpu-platform gpu-rtx6000 \
  --gpu-preset 1gpu-24vcpu-218gb --on-demand \
  --dry-run --output-format json
npa provision-if-absent --project "$NPA_PROJECT" \
  --cpu-nodes 1 --cpu-platform cpu-d3 --cpu-preset 8vcpu-32gb \
  --gpu-nodes 1 --gpu-platform gpu-rtx6000 \
  --gpu-preset 1gpu-24vcpu-218gb --on-demand

eval "$(npa configure --show --env)"
export KUBE_CONTEXT="$NPA_KUBE_CONTEXT"
export NPA_REGISTRY=ghcr.io/nebius/nebius-physical-ai
export POLICY_IMAGE="${NPA_REGISTRY}/npa-sonic@sha256:c9ba0996b28f54b013e36da689638b386a7ef9c0c8c4413fc4b3c72ff1a808bb"
npa workbench workflow gpus --context "$KUBE_CONTEXT" --json
```

The final command must report an allocatable RTX PRO 6000 accelerator before launch.

## 2. Freeze and publish the owned dataset

Use the pushed branch commit even if the canonical PR has not yet merged. From WSL:

```bash
export SHADOW_REPO=/mnt/c/Users/crist/dev/projects/shadow-dance
cd "$SHADOW_REPO"
git status --short
git fetch fork feature/supersonic-submission
export SUBMISSION_COMMIT="$(git rev-parse feature/supersonic-submission)"
git ls-remote fork "refs/heads/feature/supersonic-submission" \
  | grep -F "$SUBMISSION_COMMIT"
```

The NPA operator venv intentionally does not carry the Hugging Face publishing extra.
Run the dataset checks and publication from PowerShell in the project venv:

```powershell
Set-Location C:\Users\crist\dev\projects\shadow-dance
.venv\Scripts\python.exe scripts\verify_dataset_bundle.py
.venv\Scripts\python.exe scripts\publish_dataset.py `
  --repo-id cristpierce/shadow-dip-v1 --dry-run
.venv\Scripts\hf.exe auth login
.venv\Scripts\python.exe scripts\publish_dataset.py `
  --repo-id cristpierce/shadow-dip-v1 `
  --report .runtime\huggingface-dataset-publication.json
```

Verify
`https://huggingface.co/datasets/cristpierce/shadow-dip-v1` in a logged-out browser and
record its immutable commit URL. The publisher refuses missing PKLs or a failed QA
report.

## 3. Materialize a guaranteed no-compute launch plan

Do this only after recording the entrant's explicit EULA acceptance. It renders the
exact job but does not schedule a GPU:

```bash
cd ~/npa-shadow-operator
source .venv/bin/activate

export SHADOW_REPO=/mnt/c/Users/crist/dev/projects/shadow-dance
export SUBMISSION_COMMIT="$(git -C "$SHADOW_REPO" rev-parse feature/supersonic-submission)"
export RUN_ID="shadow-dance-$(date -u +%Y%m%dT%H%M%SZ)"
export NPA_S3_PREFIX="${NPA_S3_BASE_PREFIX:+${NPA_S3_BASE_PREFIX}/}shadow-dance/${RUN_ID}"
export EVIDENCE_S3_URI="s3://${NPA_S3_BUCKET}/${NPA_S3_PREFIX}"
export HF_MODEL_REPO=cristpierce/shadow-dance-sonic
export ENTRANT_NVIDIA_EULA_ACCEPTED=YES
export ACCEPT_EULA=Y

python "$SHADOW_REPO/scripts/materialize_cloud_plan.py" \
  --workflow "$SHADOW_REPO/cloud/sky-shadow-dance.yaml" \
  --run-id "$RUN_ID" \
  --registry "$NPA_REGISTRY" \
  --image "$POLICY_IMAGE" \
  --submission-commit "$SUBMISSION_COMMIT" \
  --evidence-s3-uri "$EVIDENCE_S3_URI" \
  --s3-endpoint "$NPA_S3_ENDPOINT" \
  --region us-central1 \
  --hf-model-repo "$HF_MODEL_REPO" \
  --output "$SHADOW_REPO/.runtime/cloud/${RUN_ID}-materialized.yaml" \
  --require-launchable
```

This script calls NPA's materializer with registry authentication disabled, never calls
SkyPilot, never mints a token, and reports `submitted: false`. The plan must show one
Kubernetes RTX PRO 6000 task, the exact `docker:<POLICY_IMAGE>`, active host-mounted
variant, direct payload mode, frozen Git commit, and run-scoped S3 prefix. It contains
no credential values.
Runtime shell expressions such as `${HOME}` remain intentionally in `setup`/`run`.

Do **not** use `npa workbench workflow submit --plan-only` with this file. In the pinned
NPA version, the no-submit `--plan-only` branch is implemented for `npa.workflow` specs;
this file is native SkyPilot YAML. The dedicated materializer above is the fail-safe
read-only path.

If `HF_TOKEN` is intentionally unavailable, remove `--secret-env HF_TOKEN` and set
`--var HF_MODEL_REPO=`. Training and S3 evidence will still complete, but model
publication becomes a post-run manual step.

## 4. Launch once

Submit the original source YAML once, using the exact values verified above:

```bash
mkdir -p "$SHADOW_REPO/.runtime/cloud"
npa workbench workflow submit \
  "$SHADOW_REPO/cloud/sky-shadow-dance.yaml" \
  --tool sonic \
  --run-id "$RUN_ID" \
  --project "$NPA_PROJECT" \
  --registry "$NPA_REGISTRY" \
  --image "$POLICY_IMAGE" \
  --gpu-target gpu-rtx6000 \
  --image-variant sonic-k8s-host-mounted \
  --accelerators RTXPRO-6000-BLACKWELL-SERVER-EDITION:1 \
  --cloud kubernetes --region us-central1 \
  --controller-backend kubernetes \
  --infra "k8s/${KUBE_CONTEXT}" \
  --no-registry-auth --no-refresh-registry-secret \
  --accept-eula \
  --s3-endpoint "$NPA_S3_ENDPOINT" \
  --s3-bucket "$NPA_S3_BUCKET" --s3-prefix "$NPA_S3_PREFIX" \
  --var "POLICY_IMAGE=${POLICY_IMAGE}" \
  --var "SUBMISSION_COMMIT=${SUBMISSION_COMMIT}" \
  --var "RUN_ID=${RUN_ID}" \
  --var "EVIDENCE_S3_URI=${EVIDENCE_S3_URI}" \
  --var "HF_MODEL_REPO=${HF_MODEL_REPO}" \
  --var "S3_ENDPOINT_URL=${NPA_S3_ENDPOINT}" \
  --var ENTRANT_NVIDIA_EULA_ACCEPTED=YES \
  --var ACCEPT_EULA=Y \
  --secret-env AWS_ACCESS_KEY_ID --secret-env AWS_SECRET_ACCESS_KEY \
  --secret-env HF_TOKEN \
  --output-format json \
  | tee "$SHADOW_REPO/.runtime/cloud/${RUN_ID}-submit.json"
```

On-demand RTX PRO 6000 Kubernetes is the only active first-party NPA SONIC route and
has the RT capability needed for rendering. The frozen run uses 64 environments for
the 5-iteration smoke and 512 for the 250/500/4,000 candidates. This is calibrated
against a public challenge-targeted run that reported 2,000 iterations in 9,544.61
seconds at 512 environments, then needed further curriculum work before claiming full
completion. A longer ladder requires a separately versioned protocol decision; the
current job never enables it implicitly. A rolling `last.pt` is atomically refreshed
every five iterations, while regular numbered checkpoints are suppressed to avoid
uploading tens of gigabytes of redundant optimizer state. The Kubernetes controller
shares the provisioned cluster; the public GHCR image does not need a registry secret.

### Deadline guard (August 16)

The immutable challenge deadline is `2026-08-17T06:59:00Z` (August 16, 11:59 PM PT).
The job now freezes `ladder-plan.json` after the stock novelty gate and schedules the
five-step smoke plus the largest remaining candidates that fit these conservative
budgets. It fills spare time with the strongest smaller fallback and emits the selected
stages in increasing order:

| Candidate | Stage budget | Training timeout |
|---:|---:|---:|
| 5 | 15 min | 10 min |
| 250 | 30 min | 25 min |
| 500 | 60 min | 50 min |
| 4,000 | 6 h | 5 h 30 min |

It separately preserves two hours for repeated final-test evaluation, rendering, ONNX
export, validation, and upload, plus 45 minutes for logged-out URL checks and the portal.
The resulting quality-first routes and latest **post-baseline** decision times are:

| Latest decision (PT) | Scheduled route |
|---:|:---|
| 13:29 | 5 / 250 / 500 / 4,000 |
| 13:59 | 5 / 500 / 4,000 |
| 14:29 | 5 / 250 / 4,000 |
| 14:59 | 5 / 4,000 |
| 19:29 | 5 / 250 / 500 |
| 19:59 | 5 / 500 |
| 20:29 | 5 / 250 |
| 20:59 | 5 only |

Each row applies after the preceding route no longer fits. Launch earlier than those
times because base-model download, Isaac cold start, and the stock gate occur before
the decision.
The planner also subtracts time already spent before the stock gate from the ten-hour
worker cap, so a slow cold start can shorten the ladder even when the absolute deadline
alone would allow it. The outer wrapper refuses to run after the 45-minute portal
reserve begins.

If a scheduled later training stage hits its explicit timeout, the pipeline does not
mislabel its partial checkpoint. It records the timeout in `ladder-outcome.json`,
selects only among fully trained and evaluated earlier candidates, and publishes the
shortened inventory only if one still clears the frozen improvement and retention
gates. The model publisher recomputes the deadline decision and verifies both ladder
files and their hashes. A shortened ladder is disclosed evidence, not a claim that all
4,000 iterations ran.

### Cost guard

Recheck the live SkyPilot catalog before launch:

```bash
npa workbench workflow gpus --context "$KUBE_CONTEXT" --json
```

On August 16, Nebius's current
[component pricing](https://docs.nebius.com/compute/resources/pricing) lists the
`us-central1` RTX PRO 6000 at **$1.80 per GPU-hour on demand**. The task's ten-hour GPU
guard therefore caps that component near **$18**, before the small CPU node, disk, and
object-storage charges. Confirm the actual billing estimate and posted credit before
provisioning, and delete the cluster after all jobs are terminal. The timeout sends
`TERM`, allows 15 minutes for hash-skipping recovery sync, and exits `124` if still
running.

## 5. Monitor and interpret intentional stops

```bash
npa workbench workflow status "$RUN_ID" --project "$NPA_PROJECT" --watch
npa workbench workflow logs "$RUN_ID" --project "$NPA_PROJECT" --follow
```

The pipeline uploads incrementally, with SHA-256 object metadata. It also performs a
best-effort `failure-recovery/` upload on nonzero exit.

| Exit | Meaning | Next action |
|---:|---|---|
| `0` | Selected checkpoint, renders, ONNX, S3 evidence, and requested HF publish passed | Verify public files and prepare the portal |
| `3` | Stock SONIC cleared both preregistered novelty thresholds | Do not call it a new skill; revise/freeze a harder hero target |
| `4` | No scheduled candidate fit the deadline or improved hero while retaining fundamentals | Inspect the ladder/eval evidence; do not overrun the portal reserve |
| `78` | Entrant marker absent/not `YES`, or `ACCEPT_EULA` absent/not `Y` | Obtain named entrant acceptance; do not bypass |
| other | Platform, download, simulator, training, evaluation, export, or publication failure | Classify from the last log and persisted stage before retrying |

Each trained checkpoint is uploaded before its evaluations. Each evaluation is uploaded
before the next stage. `selection.json` is uploaded before any final-test evaluator is
started, preserving the temporal freeze as well as its hash. A render/export failure
therefore does not destroy training work.
Do not launch duplicate retries while the first managed job is still active.

If cancellation is necessary, first capture the exact job identity from the submit
receipt and live status, then use NPA's exact-run cancellation:

```bash
npa workbench workflow cancel "$RUN_ID" --project "$NPA_PROJECT" --json
```

After every managed job is terminal, remove the shared controller and the cluster so
the GPU and CPU nodes stop consuming credit. Preview live jobs and the exact cluster
first; NPA refuses unsafe controller teardown when it cannot prove jobs are drained,
and `cluster down` asks for confirmation unless `--force` is supplied:

```bash
"$(npa skypilot status --bin-path)" jobs queue --all
npa cluster list
npa skypilot cleanup-controller --project "$NPA_PROJECT" \
  --context "$KUBE_CONTEXT" --yes --json
cd ~/npa-shadow-operator
npa cluster down --terraform-dir deploy/cluster --project "$NPA_PROJECT"
```

## 6. Final artifact verification and publication

After a successful run, the S3 prefix contains:

```text
baseline/                       stock raw metrics and summaries
baseline/novelty.json           preregistered stock novelty decision
train/stage-{5,250,500,4000}/   training logs and rolling checkpoints as produced
checkpoints/stage-*/            packaged checkpoint + config + hash
eval/                           validation, retention, and final-test raw metrics
summaries/                      per-seed scorecards plus repeated-test aggregates
final/release/model/            selected PT, ONNX, configs, licences, hashes
final/media/                    target, all uncut renders, edited comparison, hash manifest
final/ladder-plan.json          deadline-budgeted candidate schedule
final/ladder-outcome.json       completed candidates and any honest timeout/truncation
final/selection.json            preregistered selection decision
final/final-comparison.json     untouched test result bound to selection hash
final/onnx-report.json          ONNX checker/Runtime I/O evidence
```

With `HF_MODEL_REPO` and `HF_TOKEN`, the job creates the public model repository and
writes `huggingface-model-publication.json`. Otherwise, sync the run locally and run:

```bash
python "$SHADOW_REPO/scripts/publish_model.py" \
  --run-root /path/to/downloaded/run \
  --repo-id cristpierce/shadow-dance-sonic \
  --dataset-repo cristpierce/shadow-dip-v1 \
  --dry-run
# Remove --dry-run only after the validation summary is correct.
```

The publisher refuses an inconsistent deadline ladder, a missing eligible selection,
a selected checkpoint whose hash
does not match the release, selection summaries not bound to raw metrics, a final
comparison not bound to that selection, divergent release copies, a broken release
checksum inventory, a failed ONNX report, or mismatched video sources. It includes raw
evaluation JSON/logs, every uncut render, the edited comparison, and the complete
GEAR-SONIC dual licence. Check the model and dataset pages logged out and use immutable
commit URLs in the evidence archive.

## 7. Portal handoff

Populate `submission/portal-copy.md` only from `final-comparison.json`, `selection.json`,
and the published model card. The video must compare **stock policy output** with
**selected policy output**; the labelled reference preview is never a substitute. Keep
all uncut attempts beside the edited comparison. The portal placeholder suggests a
YouTube URL; if it does not accept the immutable Hugging Face MP4 directly, publish the
same hash-verified file using `submission/video-publish-copy.md` and keep the immutable
HF source link in its description. Then complete every item in
`submission/final-checklist.md`, have the teammate verify names and links, and
explicitly submit before the deadline.
