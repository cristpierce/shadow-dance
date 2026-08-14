# Shadow Dance — SuperSONIC Trial 03

**Team SELTZER · Performance Arts · Unitree G1**

Shadow Dance is teaching SONIC a five-second **Shadow Partner Dip**: establish an
absent-partner dance frame, step back and pivot, descend into an unsupported off-axis
dip, hold for a readable beat, and recover without hand or floor support.

The move is a testable hypothesis until the stock checkpoint comparison is complete.
This repository never substitutes the kinematic reference for policy output and never
fills result tables with estimates.

![Labelled kinematic reference at the held dip](media/reference-hold.png)

*Kinematic target only—not stock or fine-tuned policy output.*

> Current state (2026-08-13): original synthetic references and the reproducible
> pipeline are being validated. Stock/fine-tuned metrics, final ONNX links, and the
> policy before/after video remain pending compute access. See [PROGRESS.md](PROGRESS.md).

## Why this is a meaningful new skill

SONIC already has broad dance data, so the claim is not “the robot learned to dance.”
The proposed novelty is the complete partnerless sequence: a recognizable asymmetric
arm frame, a planted back-step, lateral and backward load transfer, a sustained
approximately 30-degree waist-envelope pose, and controlled recovery. The hard novelty
gate is behavioral: the same frozen held-out reference must make stock SONIC fail or
materially under-track while the adapted policy succeeds.

## Evidence dashboard

| Gate | Artifact | State |
|---|---|---|
| Original data + provenance | `shadow-dip-v1` manifest and source CSVs | 22 sequences generated and hashed |
| G1 limits / foot IK / support QA | `results/reference-validation.json` | 22/22 pass; 0 warnings |
| Stock SONIC on held-out moves | raw eval log + uncut render | Pending Isaac run |
| Fine-tuned SONIC | checkpoint ladder at 5/25/100/250/500 | Pending Isaac run |
| Fundamentals retention | identical stock/fine-tuned suite | Pending Isaac run |
| Deployable policy | checked ONNX graphs + hashes | Pending selected checkpoint |
| Judge-facing comparison | locked-camera stock/fine-tuned video | Pending both policy renders |

## Dataset design

The dataset is team-authored and procedural. It does **not** contain BONES-SEED motion
or third-party dance video. Keyframes define the artistic pose; numerical inverse
kinematics solves each leg against the pinned NVIDIA G1 MJCF so planted feet stay
planted. The generator produces:

- 12 training dip variants across direction, depth, timing, hold, and step geometry;
- 6 conservative stand/squat/sway/torso-turn rehearsal motions;
- 4 separately parameterized held-out dip variants; and
- both transparent degree/centimetre CSV and SONIC motion-lib PKL forms.

Held-out variants are never placed in the training directory. Dataset details and
limitations are in [docs/dataset-card.md](docs/dataset-card.md).

## Reproduce locally

Prerequisites: Python 3.11+, Git, and a checkout of NVIDIA's upstream repository at
commit `c374bae5b9039cd0ee71377e654d11ce1bc69e1d` next to this repository.

```powershell
py -3.13 -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
$env:SONIC_ROOT = "C:\path\to\GR00T-WholeBodyControl"

.venv\Scripts\shadow-generate --sonic-root $env:SONIC_ROOT
.venv\Scripts\shadow-validate --sonic-root $env:SONIC_ROOT
.venv\Scripts\pytest -q
```

Render a labelled *reference-only* preview:

```powershell
.venv\Scripts\shadow-render `
  data/generated/heldout/shadow_dip_left_heldout_19.pkl `
  --sonic-root $env:SONIC_ROOT `
  --manifest data/manifests/shadow-dip-v1.json `
  --output media/reference-kinematic.mp4
```

The generated PKLs and videos are intentionally ignored by Git. The source CSVs,
manifest, validator report, code, and hashes make them reproducible. The submission
dataset will also be published as a versioned Hugging Face artifact.

### Frozen reference QA

These are measured from `results/reference-validation.json`, not policy results:

| Check | Worst case across 22 sequences |
|---|---:|
| Foot IK position / orientation residual | 6.00 mm / 3.21° |
| Joint-limit violation | 0 rad |
| Peak joint speed vs Isaac limit | 15.7% |
| Floor penetration | 3.58 mm |
| Planted-foot horizontal speed, p95 | 0.011 m/s |
| Two-foot support margin | +0.054 m minimum |
| Deep-hold support margin | +0.070 m minimum |
| Dynamic single-support margin | −0.028 m minimum |
| MuJoCo self contacts | 0 |

The negative instantaneous margin occurs during the moving-foot interval and is why
the policy baseline remains a mandatory go/no-go gate; the planted deepest hold has a
positive 7.0 cm quasi-static margin.

## Train, compare, and export

Isaac Lab uses the official `sonic_release` architecture and checkpoint. The custom
motions exercise the G1 and derived teleoperation references; `smpl_motion_file=dummy`
is supported by upstream and prevents fake SMPL data from entering the provenance
chain.

```bash
# 5-iteration data/environment smoke
SONIC_ROOT=/workspace/GR00T-WholeBodyControl \
NUM_ENVS=256 ITERATIONS=5 RUN_NAME=shadow_dip_smoke \
bash scripts/train.sh

# Identical frozen held-out references for stock and a candidate checkpoint
bash scripts/evaluate.sh /workspace/sonic_release/last.pt stock
bash scripts/evaluate.sh /workspace/outputs/.../model_step_000100.pt finetuned_100

# Locked-camera policy output and ONNX export
bash scripts/render_policy.sh /workspace/sonic_release/last.pt stock
bash scripts/render_policy.sh /workspace/outputs/.../best.pt finetuned
bash scripts/export_onnx.sh /workspace/outputs/.../best.pt
python scripts/verify_artifacts.py /workspace/outputs/.../exported
```

The checkpoint ladder stops when held-out improvement plateaus or fundamentals regress.
It is not an instruction to burn the full credit allocation. Exact parameters and the
selection rule are in [configs/shadow_dip_finetune.yaml](configs/shadow_dip_finetune.yaml).

## Result contract

The final headline will be populated only from frozen evaluation artifacts:

> On the same held-out Shadow Partner Dip references, stock SONIC completed `[x/n]`
> trials and the selected fine-tuned checkpoint completed `[y/n]`; local MPJPE changed
> from `[a]` to `[b]` mm while the stand/turn retention score changed by `[z]` points.

Reference playback proves the target is kinematically coherent. It is not evidence that
the policy can execute it. “Before” and “after” will always mean stock-policy and
fine-tuned-policy simulation output, respectively.

## Repository map

```text
src/shadow_dance/       generator, MuJoCo IK, validator, renderer
data/                   provenance manifest, splits, dataset notes
configs/                frozen experiment intent and checkpoint ladder
scripts/                train, eval, render, export, artifact checks
results/                raw/derived evaluation contract
submission/             portal-ready copy and completion checklist
docs/research/          dated challenge and strategy research
```

## Safety, licensing, and limits

- Designed for Unitree G1 and validated in simulation; no real-robot claim is made.
- A real robot must use vendor safety limits, an operator stop, and a clear fall zone.
- Project code and generated motion are Apache-2.0. NVIDIA source/model terms remain in
  force; see [NOTICE](NOTICE).
- The final policy is a derivative of NVIDIA's SONIC checkpoint under the NVIDIA Open
  Model License and will ship with required attribution.
- No BONES-SEED raw or derived motion is used in `shadow-dip-v1`.

## Team

Team **SELTZER** (two members). Repository implementation and submission coordination:
Pierce Crist (`cristpierce`) and teammate. The final portal copy will name both members
exactly as registered before submission.
