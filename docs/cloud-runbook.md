# Shadow Dance cloud execution and publication runbook

**Prepared:** 2026-08-13 PT; runtime route corrected 2026-08-16 PT
**Target:** Nebius RTX PRO 6000 Managed Kubernetes, public NPA runtime-fetch SONIC
image, frozen Shadow Dance commit
**Rule:** do not start paid compute until the immutable inputs, storage, and licences
below all pass.

This is the operator handoff for the stock baseline, novelty gate, 5/250/500/2,000/4,000 checkpoint
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
   "applied" state is not proof that the $50 credit has posted. The August 16 portal
   client sends the **Claim $50 Nebius compute** button to
   <https://dev.nebius.com/builders>. Its short landing-page summary mentions a $25
   Token Factory credit and $25 Tavily credit, but the linked June 2026 Builder Program
   terms are more specific: section C.1 grants $25 of **Nebius AI Cloud** credit after
   successful registration and email verification; section C.2 schedules another $25
   of AI Cloud credit approximately 30 days later. Only the first $25 can be assumed to
   arrive inside this challenge window. Check the entrant's inbox/spam for the required
   double-opt-in and promotional-code email, redeem it, then verify the AI Cloud balance
   in the console. Nebius's current promo-code instructions also say that billing details
   must be configured first and that adding a card charges $25, which is then added to
   the account balance. This is an entrant-owned financial and legal action; broad
   project approval does not authorize the operator to enter payment details or trigger
   the charge. If the entrant does not explicitly choose that $25 activation, ask the
   organizer whether Trial 03 has a fee-free redemption path. If the initial code is
   absent after verification, send this in the challenge Discord help desk:

   > Team SELTZER's **Claim $50 Nebius compute** button currently opens
   > `dev.nebius.com/builders`. We completed registration and email verification, but
   > the initial $25 AI Cloud promotional code described in Builder Program terms C.1
   > has not arrived or appeared in our console. We need it for the supported RTX PRO
   > 6000 Managed Kubernetes SONIC workload. Could you confirm or resend the code and
   > the Trial 03 redemption path? The public promo-code instructions also require a $25
   > card activation; please confirm whether challenge credit can be redeemed without
   > that personal charge. The public Compute quota table also defaults `us-central1`
   > regular RTX PRO 6000 quota to zero; please grant or expedite quota **1** for our
   > project, or confirm that we should use the preemptible pool.

   Do not treat the outbound link or submitted form as a credit receipt. If the entrant
   chooses the standard card activation, the paid $25 balance plus the first $25 promo
   provides margin above the approximately $18 ten-hour GPU component; CPU, storage,
   and networking still require monitoring and the existing ten-hour auto-stop. Once AI
   Cloud access is visible, in WSL run
   `cd /home/crist/npa-shadow-operator && .venv/bin/npa configure`, select a
   `us-central1` project, and open **Administration -> Limits -> Quotas -> Compute**.
   Nebius's current
   [Compute quota table](https://docs.nebius.com/compute/resources/quotas-limits)
   gives new `us-central1` projects a default quota of **zero** RTX PRO 6000 GPUs for
   regular VMs without reservations. Its
   [Managed Kubernetes quota page](https://docs.nebius.com/kubernetes/resources/quotas-limits)
   confirms that Kubernetes nodes consume those same Compute quotas. Verify the actual
   project has at least one regular RTX PRO 6000 GPU, one GPU VM, one CPU VM, and 1,151
   GiB of Network SSD capacity. If RTX quota is zero, an admin must immediately request
   **1** through the row's **Change quota** action and copy the request into the challenge
   support escalation. Credit does not bypass quota. The supported cluster provisioning
   command is in section 1; dry-run it before creating the GPU node.

   If the organizer cannot grant regular quota in time, the same NPA command supports
   `--preemptible` and Nebius currently publishes a default preemptible-VM quota of eight.
   That count does not guarantee RTX capacity. Treat it as an availability fallback
   only: the platform may reclaim the GPU at any time, so keep every completed checkpoint
   in S3 and never describe an interrupted candidate as complete. Prefer the documented
   on-demand route whenever quota exists.

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
   Bots entry from `DRAFT` to submitted. The portal client counts exactly seven required
   values: track, project name, writeup, GitHub URL, Hugging Face policy URL, Hugging Face
   dataset URL, and simulation-video URL. It permits an incomplete **Save draft**, but
   disables **Submit entry** until all seven are non-empty. After submitting, verify the
   status indicator and the **Resubmit entry** action; a saved 7/7 draft is still not a
   submission. The kinematic reference video is not a substitute.

Everything else in this runbook is automated or already prepared.

### Local GPU contingency

This workstation exposes an RTX 5070 Ti Laptop GPU with 12,227 MiB VRAM to WSL2, but
the WSL VM has 15 GiB RAM. Its Windows NVIDIA driver is 577.13. NVIDIA's current
[Isaac Lab requirements](https://isaac-sim.github.io/IsaacLab/develop/source/setup/installation/index.html#system-requirements)
recommend at least 32 GB RAM, 16 GB GPU VRAM, and driver 580.88 on Windows for full
Isaac Sim workflows, with more for training. The laptop is therefore below all three
supported floors. Docker Engine 29.1.3, Git LFS 3.4.1, NVIDIA Container Toolkit 1.19.1,
and a public CUDA 12.8 GPU-container smoke are installed and working in WSL. The exact
SONIC image carries CUDA 13/PyTorch 2.9, however, and its open-only GPU preflight is
currently blocked by the container runtime with `unsatisfied condition: cuda>=13.0`.
No image process or Isaac download begins. The workstation route therefore remains
blocked until the entrant updates Windows to NVIDIA driver 580.88 or newer and reboots.
Even then it is only a best-effort 4/8-environment headless fallback; do not plan the
500/2,000/4,000-iteration evidence run around it.

The guarded wrapper uses the same digest-pinned image and evidence pipeline as cloud,
keeps results under `outputs/cloud/<run-id>`, and makes S3 a no-op only when
`LOCAL_ONLY=1`. The managed YAML pins `LOCAL_ONLY=0` and checks it twice, so this
contingency cannot silently weaken cloud durability. The wrapper also requires a clean
checkout and never supplies either licence marker itself. Once the entrant has sent the
exact acceptance statement above, run from WSL:

```bash
cd /mnt/c/Users/crist/dev/projects/shadow-dance
export ACCEPT_EULA=Y
export ENTRANT_NVIDIA_EULA_ACCEPTED=YES
bash scripts/run_local_fallback.sh
```

The default local ladder is 5/250 iterations with 4 smoke environments and 8 main
environments. The immutable Isaac 5.1 cache is held in Docker volume
`shadow-dance-isaac-5-1-cache`; it contains entrant-fetched proprietary NVIDIA bytes
after first use and must not be published or copied into the repository. If the exact
image reports a CUDA-driver or Isaac startup incompatibility, stop rather than changing
the digest or disabling a check: the RTX PRO 6000 managed route remains primary.

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

Free operator prerequisites were completed on August 16 without touching an account:
`~/.local/bin/nebius` resolves the existing CLI, Terraform 1.13.3 and kubectl 1.34.10
were installed from checksum-verified upstream binaries, and user-local Ubuntu 24.04
`socat` 1.8.0.0/`libwrap0` now satisfies SkyPilot's port-forward dependency. A fresh
`npa skypilot verify` no longer reports a missing binary; Kubernetes is disabled only
because no kubeconfig/context exists, and Nebius remains disabled for missing entrant
authentication. Do not reinstall these tools or mistake their readiness for cloud
readiness.

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

An independent OCI-history audit found an additional preflight requirement in this
exact digest: its upstream checkout exports `GIT_LFS_SKIP_SMUDGE=1` and then removes
`.git`. That correctly keeps model weights out of the image, but it also leaves the G1
URDF's visual meshes as pointer stubs. `cloud_pipeline.sh` therefore runs
`hydrate_sonic_assets.py` before base-model download and Isaac startup. It performs an
anonymous sparse checkout at SONIC commit `0a87181...`, copies only the G1 URDF/mesh
subtree, and fails closed unless all 69 files total 68,376,574 bytes, contain no LFS
pointers, satisfy every URDF mesh reference, and match manifest SHA-256
`4c7faab77116580265453eb4d15559e8e7e2ae43dfac3150a94150c6562399e3`. The checkout
forces `core.autocrlf=false` and `core.eol=lf`; this is the Linux runtime identity, not
a Windows worktree's CRLF-expanded URDF. Do not bypass this gate. Its
`sonic-assets.json` report is uploaded under the run's `evidence/` prefix;
the fetch includes no checkpoint/model-weight path and requires no Hugging Face token.
The exact pulled digest declares `Config.User=root`, so its root-owned nested asset
directory is writable during the current run. The reviewed Dockerfile can also be built
with a non-root runtime user; the pipeline handles that variant by using its configured
non-interactive `sudo` only for the pinned hydration command. It does not elevate
training, evaluation, downloads of model weights, or publication.
The active image's ordinary interpreter is `/opt/npa/venv/bin/python` (exported as
`NPA_IMAGE_PYTHON`), while `/isaac-sim/python.sh` is the Isaac bootstrap shim. The task
asserts both identities; `/opt/npa/sim/venv/bin/python` belongs to the retired baked
variant and must not be reintroduced.

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
the 5-iteration smoke and 512 for the 250/500/2,000/4,000 candidates. This is calibrated
against a public challenge-targeted run that reported 2,000 iterations in 9,544.61
seconds at 512 environments, then needed further curriculum work before claiming full
completion. Any further ladder change requires a separately versioned protocol
decision; the current job never enables one implicitly. A rolling `last.pt` is
atomically refreshed
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
| 2,000 | 3 h 30 min | 3 h |
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
| 15:59 | 5 / 250 / 500 / 2,000 |
| 16:29 | 5 / 500 / 2,000 |
| 16:59 | 5 / 250 / 2,000 |
| 17:29 | 5 / 2,000 |
| 19:29 | 5 / 250 / 500 |
| 19:59 | 5 / 500 |
| 20:29 | 5 / 250 |
| 20:59 | 5 only |

The 2,000 and 4,000 stages are alternative quality tiers, not cumulative requirements.
The ten-hour cap cannot fit both with the evidence reserve, so the scheduler always
prefers 4,000 when available and records 2,000 as omitted; it selects 2,000 only after
4,000 no longer fits. This closes the previous 500-to-4,000 deadline gap without making
the primary route longer or changing the quality gates.

Each row applies after the preceding route no longer fits. Launch earlier than those
times because G1 asset hydration, base-model download, Isaac cold start, and the stock
gate occur before the decision.
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
`us-central1` RTX PRO 6000 at **$1.80 per GPU-hour on demand**, CPU-d3 at $0.012 per
vCPU-hour plus $0.0032 per GiB-hour, and Network SSD at $0.071 per GiB per 730 hours.
For the NPA default one-GPU/one-CPU cluster and its 1,151 GiB of boot disks, ten hours of
the published components are approximately **$21.10** ($18 GPU + $1.98 CPU node + $1.12
disks), excluding object storage, egress, taxes, and setup time outside the workload
guard. This leaves little margin inside the first $25 promotional grant. Confirm the
console estimate and posted balance before provisioning, and delete the cluster after
all jobs are terminal. The timeout sends
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
train/stage-{5,250,500,2000,4000}/ training logs and rolling checkpoints as produced
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
