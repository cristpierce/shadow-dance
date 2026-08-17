# Shadow Dance — SuperSONIC Trial 03

**Team SELTZER · Performance Arts · Unitree G1**

Shadow Dance is teaching SONIC a five-second **Shadow Partner Dip + Gancho**: establish
an absent-partner dance frame, step back and pivot, transfer into an unsupported
off-axis hold, sweep a free leg into a 29–31 cm hooked pose, and recover without hand
or floor support.

The move is a testable hypothesis until the stock checkpoint comparison is complete.
This repository never substitutes the kinematic reference for policy output and never
fills result tables with estimates.

![Labelled kinematic reference at the held gancho](media/reference-hold.png)

*Kinematic target only—not stock or fine-tuned policy output.*

> Current state (2026-08-16): the combined `shadow-dance-v2` bundle passes 54/54
> manifest-bound reference checks with zero warnings, while preserving all 30 v1
> sequences and all 60 of their PKL/CSV payload hashes byte-for-byte. An account-free
> stock deployment proxy found a clear
> global-position weakness on the gancho validation family, but it is not Isaac or
> WBT-Bench evidence. The
> immutable [Shadow Dance v2.0.0 reference release](https://github.com/cristpierce/shadow-dance/releases/tag/shadow-dance-v2.0.0)
> is public, with v1 retained as its audit anchor. A separately labelled experimental
> affine deployment adapter now provides a real derivative ONNX and deterministic
> MuJoCo stock/adapted comparison, but its mixed result is **not** the required
> Isaac/PPO fine-tune or WBT-Bench evidence. Official metrics and the official policy
> before/after remain pending authorized compute access.
> See [PROGRESS.md](PROGRESS.md).
> The exact Nebius execution and publication handoff is in
> [docs/cloud-runbook.md](docs/cloud-runbook.md).

## Why this is a meaningful new skill

SONIC already has broad dance data, so the claim is not “the robot learned to dance.”
The proposed novelty is the complete partnerless sequence: a recognizable asymmetric
arm frame, a planted back-step, lateral and backward load transfer, a sustained
approximately 30-degree waist-envelope pose, an aerial hooked-leg sweep on one-foot
support, and controlled recovery. The hard novelty gate remains behavioral: the
official stock SONIC run must fail or materially under-track the frozen validation
family while the adapted policy improves it. Checkpoint selection then freezes before
either policy is measured on the independent final-test family.

## Evidence dashboard

| Gate | Artifact | State |
|---|---|---|
| Original data + provenance | `data/manifests/shadow-dance-v2.json`, PKLs, and source CSVs; immutable [v1 release](https://github.com/cristpierce/shadow-dance/releases/tag/shadow-dip-v1.0.0) retained | 54 v2 sequences committed; 60/60 v1 PKL/CSV hashes preserved |
| G1 limits / foot IK / support QA | `results/reference-validation-v2.json` | 54/54 pass; 0 warnings |
| Public stock ONNX preflight | MuJoCo port of NVIDIA's deployment observation/action contract | Gancho validation: 4/4 upright, 28.88 mm local MPJPE, 114.50 mm mean root error; not Isaac/WBT-Bench |
| Experimental affine proxy adapter | `results/proxy-adapter-final-comparison.json`, model card, checked derivative ONNX release | Fresh proxy test: 8/8 upright; joint RMSE -9.60%, global MPJPE -0.72%, local MPJPE +0.75% (worse); not Isaac/PPO/WBT-Bench |
| Stock SONIC on validation moves | raw Isaac eval log + novelty report | Pending authorized Isaac run |
| Fine-tuned SONIC | deadline-planned 5/250/500/2,000/4,000 ladder from pinned base | Pending Isaac run |
| Fundamentals retention | identical stock/fine-tuned suite | Pending Isaac run |
| Official final test | 8 motions × 3 seeds per policy, bound to frozen selection | V2 test was consumed once after proxy-adapter freeze; any later official run must disclose that reuse or reserve a new test family |
| Deployable policy | checked ONNX graphs + hashes | Pending selected checkpoint |
| Judge-facing comparison | locked-camera stock/fine-tuned video | Pending both policy renders |

## Dataset design

The dataset is team-authored and procedural. It does **not** contain BONES-SEED motion
or third-party dance video. Keyframes define the artistic pose; numerical inverse
kinematics solves each leg against the pinned NVIDIA G1 MJCF so planted feet stay
planted. The generator produces:

- 12 training dip variants across direction, depth, timing, hold, and step geometry;
- 12 training gancho variants across direction, load transfer, timing, and hook geometry;
- 10 conservative stand/squat/sway/torso-turn/forward-walk/heading-turn rehearsal motions;
- 8 separately parameterized validation motions used for checkpoint selection;
- 4 disclosed legacy v1 test motions isolated as preflight-only after local exploration;
- 8 independently parameterized final-test motions reserved for policy evaluation only
  after selection; and
- both transparent degree/centimetre CSV and SONIC motion-lib PKL forms.

The locomotion references are measurable rather than label-only: the two walks move the
root forward 16.4–17.2 cm, and the two heading turns finish 20.6–22.6° from the starting
heading. They are a transparent local retention proxy; no official WBT-Bench score is
claimed until the organizer's evaluator is actually run.

Validation, preflight, and final-test variants are never placed in the training
directory. The preflight split is excluded from training, selection, and final
reporting. Final test is excluded from every training, novelty, early-stopping, and
checkpoint-selection decision. Dataset details and limitations are in
[docs/dataset-card-v2.md](docs/dataset-card-v2.md). The original frozen v1 card remains
at [docs/dataset-card.md](docs/dataset-card.md).

## Reproduce locally

Prerequisites: Python 3.11+, Git, and a checkout of NVIDIA's upstream repository at
commit `c374bae5b9039cd0ee71377e654d11ce1bc69e1d` next to this repository.

```powershell
py -3.13 -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev,onnx,publish]"
$env:SONIC_ROOT = "C:\path\to\GR00T-WholeBodyControl"

.venv\Scripts\shadow-generate --profile dance-v2 --sonic-root $env:SONIC_ROOT
.venv\Scripts\shadow-validate --sonic-root $env:SONIC_ROOT `
  --dataset data/generated-v2 `
  --manifest data/manifests/shadow-dance-v2.json `
  --report results/reference-validation-v2.json
.venv\Scripts\python scripts/verify_dataset_bundle.py --profile dance-v2
.venv\Scripts\pytest -q
```

Render a labelled *reference-only* preview:

```powershell
.venv\Scripts\shadow-render `
  data/generated-v2/heldout/shadow_gancho_right_heldout_02.pkl `
  --sonic-root $env:SONIC_ROOT `
  --manifest data/manifests/shadow-dance-v2.json `
  --output media/reference-kinematic.mp4
```

The small frozen PKLs, source CSVs, manifest, validator report, code, hashes, and clearly
watermarked reference preview are committed so the cloud job needs no hidden local
input. Policy renders remain ignored until they are packaged with their run evidence.
The exact frozen bundle is also available in the public
[Shadow Dance v2.0.0 reference release](https://github.com/cristpierce/shadow-dance/releases/tag/shadow-dance-v2.0.0).
Its 4,179,263-byte archive SHA-256 is
`c1bde31a71e5d596f5018e01da8bcdb097ae314bd65c98c2aefa69fadb84217b`;
an anonymous redownload and full 108-file manifest verification passed. The immutable
[v1.0.0 release](https://github.com/cristpierce/shadow-dance/releases/tag/shadow-dip-v1.0.0)
remains the byte-preservation audit anchor. V2 will also be mirrored to a versioned
Hugging Face dataset after entrant authentication.

### Frozen v2 reference QA

These are measured from `results/reference-validation-v2.json`, not policy results:

| Check | Worst case across 54 sequences |
|---|---:|
| Foot IK position / orientation residual | 6.96 mm / 3.74° |
| Joint-limit violation | 0 rad |
| Peak pelvis drop / waist roll | 0.147 m / 0.495 rad (28.4°) |
| Gancho foot height | 0.314 m maximum |
| Peak joint speed vs Isaac limit | 45.4% |
| Peak joint acceleration | 226.10 rad/s² |
| Floor penetration | 7.923 mm |
| Planted-foot horizontal speed, p95 | 0.0752 m/s |
| Two-foot support margin | +0.024 m minimum |
| Hero deep-hold support margin | +0.017 m minimum |
| Dynamic single-support margin | −0.029 m minimum |
| MuJoCo self contacts | 0 |

The negative instantaneous margin occurs during a moving-foot interval and is why the
policy baseline remains a mandatory go/no-go gate. Every dip/gancho deepest hold has a
positive quasi-static support margin; the gancho's aerial leg is checked through joint
limits, velocity, clearance, self-contact, and one-foot support rather than a fictitious
six-DOF sole target.

## Experimental account-free adapter

Licensed Isaac compute was unavailable, so a deliberately small fallback experiment
calibrates the public GEAR-SONIC decoder with a per-joint affine transform. Twelve
gancho training motions provide supervised action/target statistics; gains and biases
are bounded and shrunk 90% toward identity. Four separate gancho validation motions
select the transform before the eight v2 test motions are opened. The frozen transform
is appended directly to the public decoder graph without changing its
`obs_dict [1,994] -> action [1,29]` contract.

| Deterministic MuJoCo proxy, 8 fresh motions | Stock | Adapter | Change |
|---|---:|---:|---:|
| Upright completion | 8/8 | 8/8 | unchanged |
| Local MPJPE | 29.229 mm | 29.448 mm | **+0.75% (worse)** |
| Global MPJPE | 85.427 mm | 84.810 mm | -0.72% |
| Root-position error | 77.687 mm | 76.706 mm | -1.26% |
| Joint RMSE | 9.544 deg | 8.628 deg | -9.60% |

This is a mixed result and is not promoted as the challenge fine-tune. It is useful
supplemental evidence that the complete data-to-ONNX/evaluation path works without
concealing a regression. See the [model card](docs/proxy-adapter-model-card.md),
[frozen selection](results/proxy-adapter-selection.json), and
[complete comparison](results/proxy-adapter-final-comparison.json). Because these test
motions have now been evaluated by the proxy adapter, a later official run must disclose
that prior use and avoid describing them as previously unopened; preferably it should
reserve a newly generated final-test family before any additional tuning.

## Train, compare, and export

Isaac Lab uses the official `sonic_release` architecture and checkpoint. The custom
motions exercise the G1 and derived teleoperation references; `smpl_motion_file=dummy`
is supported by upstream and prevents fake SMPL data from entering the provenance
chain.

The pinned NPA image deliberately leaves Git LFS payloads out of its upstream checkout,
which also leaves the G1 visual meshes as pointer stubs. Before downloading Isaac or
starting evaluation, the cloud pipeline sparsely fetches only the G1 URDF/mesh subtree
from the image's exact SONIC commit and verifies 69 files, 68,376,574 bytes, zero
pointers, and canonical manifest SHA-256
`4c7faab77116580265453eb4d15559e8e7e2ae43dfac3150a94150c6562399e3`. Model weights
are excluded from that fetch; `sonic-assets.json` records the result.

```bash
# 5-iteration data/environment smoke
SONIC_ROOT=/workspace/GR00T-WholeBodyControl \
NUM_ENVS=64 ITERATIONS=5 RUN_NAME=shadow_dip_smoke \
bash scripts/train.sh

# Identical frozen validation references for stock and a candidate checkpoint
MOTION_KEYS_FILE=data/splits-v2/heldout.txt NUM_ENVS=8 SEED=42 \
  bash scripts/evaluate.sh /workspace/sonic_release/last.pt stock data/generated-v2/heldout
MOTION_KEYS_FILE=data/splits-v2/heldout.txt NUM_ENVS=8 SEED=42 \
  bash scripts/evaluate.sh /workspace/outputs/.../last.pt stage-4000 data/generated-v2/heldout

# Locked-camera policy output and ONNX export
MOTION_KEYS_FILE=data/splits-v2/test.txt NUM_ENVS=8 SEED=303 \
  bash scripts/render_policy.sh /workspace/sonic_release/last.pt stock data/generated-v2/test
MOTION_KEYS_FILE=data/splits-v2/test.txt NUM_ENVS=8 SEED=303 \
  bash scripts/render_policy.sh /workspace/outputs/.../last.pt selected data/generated-v2/test
bash scripts/export_onnx.sh /workspace/outputs/.../last.pt data/generated-v2/test
python scripts/verify_artifacts.py /workspace/outputs/.../exported
```

The checkpoint ladder is bounded by the 10-hour cloud wall-time guard and the absolute
submission deadline. When any candidate fits, the scheduler keeps the five-step smoke,
then prioritizes the largest remaining candidate that fits and uses spare time for the
strongest smaller fallback. This preserves two hours for final evidence and 45 minutes
for portal submission without wasting a late 4,000-step window on only short stages.
It records every omitted/timed-out stage and stops if no completed candidate clears the
preregistered novelty, improvement, and retention gates. It is not an instruction to
burn the full credit allocation. Exact parameters and the selection rule are in
[configs/shadow_dip_finetune.yaml](configs/shadow_dip_finetune.yaml).

## Result contract

The final headline will be populated only from frozen evaluation artifacts:

> Across 24 untouched final-test trials (8 motions × 3 simulator seeds), stock SONIC completed `[x/24]`
> trials and the selected fine-tuned checkpoint completed `[y/24]`; local MPJPE changed
> from `[a]` to `[b]` mm while the 10-motion fundamentals-retention score changed by
> `[z]` points.

Reference playback proves the target is kinematically coherent. It is not evidence that
the policy can execute it. “Before” and “after” will always mean stock-policy and
fine-tuned-policy simulation output, respectively.

## Repository map

```text
src/shadow_dance/       generator, MuJoCo IK, validator, renderer
data/                   provenance manifest, splits, dataset notes
configs/                frozen experiment intent and checkpoint ladder
scripts/                train, eval, render, export, artifact checks
                        and guarded WSL/Docker fallback
results/                raw/derived evaluation contract
submission/             portal-ready copy and completion checklist
docs/research/          dated challenge and strategy research
docs/cloud-runbook.md   exact no-compute plan, launch, recovery, and publication handoff
```

## Safety, licensing, and limits

- Designed for Unitree G1 and validated in simulation; no real-robot claim is made.
- A real robot must use vendor safety limits, an operator stop, and a clear fall zone.
- Project code and generated motion are Apache-2.0. NVIDIA source/model terms remain in
  force; see [NOTICE](NOTICE).
- The final policy is a derivative of NVIDIA's SONIC checkpoint under the NVIDIA Open
  Model License and will ship with required attribution.
- No BONES-SEED raw or derived motion is used in `shadow-dip-v1` or `shadow-dance-v2`.

## Team

Team **SELTZER** (two members). Repository implementation and submission coordination:
Pierce Crist (`cristpierce`) and Myles Shetty (`Durp06`). The portal currently exposes
only the teammate initial in the supplied screenshot, so both display names must still
be checked exactly as registered before submission.

## Challenge acknowledgement

**Motion Data by Bones Studio.** This acknowledgement is included as requested by the
Ultimate Bots portal. Shadow Dance's published trajectories are independently
team-authored; no BONES-SEED motion or derived data is included.
