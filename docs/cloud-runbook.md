# Shadow Dance cloud execution and publication runbook

**Prepared:** 2026-08-13 PT
**Target:** Nebius L40S, NPA `npa-sonic:0.1.2`, frozen Shadow Dance commit
**Rule:** do not start paid compute until the immutable inputs, storage, and licences
below all pass.

This is the operator handoff for the stock baseline, novelty gate, 5/500/4,000 checkpoint
ladder, selection-validation and retention evaluation, untouched final testing, policy
renders, ONNX validation, S3 evidence, and optional Hugging Face model publication. The
final test repeats all four motions under three independent simulator seeds for each
policy. The job is intentionally one serial task so the checkpoint and evidence chain
cannot drift across machines.

## The five things only the entrant can do

1. **Accept NVIDIA's terms in your own name.** Read the
   [current Omniverse/AI product-specific terms](https://www.nvidia.com/en-us/agreements/enterprise-software/product-specific-terms-for-ai-products/),
   [Isaac Sim Additional Software and Materials Licence](https://docs.isaacsim.omniverse.nvidia.com/latest/common/license-isaac-sim-additional.html),
   and [NVIDIA Software Licence Agreement](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-software-license-agreement/).
   Then send this exact statement to the project operator:

   > I accept the NVIDIA Omniverse Licence Agreement, NVIDIA Isaac Sim Additional
   > Software and Materials Licence, and NVIDIA Software Licence Agreement for this
   > SuperSONIC project, and authorize OMNI_KIT_ACCEPT_EULA=YES and
   > ISAACSIM_ACCEPT_EULA=YES.

   General permission to work on the project is not legal acceptance of named
   third-party agreements. The pipeline exits `78` before downloading Isaac unless both
   variables are exactly `YES`.

2. **Complete interactive Nebius login and confirm usable credit/quota.** The portal's
   "applied" state is not proof that the $50 credit has posted. In WSL, run
   `cd /home/crist/npa-shadow-operator && .venv/bin/npa configure --interactive --provision`,
   select the intended project, and confirm an L40S can be scheduled in `eu-north1`.

3. **Complete Hugging Face login locally.** Never paste a token into chat, Git, YAML, or
   a shell command argument. Run `.venv\Scripts\hf.exe auth login` interactively in the
   Windows project, and let WSL `npa configure` store/resolve `HF_TOKEN` through its
   protected credential prompt for cloud publication. Use a token authorized to create
   and update the two public repositories (a download-only token is insufficient). The
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

5. **Publish the real policy comparison and submit the portal entry.** A signed-in team
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
git checkout 1e8acb921aa953c1e2ce018bcbc6417611768a16

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

Resolve the non-secret launch values from that configuration:

```bash
export NPA_PROJECT=default  # replace if npa configure used another alias
export NPA_REGISTRY="$(python -c \
  'from npa.clients.config import resolve_container_registry; print(resolve_container_registry())')"
export NPA_S3_BUCKET="$(python -c \
  'from npa.clients.config import resolve_project_storage; print(resolve_project_storage().checkpoint_bucket)')"
export POLICY_IMAGE="${NPA_REGISTRY}/npa-sonic@sha256:bdf81f5b7f1c879ac920df53588a15129b2ac71d9492e8c2fc34ce636a5373fb"

printf 'project=%s\nregistry=%s\nbucket=%s\nimage=%s\n' \
  "$NPA_PROJECT" "$NPA_REGISTRY" "$NPA_S3_BUCKET" "$POLICY_IMAGE"
test -n "$NPA_REGISTRY"
test -n "$NPA_S3_BUCKET"
case "$POLICY_IMAGE" in
  cr.*.nebius.cloud/*/npa-sonic@sha256:bdf81f5b7f1c879ac920df53588a15129b2ac71d9492e8c2fc34ce636a5373fb) ;;
  *) echo "Unexpected SONIC image: $POLICY_IMAGE" >&2; exit 2 ;;
esac
```

The official default registry currently resolves to
`cr.eu-north1.nebius.cloud/e00cm0vc6t09m0z5gw`. It is a public locator but still
requires a Nebius IAM pull token. NPA mints and injects a short-lived token because the
SONIC image is the task's direct `resources.image_id`; no registry password is committed.
The image reference is pinned to the L40S digest recorded by NPA, not only the mutable
`0.1.2` tag. There is no confirmed public GHCR copy of that image.

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
export EVIDENCE_S3_URI="s3://${NPA_S3_BUCKET}/shadow-dance/${RUN_ID}"
export HF_MODEL_REPO=cristpierce/shadow-dance-sonic
export OMNI_KIT_ACCEPT_EULA=YES
export ISAACSIM_ACCEPT_EULA=YES

python "$SHADOW_REPO/scripts/materialize_cloud_plan.py" \
  --workflow "$SHADOW_REPO/cloud/sky-shadow-dance.yaml" \
  --run-id "$RUN_ID" \
  --registry "$NPA_REGISTRY" \
  --image "$POLICY_IMAGE" \
  --submission-commit "$SUBMISSION_COMMIT" \
  --evidence-s3-uri "$EVIDENCE_S3_URI" \
  --hf-model-repo "$HF_MODEL_REPO" \
  --output "$SHADOW_REPO/.runtime/cloud/${RUN_ID}-materialized.yaml" \
  --require-launchable
```

This script calls NPA's materializer with registry authentication disabled, never calls
SkyPilot, never mints a registry token, and reports `submitted: false`. The plan must
show one Nebius L40S task, the exact `docker:<POLICY_IMAGE>`, direct payload mode, the
frozen Git commit, and the run-scoped S3 prefix. It contains no credential values.
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
  --gpu-target l40s --accelerators L40S:1 --cloud nebius --region eu-north1 \
  --controller-backend nebius \
  --no-use-spot \
  --s3-endpoint https://storage.eu-north1.nebius.cloud \
  --s3-bucket "$NPA_S3_BUCKET" --s3-prefix "shadow-dance/${RUN_ID}" \
  --var "POLICY_IMAGE=${POLICY_IMAGE}" \
  --var "SUBMISSION_COMMIT=${SUBMISSION_COMMIT}" \
  --var "RUN_ID=${RUN_ID}" \
  --var "EVIDENCE_S3_URI=${EVIDENCE_S3_URI}" \
  --var "HF_MODEL_REPO=${HF_MODEL_REPO}" \
  --var OMNI_KIT_ACCEPT_EULA=YES --var ISAACSIM_ACCEPT_EULA=YES \
  --secret-env AWS_ACCESS_KEY_ID --secret-env AWS_SECRET_ACCESS_KEY \
  --secret-env HF_TOKEN \
  --output-format json \
  | tee "$SHADOW_REPO/.runtime/cloud/${RUN_ID}-submit.json"
```

On-demand L40S is the reliability default because the deadline is close and rendering
needs RT-capable hardware. The frozen run uses 64 environments for the 5-iteration smoke
and 512 for the 500/4,000 candidates. This is calibrated against a public
challenge-targeted run that reported 2,000 iterations in 9,544.61 seconds at 512
environments, then needed further curriculum work before claiming full completion. A
longer ladder requires a separately versioned protocol decision; the current job never
enables it implicitly. A rolling `last.pt` is atomically refreshed
every five iterations, while regular numbered checkpoints are suppressed to avoid
uploading tens of gigabytes of redundant optimizer state.
`--controller-backend nebius` uses NPA's small `cpu-e2_2vcpu-8gb` fallback controller;
without this explicit selection, the CLI assumes an existing Kubernetes controller.

### Cost guard

Recheck the live SkyPilot catalog before launch:

```bash
"$(npa skypilot status --bin-path)" gpus list L40S --infra nebius/eu-north1
```

On August 14, the pinned catalog priced the requested
`gpu-l40s-a_1gpu-16vcpu-64gb` at **$1.747/hour on demand** (matching Nebius's
[component pricing](https://docs.nebius.com/compute/resources/pricing)). At that price,
$50 is about 28.6 instance-hours. The task has an immutable ten-hour wall-time guard,
so one attempt is capped near **$17.47** of VM compute before minor disk/object-storage
costs; a ten-hour 2-vCPU/8-GB controller is roughly another $0.50. This leaves room
for diagnosis and a deliberate retry. The timeout sends `TERM`, allows 15 minutes for
the pipeline's hash-skipping recovery sync, and then exits `124` if still running.

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
| `4` | No 5/500/4,000 candidate improved hero while retaining fundamentals | Inspect stage summaries; justify a longer ladder or revise data |
| `78` | EULA variables absent or not exactly `YES` | Obtain named entrant acceptance; do not bypass |
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

After every managed job is terminal, tear down the shared CPU controller so it cannot
continue consuming credit. Preview live jobs first; NPA refuses unsafe teardown when it
cannot prove they are drained:

```bash
"$(npa skypilot status --bin-path)" jobs queue --all
npa skypilot cleanup-controller --project "$NPA_PROJECT" --yes --json
```

## 6. Final artifact verification and publication

After a successful run, the S3 prefix contains:

```text
baseline/                       stock raw metrics and summaries
baseline/novelty.json           preregistered stock novelty decision
train/stage-{5,500,4000}/       training logs and rolling checkpoints as produced
checkpoints/stage-*/            packaged checkpoint + config + hash
eval/                           validation, retention, and final-test raw metrics
summaries/                      per-seed scorecards plus repeated-test aggregates
final/release/model/            selected PT, ONNX, configs, licences, hashes
final/media/                    target, all uncut renders, edited comparison, hash manifest
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

The publisher refuses a missing eligible selection, a selected checkpoint whose hash
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
