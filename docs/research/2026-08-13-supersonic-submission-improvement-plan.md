# Shadow Dance: SuperSONIC submission improvement plan

- **Research snapshot:** 2026-08-13, 3:00 PM Pacific
- **Hard deadline:** 2026-08-16, 11:59 PM Pacific
- **Time remaining at snapshot:** about 81 hours
- **Repository audited:** `Durp06/shadow-dance` at `923096b914dca80eabef22734eadfcf8a1b36fd8`
- **Recommended track:** Performance Arts

This is a rescue plan for the current deadline, not a continuation of the original
two-week schedule. It separates verified facts from recommendations and calls out the
questions that can only be answered in the authenticated challenge portal.

## Executive recommendation

Keep the partnerless-dance idea, but narrow the submitted skill to a single, testable
3–6 second move:

> **Shadow Partner Dip:** establish an unmistakable partner-dance frame, pivot into a
> split stance, execute a deep off-axis back-and-side dip, hold it for one beat, and
> recover to a stable dance frame without hand support, floor contact, or partner
> counterweight.

The entry should claim the **entire sequence**, not merely “a deep lean.” A lateral lean
already appears in the organizer's own [challenge promo](https://www.youtube.com/shorts/XxDfrKiPRjE),
so a pose-only dip risks looking easy or familiar. The pivot, asymmetric lower-body
loading, sustained hold, absent-partner arm frame, and controlled recovery are what make
the skill both readable and difficult.

Use one canonical five-second timing contract for the hero, then time-scale it for the
slow/fast variants:

| Phase | Canonical window | Visible requirement |
|---|---:|---|
| Establish frame | 0.0–0.6 s | Stable two-foot stance and unmistakable absent-partner arm frame. |
| Step and pivot | 0.6–1.4 s | Split stance plus a clear heading change, without foot skating. |
| Descend off axis | 1.4–2.4 s | Pelvis drops and translates laterally/back while the feet remain planted. |
| Hold | 2.4–2.9 s | Maintain the deepest feasible shape for a readable beat. |
| Recover | 2.9–4.3 s | Reverse the load transfer without hand/floor support. |
| Settle | 4.3–5.0 s | Finish upright and stable in the dance frame. |

This timing is a project recommendation, not a contest constraint. Keep phase order and
the hold in every variant; vary depth, direction, and overall tempo rather than creating
unrelated choreography.

The submission should be organized around one evidence chain:

```text
owned reference motion
  -> physically feasible G1 reference replay
  -> stock SONIC fails or materially under-tracks it
  -> fine-tuned SONIC tracks it reliably on held-out takes
  -> walking and turning remain intact
  -> the same checkpoint exports and validates as ONNX
```

Do not spend the remaining window on a 30–45 second routine, multi-camera capture,
Quest teleoperation, a new HMR stack, or the full BONES-SEED download. Those are useful
only after the evidence chain above is complete.

## What Ultimate Bots is actually judging

The current [official challenge page](https://www.ultimatebots.com/hackathon) is the
authoritative source. It says:

- Performance Arts covers dance, gymnastics, expressive, and character motion.
- The target must be physically possible for a Unitree G1 but not performable by the
  stock model. Harder and more original moves score higher.
- The required loadout is a fine-tuned ONNX policy, the dataset and its provenance, a
  reproducible training config, a short simulation demo, and a stock before/after.
- WBT-Bench is the objective backbone: tracking reward plus penalties for flailing,
  self-collision, and jitter, with walking and turning fundamentals.
- Judges also evaluate difficulty/originality, clean and reliable execution, and
  pipeline cleanliness. Judges make the final decision; no numeric category weights
  are published.
- The deadline is August 16 at 11:59 PM PT and the portal entry can be updated until
  close.

The practical interpretation is below. The “proof to ship” column should become the
submission's table of contents.

| Criterion | What the judges need to believe | Proof to ship |
|---|---|---|
| WBT-Bench | The policy tracks without gaming the pose or sacrificing fundamentals. | Raw WBT report, stock/fine-tuned comparison, walking and turning deltas. |
| Difficulty | This is dynamic whole-body balance, not an arm animation or static bow. | Joint/root trajectory, support geometry, split stance, dip depth, hold, recovery. |
| Originality | The stock model did not already know this exact skill. | Stock failure on the exact reference; nearest-neighbor review; precise novelty claim. |
| Execution | It works cleanly and repeatedly rather than once in a favorable render. | Held-out takes, multiple rollouts, success rate, uncut repeated attempts. |
| Pipeline cleanliness | A judge can understand and rerun the path. | Pinned code, manifest, config, commands, checksums, environment, license notes. |

One useful organizer signal comes from a recent UC Berkeley event. The organizer's
[recap](https://www.linkedin.com/posts/vitl2907_we-came-to-the-uc-berkeley-ai-hackathon-to-activity-7474913971892867072-vw-Z)
highlighted a phone-video-to-mocap-to-G1 trained policy that reached a real robot in
under a day, and described the overall winner as the most complete project on the
floor. That is not the Trial 03 rubric, but it reinforces the value of a complete,
visible train-to-deploy loop over an ambitious design document.

## Current submission readiness

As of the audited commit, the repository contains seven tracked files and about 32 KB
of content. It has three Markdown documents and no Python, YAML, dataset, checkpoint,
ONNX model, metrics, demo, README, release, tag, issue, pull request, or CI workflow.
The spec itself says “design approved, not started.”

The portal notes in `HANDOFF.md` are dated August 2 and cannot be treated as current.
At that time the entry was a draft with only one of seven fields complete, the wrong
track selected, no solo team created, compute unclaimed, and GitHub/Discord not
connected. The current public page instead lists five deliverables and says they map
one-to-one to current loadout slots. Treat that mismatch as evidence that the portal
schema changed, not as permission to omit anything; inspect every authenticated field
as the first action on return.

| Required outcome | Current evidence | Assessment |
|---|---|---|
| Eligible portal entry | Stale handoff note only | **Unknown / immediate blocker** |
| New and difficult move | Written concept only | Promising, not demonstrated |
| Dataset | Capture protocol only | Missing |
| Reproducible config | No YAML or lockfile | Missing |
| Stock baseline | No metrics or render | Missing |
| Fine-tuned checkpoint | None | Missing |
| ONNX | None | Missing |
| Short simulation demo | None | Missing |
| Public explanation | No root README | Missing |

The highest-leverage improvement is therefore **completion**, followed by strength of
evidence. Expanding the choreography before the first baseline would move in the wrong
direction.

## Concept verdict

### What to keep

- Performance Arts is the right track.
- “Dancing with an absent partner” is a memorable stage concept.
- A split-stance off-axis dip stresses balance, whole-body coordination, and controlled
  recovery while avoiding object or partner contact.
- Surrounding the dip with one pivot and one recovery makes it legible as choreography
  and naturally exercises turning.

### What to change

- Name and define the **skill sequence**, not only the pose.
- Make the hero clip 3–6 seconds. A longer routine may be a closing beauty shot, but it
  should not be the training or judging unit.
- Replace the categorical claim “BONES-SEED has no dip” with an empirical claim:
  “The released stock checkpoint fails this measured off-axis partner-frame sequence,
  while our fine-tuned policy succeeds.”
- Demonstrate novelty in geometry and policy behavior, not dataset keywords.
- Use medium amplitude if it is the deepest version that lands reliably. Clean,
  physically plausible execution is an explicit judging criterion.

### Go/no-go baseline gate

Before scaling data collection or training, run the stock checkpoint on one clean
reference clip.

| Result | Decision |
|---|---|
| Stock succeeds reliably and looks close to reference | The move does not satisfy the challenge premise. Add the pivot/hold/recovery, increase off-axis loading within limits, or switch hero skill. |
| Stock fails, falls, jitters, or materially truncates the dip | Proceed and save this exact run as the before evidence. |
| Kinematic G1 reference itself clips, slides, penetrates, or violates limits | Fix the retarget or reduce amplitude before training. A policy cannot rescue a bad target cleanly. |
| Stock and reference both look acceptable but metrics disagree | Inspect termination, root drift, feet, self-collision, and playback alignment before claiming failure. |

This gate is essential because SONIC is a broad generalist. Absence of the words
“partner dip” in training metadata does not prove the stock policy cannot generalize to
the motion.

### Physical-feasibility argument

Unitree publishes a roughly 35 kg G1 with optional waist roll and pitch. The
[official G1 model](https://github.com/unitreerobotics/unitree_ros/blob/master/robots/g1_description/g1_29dof_rev_1_0.xml)
limits waist roll and pitch to about ±0.52 rad (±30°), while the hips and knees have
substantially larger ranges. Therefore a visually deep dip cannot come from bending the
waist alone. It must distribute the shape through:

- a wide or split stance;
- asymmetric hip and knee flexion;
- controlled ankle contribution;
- pelvis/root translation over the support region; and
- torso articulation that stays inside the approximately ±30° waist envelope.

For every candidate reference, record:

- maximum root and torso roll/pitch;
- minimum pelvis height;
- maximum joint-limit utilization;
- center-of-mass or root projection relative to the support polygon;
- foot slip and non-foot contacts;
- self-collision count;
- peak joint speed/acceleration; and
- whether the robot returns to a stable standing/dance frame.

These values turn “the robot should be able to do it” into an auditable feasibility
case. They are project evidence, not official judging thresholds.

## Corrections to the original technical strategy

The existing spec contains several decisions that were reasonable hypotheses on August
2 but should not remain hard constraints.

| Existing decision | Updated finding | Recommendation |
|---|---|---|
| Every custom clip must have paired SMPL. | Current NVIDIA documentation says custom motion can set `smpl_motion_file: dummy`; placeholder SMPL is weaker but supported. | Use G1 motion plus `dummy` first. Add real SMPL only if already exported and working. |
| “The road is SMPL.” | The G1 encoder can train from robot trajectories. SMPL is optional for this deadline. | Prefer the shortest clean Studio/Kimodo-to-G1 path. |
| 20–40 clips and a 30–45 s phrase. | A public [video-to-SONIC reproduction](https://github.com/IIIIQIIII/sonic-g1-video-eval) found short segmented clips much healthier than a long motion; smoothing and slowdown helped but did not fix global failure. | Use short skill clips and held-out takes. Treat the long phrase as optional presentation. |
| Start at 25% custom / 75% BONES-SEED. | The ratio has no demonstrated basis, raw BONES use is license-gated, and equal-per-motion/adaptive sampling means clip counts affect exposure. | Use owned hero plus owned walk/turn/stand retention clips. Add BONES only after eligibility and redistribution handling are confirmed. |
| Local machine is a 3060 Ti. | The machine inspected on Aug 13 reports an RTX 5070 Ti Laptop GPU with 12 GB, WSL2 Ubuntu 24.04, Python 3.12, no Docker command, and no ready SONIC environment. | Update the handoff. Local smoke may be possible, but environment setup remains unproven; cloud is the primary path. |
| One long fine-tune. | The official recipe exposes frequent checkpoints and eval. | Use a wall-clock-bounded checkpoint ladder and stop at the best validation/fundamentals tradeoff. |

NVIDIA's current [training guide](https://nvlabs.github.io/GR00T-WholeBodyControl/user_guide/training.html)
still recommends `sonic_release` for fine-tuning the released checkpoint. Keep that
choice. SONIC v1.1 is aimed at heading-stable teleoperation/VLA and requires its matching
checkpoint and observation config; changing architectures now adds risk without a clear
benefit for an offline G1 reference skill.

## Dataset plan

### Preferred source order

1. **Ultimate Bots Studio, using owned phone footage.** The official
   [Studio](https://studio.ultimatebots.com/) supports video or motion upload,
   timeline editing, and physics-simulated humanoid preview. The authenticated portal
   must confirm which raw training export is available.
2. **Kimodo G1 output.** NVIDIA's
   [Kimodo project](https://research.nvidia.com/labs/sil/projects/kimodo/) can generate
   kinematic G1 motion, and the challenge explicitly offers Kimodo through Studio.
3. **Procedural editing of an owned/generated G1 trajectory.** Use this to control the
   hold duration, amplitude, and transition while staying inside joint limits.
4. **GEM-X + SOMA Retargeter only if already operational.** It is a valid open pipeline,
   but installing and debugging it now is riskier than the hosted Studio path.

Do a 60–90 minute bake-off on one clip and commit to the first path that produces a
replayable G1 motion. Do not run parallel motion-estimation projects after the deadline
window starts.

### Minimal owned dataset

Aim for 16–20 short clips, all created by the team:

| Group | Suggested count | Purpose |
|---|---:|---|
| Shallow/medium/full dip, slow and performance tempo | 6 | Amplitude and speed curriculum |
| Mirrored or opposite-direction variants | 3 | Symmetry and directional robustness |
| Entry/pivot/hold/recovery transition variants | 3 | Prevent overfitting to one timing pattern |
| Neutral stand, forward walk, turn left, turn right | 4 | Owned fundamentals retention buffer |
| Held-out complete dip takes | 3–4 | Validation/test only; never included in training |

Use separate performances or generated seeds for held-out clips. Splitting adjacent
frames from the same take leaks nearly identical motion into train and test and does not
demonstrate generalization.

Capture only what the retargeter needs:

- one fixed camera, full body and feet visible;
- bright light, contrasting fitted clothes, little motion blur;
- a brief neutral pose before and after;
- no occluding props or partner;
- three amplitudes and two speeds; and
- no copyrighted music in the distributable clip unless it is licensed.

Multi-camera capture is optional. A clean single-camera take through the organizer's
own workflow is more valuable now than a sophisticated capture rig whose calibration is
not ready.

### Data contract and provenance

Every exported motion should have a sidecar manifest entry:

```yaml
id: shadow_dip_medium_fast_take03
source: original_video
performer_consent: true
source_file_sha256: ...
retargeter: ultimate-bots-studio
retargeter_version: ...
robot: unitree_g1_29dof
source_fps: ...
training_fps: 30
duration_s: ...
split: train
direction: left
amplitude: medium
tempo: performance
smpl: dummy
qa:
  joint_limits: pass
  feet: pass
  forbidden_contacts: pass
notes: ...
```

Publish the owned dataset, its manifest, conversion command, and license. If large
binary artifacts live on Hugging Face or an object store, keep immutable hashes and a
download script in GitHub.

### BONES-SEED license decision

The current [BONES-SEED license](https://huggingface.co/datasets/bones-studio/seed/blob/main/LICENSE.md)
is not a generic open-data license. It limits access to qualifying academic users and
qualifying startups with less than $1 million in annual gross revenue, prohibits raw
dataset redistribution, and requires specified credit for public models/software.
Ultimate Bots likewise says entrants are responsible for licenses.

For this deadline, the cleanest plan is:

- do not use raw BONES-SEED in the fine-tune unless the entrant's eligibility is
  affirmatively known;
- do not upload BONES motions as the challenge's dataset deliverable;
- use owned walking/turning clips as the retention buffer; and
- if BONES is used, publish only the owned custom dataset plus a reproducible manifest
  of restricted inputs, include the required “Motion Data by Bones Studio” credit, and
  obtain license clarification if any derived trajectory would be distributed.

The released SONIC model is separately covered by the
[NVIDIA Open Model License](https://github.com/NVlabs/GR00T-WholeBodyControl/blob/main/LICENSE),
which permits derivative models and redistribution with its license and attribution.
Starting from that checkpoint does not require republishing its original raw training
dataset.

## Reference-motion QA before training

No candidate enters the training set until it passes all four gates:

1. **Schema:** loads as a SONIC motion-lib PKL with expected G1 DOF/body order, finite
   values, correct quaternion convention, and an explicit FPS.
2. **Kinematics:** replays smoothly in the G1 model with no teleport, foot penetration,
   impossible root drift, or joint-limit violation.
3. **Physical plausibility:** no non-foot ground contact, visible foot skating during
   the hold, self-intersection, or violent acceleration spike.
4. **Narrative:** the arm frame and weight transfer clearly read as a partnerless dip
   from at least one fixed camera angle.

Trim bad leading/trailing frames, split long sequences, smooth only documented spikes,
and slow only when the slowed timing remains part of the claimed skill. Keep raw and
processed hashes so the cleanup is reproducible.

## Evaluation design

### Required comparison matrix

Run identical reference clips, seeds, terminations, and camera settings for both
policies.

| Suite | Stock SONIC | Fine-tuned SONIC | Decision use |
|---|---:|---:|---|
| Train hero variants | Record | Record | Diagnose fit, not headline result |
| Held-out hero variants | Record | Record | Main evidence |
| Shallow/medium/full amplitude | Record | Record | Select deepest reliable submission amplitude |
| Left/right direction | Record | Record | Robustness |
| Stand/walk/turn left/turn right | Record | Record | Catastrophic-forgetting guard |
| Portal WBT-Bench | Record | Record | Official objective backbone |

Preserve raw per-episode JSON, the exact command, config, seed list, checkpoint hash,
and rendered video. Generate summary tables from raw results rather than hand-copying
numbers.

The released checkpoint embeds NVIDIA-internal motion paths, and a fine-tuned
checkpoint embeds its training-data path. Override both when evaluating the frozen
held-out set so stock and fine-tuned policies see the exact same references:

```bash
python gear_sonic/eval_agent_trl.py \
  +checkpoint=<stock_or_finetuned_checkpoint.pt> \
  +headless=True \
  ++eval_callbacks=im_eval \
  ++run_eval_loop=False \
  ++num_envs=<fit-to-GPU> \
  "+manager_env/terminations=tracking/eval" \
  "++manager_env.commands.motion.motion_lib_cfg.motion_file=<frozen_eval_robot_pkl_dir>" \
  "++manager_env.commands.motion.motion_lib_cfg.smpl_motion_file=dummy"
```

### Project success gates

These are proposed internal gates, not published contest thresholds:

Freeze a deterministic hero-success detector before comparing checkpoints. Count an
episode successful only when it (a) avoids early termination, self-collision, and
non-foot ground contact; (b) reaches a predeclared fraction of the reference dip depth
and lateral/root excursion; (c) stays inside the chosen tracking-error band throughout a
minimum hold window; and (d) finishes inside declared terminal pose/root tolerances for
a settle window. Calibrate the numeric tolerances on the kinematic reference and stock
baseline, write them into the evaluation config, and do not relax them after seeing a
fine-tuned result.

- **Challenge premise:** stock hero success is clearly poor or the visual/metric error
  is materially worse than the fine-tuned policy. If stock already succeeds, change the
  skill before spending compute.
- **Hero reliability:** aim for at least 95% successful completion across 20 or more
  held-out rollouts. If the full-amplitude version misses, submit the deepest amplitude
  that meets the reliability gate.
- **Tracking:** prefer NVIDIA's converged guidance of `mpjpe_l < 30 mm`,
  `mpjpe_g < 200 mm`, and success above 0.97, while emphasizing the stock-to-fine-tuned
  delta if a focused run does not reach full-convergence values.
- **Fundamentals:** no more than a five-percentage-point success drop on owned
  walking/turning tests, and no conspicuous new jitter or falls.
- **Physical cleanliness:** zero self-collisions, zero forbidden ground contacts, no
  obvious foot skating in the held dip, and a stable recovered pose.
- **ONNX:** structural checker passes, ONNX Runtime loads every submitted model, outputs
  are finite, and a fixed observation produces a documented output shape and checksum.

Do not select the “last” checkpoint automatically. Select the checkpoint on a frozen
scorecard: held-out hero tracking first, then fundamentals, then physical penalties.

### Demo storyboard

Keep the main video approximately 20–30 seconds unless the portal specifies otherwise:

1. **0–2 s:** title and one-sentence claim.
2. **2–6 s:** human or kinematic reference with the skill phases labeled.
3. **6–13 s:** synchronized stock and fine-tuned split screen, same reference and
   camera, with no cut through the failure/recovery.
4. **13–20 s:** a simultaneous three-up grid of uncut fine-tuned attempts or held-out
   variations.
5. **20–25 s:** compact metric card: hero success, MPJPE, WBT/fundamentals delta.
6. **Optional close:** one brief full-phrase beauty shot, clearly labeled optional.

Include links to raw longer runs. Do not use camera cuts, speed changes, or music to
hide a fall, reset, or jitter. Prefer one locked three-quarter view that keeps both feet
visible and makes the lateral/back root excursion readable; use it for reference, stock,
and fine-tuned footage.

## Fine-tuning strategy

### Reproducible upstream path

Pin a tested `NVlabs/GR00T-WholeBodyControl` commit rather than tracking `main`. The
research snapshot used `c374bae5b9039cd0ee71377e654d11ce1bc69e1d`; the challenge's
provided starter commit takes precedence if the portal specifies one.

The first real fine-tune should use the official `sonic_release` checkpoint, the G1
motion library, and dummy SMPL:

```bash
python gear_sonic/train_agent_trl.py \
  +exp=manager/universal_token/all_modes/sonic_release \
  +checkpoint=sonic_release/last.pt \
  num_envs=<fit-to-GPU> headless=True use_wandb=false \
  ++manager_env.commands.motion.motion_lib_cfg.motion_file=<train_robot_pkl_dir> \
  ++manager_env.commands.motion.motion_lib_cfg.smpl_motion_file=dummy \
  ++algo.config.num_learning_iterations=<stage_iterations> \
  ++callbacks.model_save.save_frequency=25 \
  ++callbacks.model_save.save_last_frequency=5
```

In the current trainer, `+checkpoint` loads model weights for fine-tuning. Full
optimizer/environment/trainer state is restored only when resume behavior is enabled;
do not use resume for the initial adaptation unless the provided recipe explicitly
requires it.

Use the official default actor learning rate (`2e-5`) for the first measured run. The
remaining budget is too small for an unstructured hyperparameter sweep. Escalate only
when evidence points to a specific failure:

- hero does not improve: improve/oversample clean hero data or extend iterations;
- hero improves but fundamentals regress: choose an earlier checkpoint, add owned
  locomotion clips, or try `1e-5`;
- motion falls at one phase: inspect that segment and retarget/slow it rather than
  globally adding compute;
- validation plateaus while train improves: stop; the dataset is overfit.

The motion library begins with roughly equal sequence exposure and uses adaptive
sampling to emphasize failing segments. Therefore file composition matters. Avoid
creating many near-duplicate files merely to manufacture a ratio; document every
augmentation and inspect actual per-motion sampling metrics.

### Checkpoint ladder

Use wall-clock and metrics, not a promise to reach 100,000 iterations:

The current model-save callback writes numbered checkpoints every 2,000 steps and
`last.pt` every 50 by default. The command above deliberately overrides the callback,
not the legacy `algo.config.save_interval` value, so a five-iteration smoke produces a
recoverable `last.pt` and the 25-step gate produces a numbered checkpoint. Verify both
files before starting the longer run.

1. 1–5 iteration environment/data smoke; no credit-heavy run until it writes a
   checkpoint.
2. 25-iteration functional run; export/evaluate once.
3. 100-iteration first decision checkpoint.
4. Continue to 250/500 only while held-out hero metrics improve and fundamentals stay
   acceptable.
5. Reserve enough credits for one data-correction rerun and final render/export.

The official docs' 100,000-iteration convergence figure describes large-scale general
training, not a requirement for this focused challenge. The challenge itself says the
$50 credit is sized for checkpoint adaptation.

### Compute route

Use this order:

1. Claim and test the challenge-provided Nebius recipe/instance immediately.
2. Run a one-iteration proof with sample or custom data and verify the checkpoint lands
   in durable storage.
3. Use an RT-capable GPU for final Isaac rendering; headless state-based training can
   use H100.
4. Keep local WSL as a smoke/export fallback only after its exact Isaac Lab/Python
   compatibility is proven.

Nebius publishes an open
[SONIC workbench workflow](https://github.com/nebius/nebius-physical-ai/blob/main/docs/workbench/guides/g1-humanoid-walk-sonic.md),
but it should not silently replace the contest starter. Its current setup requires
SkyPilot, registry, S3, image routing, and EULA configuration; its own repository also
documents unresolved platform/runtime paths. Use it if the portal has already
provisioned that workflow, not as a last-minute infrastructure project.

At current public [Nebius pricing](https://docs.nebius.com/compute/resources/pricing),
the GPU-only on-demand ceiling is about 13 H100 hours (`$3.85/GPU-hour`) or 37 L40S
hours (`$1.35/GPU-hour`); the usable total is lower after CPU, RAM, and storage. The
contest allocation may expose a different recipe or SKU, so verify its meter before the
first long run. Set budget alerts, use run-scoped output paths, prefer a tested
spot/preemptible route only after checkpoint recovery works, and shut down idle
resources.

## Upstream export and deployment risks

ONNX export is part of the official upstream path and produces:

- `*_g1.onnx` — combined G1 reference encoder and dynamics decoder;
- `*_smpl.onnx` and `*_teleop.onnx` — other reference modalities;
- `*_encoder.onnx` — encoders; and
- `*_decoder.onnx` — decoder.

For this entry, nominate the combined `*_g1.onnx` as the direct motion-reference policy
and also include the encoder/decoder pair, `model_config.yaml`, training config, input
layout notes, hashes, and NVIDIA model license attribution. Verify which exact files the
portal slot expects before upload.

Two current upstream issues matter for “we can run what you shipped”:

- [Issue 233](https://github.com/NVlabs/GR00T-WholeBodyControl/issues/233) reports
  missing C++ observation aliases for `sonic_release` sim-to-sim deployment; the
  proposed [PR 232](https://github.com/NVlabs/GR00T-WholeBodyControl/pull/232) is open.
- [Issue 241](https://github.com/NVlabs/GR00T-WholeBodyControl/issues/241) reports no
  documented conversion from training motion-lib PKL to deploy reference format; the
  proposed [PR 240](https://github.com/NVlabs/GR00T-WholeBodyControl/pull/240) is open.

Do not silently build the entry on unmerged code. The required contest demo can use the
official Isaac evaluation/render path. If the judges require C++ sim-to-sim, vendor the
minimal reviewed patches at pinned commits, document them, and run an explicit smoke.
Ask the challenge Discord which branch/patch the judges use.

Export command from the official path:

```bash
python gear_sonic/eval_agent_trl.py \
  +checkpoint=<best_checkpoint.pt> \
  +headless=True ++num_envs=1 \
  +export_onnx_only=true
```

After export:

1. run `onnx.checker.check_model`;
2. open each required graph in ONNX Runtime;
3. record names, dtypes, and shapes of every input/output;
4. run a fixed finite test vector and save output statistics;
5. calculate SHA-256 checksums; and
6. test the archive from a clean download path, not the training directory.

## Repository and submission package

Treat the model artifacts as large binaries from the start. NVIDIA's published
[`sonic_release/last.pt`](https://huggingface.co/nvidia/GEAR-SONIC/tree/main/sonic_release)
is about 469 MB, and a published
[`sonic_v1_1` decoder ONNX](https://huggingface.co/nvidia/GEAR-SONIC/tree/main/sonic_v1_1)
is about 150 MB. GitHub
[blocks ordinary repository blobs above 100 MiB](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github).
Do an early test upload to the portal, and place the final model in the portal directly,
a GitHub Release, Git LFS, or a versioned Hugging Face model repository rather than
discovering the size constraint during the final submission hour.

The challenge encourages open source but does not require it. Prefer public,
immutable artifacts for reproducibility, but keep any license-restricted input private
and supply the portal with the permitted manifest/instructions instead of breaching a
data license for appearances.

The root README should make the submission judgeable in under two minutes. Proposed
layout:

```text
README.md
LICENSE
NOTICE
MODEL_CARD.md
configs/
  shadow_dip_finetune.yaml
  environment.lock-or-container.txt
data/
  README.md
  manifest.yaml
  splits/
scripts/
  convert_data.py-or-wrapper
  validate_motion.py
  run_baseline.ps1-or-sh
  train.sh
  evaluate.sh
  export_onnx.sh
results/
  baseline_hero.json
  finetuned_hero.json
  fundamentals.json
  wbt_bench.json
  summary.csv
artifacts/
  MANIFEST.md
  SHA256SUMS
docs/
  dataset-card.md
  experiment-report.md
  research/
media/
  hero-before-after.mp4-or-linked-external
```

Large dataset/model/video artifacts may live in a versioned Hugging Face repository or
GitHub Release. The GitHub repository should still contain their immutable URLs,
checksums, licenses, and a download command.

### Root README order

1. One sentence: what was taught and why stock SONIC cannot do it.
2. Embedded or linked 20–30 second before/after.
3. Three-result table: repeated final-test hero, fundamentals retention, ONNX validation.
4. Exact reproduction quickstart.
5. Dataset composition and license/provenance.
6. Training config and compute used.
7. Limitations and safety note.
8. Artifact links and checksums.

Use a result-backed claim template and fill the brackets only from frozen evaluation
outputs:

> We taught SONIC a five-second **Shadow Partner Dip**—dance frame, split-stance pivot,
> unsupported off-axis dip, held beat, and controlled recovery. Across the same 12
> untouched final-test trials, stock SONIC completed `[x/12]` and our fine-tuned policy
> completed `[y/12]`, while the 10-motion fundamentals-retention result changed by
> `[z]` percentage points.

Avoid claiming real-robot validation unless Ultimate Bots actually runs it. Say
“designed for G1 and validated in simulation.”

## Deadline schedule

### August 13 — establish the floor

**First 60 minutes after return**

- Open the portal: create/confirm the solo team, set Performance Arts, claim compute,
  connect GitHub/Discord, fill country, and save every current loadout slot.
- Download the exact starter recipe and WBT-Bench from the portal.
- Verify upload/link limits and whether a draft with external links counts as submitted.
- Submit a complete placeholder entry as soon as the portal permits, then update it.

**Next 2 hours**

- Pin the contest/upstream commit and prove sample data: replay, one-iteration train,
  checkpoint, eval, render, ONNX export.
- If this is not green in two hours, move to the challenge-provided Nebius environment
  and stop local setup work.

**Next 2–4 hours**

- Produce one Studio/Kimodo medium dip.
- Convert and kinematically replay it.
- Run the stock baseline. Make the move go/no-go decision.

### August 14 — data and first real model

- Capture/generate the small amplitude/tempo/direction set and owned fundamentals.
- Validate every motion and freeze train/validation/test manifests.
- Save stock baseline metrics and renders before training.
- Run the 5/250/500/4,000 checkpoint ladder.
- Evaluate held-out hero plus stand/walk/turn; choose whether to continue or fix data.

### August 15 — complete and submit early

- Run only the justified continuation/recovery fine-tune.
- Select the best checkpoint by the frozen scorecard.
- Run WBT-Bench, final held-out repeats, final render, ONNX export, and clean-download
  validation.
- Publish dataset/model artifacts, README, model card, metrics, demo, and checksums.
- Fill every portal slot and submit the complete entry by the end of August 15.

### August 16 — buffer, not core work

- Reproduce from the public links on a clean path.
- Repair broken links, upload limits, missing attributions, or portal fields.
- If reliability is below threshold, fall back to the shallower proven amplitude rather
  than starting a new pipeline.
- Freeze the entry several hours before 11:59 PM PT.

## Stop rules and fallback ladder

| Trigger | Required response |
|---|---|
| Portal/team/compute not active in first hour | Escalate in Discord/help desk immediately; continue owned-data prep in parallel. |
| Local SONIC smoke not green in two hours | Use challenge Nebius environment; stop local dependency work. |
| Studio cannot export a usable training trajectory in 90 minutes | Try Kimodo G1 output or procedural G1 edit; do not install multiple HMR systems. |
| Stock already lands the move | Increase specific difficulty or switch skill; do not market ordinary generalization as learning. |
| Full dip reference is infeasible | Use medium amplitude and quantify the physical envelope. |
| Fine-tune shows no held-out gain by the first meaningful checkpoint | Fix/split/clean data before adding iterations. |
| Hero improves but walking/turning regress | Select an earlier checkpoint or add owned retention clips; do not hide regression. |
| Deployment patch path consumes more than two hours | Complete official Isaac demo and ONNX validation; document the upstream issue and ask organizers for their branch. |
| Full package is not complete by midday Aug 15 | Drop full routine, extra camera work, and secondary experiments; ship the hero evidence chain. |

Fallback order for the hero itself:

1. Full-amplitude pivot + dip + hold + recovery.
2. Medium-amplitude version with the same complete sequence.
3. Shallow version plus a more distinctive pivot/arm-frame timing.
4. If stock handles all three, select a different short generated move for which
   feasibility and stock failure are already demonstrated. Do not force the original
   story after it fails the premise gate.

Predefine three backup hypotheses so that a failed stock gate does not trigger an open-
ended ideation session. None is presumed novel until its stock baseline is measured:

| Backup | Why it may separate from stock | Main feasibility risk |
|---|---|---|
| **Shadow gancho** | Dance frame, planted pivot, brief one-leg balance, and a hooked free-leg sweep create a distinctive whole-body sequence. | Free-leg/self-collision clearance and stance-ankle load. |
| **Spiral lunge and unwind** | Cross-back step, deep asymmetric lunge, torso/arm counter-rotation, held shape, then direction reversal. | May be too close to motions the generalist already tracks. |
| **Hovering knee drop** | Descend until one knee stops just above the floor, hold without contact, and recover without hands. | Very small ground-clearance margin and high knee/hip demand. |

Give each backup only one clean reference replay and one stock evaluation. Choose the
first physically clean candidate with an obvious stock failure; do not run three new
training campaigns.

## Prioritized backlog

### P0 — submission blockers

- [ ] Verify portal/team/track/compute/Discord/GitHub and all current loadout fields.
- [ ] Download and run the portal's exact starter and WBT-Bench.
- [ ] Produce one valid G1 reference and stock baseline.
- [ ] Confirm the move actually meets the “stock cannot” premise.
- [ ] Complete one fine-tune that writes a checkpoint.
- [ ] Export and validate the required ONNX artifact(s).
- [ ] Publish a short stock/fine-tuned simulation comparison.
- [ ] Fill every portal slot before August 15 ends.

### P1 — score multipliers

- [ ] Held-out amplitude/tempo/direction tests and 20+ repeated hero rollouts.
- [ ] Walking/turning retention comparison and WBT raw report.
- [ ] Physical-feasibility metrics and clean reference visualization.
- [ ] Reproducible commands, pinned versions, artifact hashes, dataset/model cards.
- [ ] Concise originality analysis based on nearest motions plus stock behavior.

### P2 — only after complete submission

- [ ] Full dance phrase beauty shot.
- [ ] Real SMPL pairing.
- [ ] C++ sim-to-sim deployment with reviewed upstream patches.
- [ ] More cameras, Quest teleoperation, broad hyperparameter sweeps.

## Manual questions that remain

These cannot be answered from the public site or repository and should be resolved in
the portal/Discord immediately:

1. Is the solo team active, is the entry set to Performance Arts, and is the compute
   credit claimed?
2. What exact file(s), size limits, and observation config does the ONNX loadout slot
   expect?
3. Which SONIC commit/container and which open deployment patches will judges use?
4. Where is the current WBT-Bench package and what command creates the accepted report?
5. What raw motion format can Studio export for the challenge starter scripts?
6. Does the entrant qualify under the current BONES-SEED license? If not, confirm the
   all-owned dataset plan.
7. Are there already captures, motion files, checkpoints, or portal links that have not
   been committed to this repository?
8. Are Studio-generated trajectories licensed for public dataset redistribution, or
   should only the source footage/manifest be public?

## Research boundaries

- Public search did not reveal a reliable gallery of current Trial 03 entries. That is
  not evidence of low competition; entries may be private, portal-only, or unindexed.
- A refreshed GitHub search on August 14 found
  [`danniely/ultimate-bots-G1`](https://github.com/danniely/ultimate-bots-G1), created
  August 9 and explicitly described as a SuperSONIC fine-tune. Its public evidence
  describes an airborne `s_batido` martial-arts motion plus landing recovery, a selected
  step-600 checkpoint, and a claimed 100% full-motion physics evaluation. This is a
  serious challenge-targeted comparator, although its authenticated portal status is
  not public.
- At public commit `467865beead8253dd68ca65204e818e02f2f2a57`, that comparator's
  [`final_metrics.json`](https://github.com/danniely/ultimate-bots-G1/blob/467865beead8253dd68ca65204e818e02f2f2a57/exports/metrics/final_metrics.json)
  records its initial run as 2,000 iterations, 512 environments, 24,576,000 timesteps,
  and 9,544.61 training seconds. Its checked-in config uses a `2e-5` actor learning
  rate. Later public stages add 1,000 + 1,000 iterations and a 750-iteration recovery
  run whose step-600 checkpoint was selected. These are self-reported artifacts, not
  independently rerun benchmarks, but they make a 100-iteration competition ladder
  plainly underpowered.
- In that repository's indexed tree at the August 14 snapshot, the reported result is
  centered on one reference motion. A stock before/after, independent multi-motion
  final-test split, repeated seed aggregate, ONNX export, and repository license were
  not visible. Those observations are a dated public-artifact comparison, not a claim
  that the team lacks private evidence or will not add it before the deadline.
- Its v2 result is also a useful warning against headline progress alone: the selected
  stage reached 69/81 frames (85.2%) but recorded 0% success. The v3 result became a
  claimed 100% completion only after appending a 100-frame landing-recovery segment and
  selecting among recovery checkpoints. Shadow Dance therefore treats full recovery
  and success as hard gates, while progress and MPJPE remain diagnostics.
- A second public challenge repository appeared on August 14:
  [`qjwdlwjdl/G1-Taiji-Form-final`](https://github.com/qjwdlwjdl/G1-Taiji-Form-final)
  at commit `8f93718f3572c2a657ac1b21b4f45c7837a77016`. It enters Martial Arts rather
  than Shadow Dance's Performance Arts track, so it is a quality comparator rather
  than a direct track rival. Its public writeup claims a 25.1-second Kimodo Tai Chi
  sequence, a 4,000-iteration 2,048-environment first stage, and another 3,500
  iterations of two-GPU root-focused refinement, reaching full completion and
  34.3 mm local MPJPE. At the inspected commit, the public tree contained documentation
  and before/after MP4s but no policy, raw motion, metric JSON, or repository license;
  those absences do not rule out private portal artifacts. The useful planning signal is
  that another serious entrant also spent materially more than 2,000 iterations on a
  clean whole-body result.
- The strategic response is not a late switch to an acrobatic skill. Shadow Dance must
  make the unsupported off-axis hold and recovery visually unmistakable, then win the
  evidence categories with an exact stock baseline, frozen validation/test separation,
  12 final trials per policy, retention checks, all-owned data provenance, and an exact
  validated five-graph export. If the selected policy does not execute cleanly, this
  evidence design cannot substitute for the missing result.
- The public `sonic-g1-video-eval` and
  [`motionmatching-g1-door`](https://github.com/whitealex95/motionmatching-g1-door)
  repositories are engineering comparables, not confirmed Trial 03 competitors.
- No model training, WBT run, Studio-authenticated export, portal inspection, or browser
  simulation was performed during this research pass because the required credentials,
  artifacts, and ready Isaac environment were not present.
- No public result located in this pass establishes that a 16–20-clip custom dataset
  will converge within this exact `$50` allocation. The small dataset, checkpoint
  ladder, and stop rules are deadline-risk controls, not a promised learning curve.
- All proposed success thresholds beyond the cited NVIDIA guidance are internal project
  gates, not official challenge rules.

## August 14 execution decisions and evidence hardening

The following updates supersede earlier references to a single “held-out” headline set.

### Facts verified locally

- The [official challenge page](https://www.ultimatebots.com/hackathon), rechecked
  August 14, says “one move, one task, or one idea—depth beats breadth,” requires a
  short simulation demo and stock before/after, and judges Ambition, Execution, Data
  craft, and Reproducibility. Execution explicitly includes reliability across runs;
  finalists are also evaluated by the organizers in simulation and on league robots.
- The frozen owned dataset now contains **30** motions: 22 training/rehearsal,
  4 selection-validation (`heldout`), and 4 final-test (`test`). All 30 pass the
  committed MuJoCo reference validator with zero warnings.
- Across the full frozen set, worst measured reference values are 6.66 mm foot-IK
  position residual, 3.57° orientation residual, 15.9% of the Isaac joint-speed limit,
  54.71 rad/s² peak joint acceleration, 4.24 mm floor penetration, +5.32 cm minimum
  two-foot support margin, +7.24 cm deep-hold support margin, and zero self contacts.
  The deepest family member drops the pelvis 14.7 cm and reaches 0.49 rad (28.1°) of
  waist roll while remaining inside the pinned G1 joint envelope.
- A clean isolated regeneration produced the same 60 CSV/PKL payloads and the same
  manifest bytes (SHA-256 `1b2045380e09e6276c5ac4ff4c2bb1c7bd5903a974940f9928d7351b5f90a5d1`),
  then independently passed all 30 validator cases. This is the local reproducibility
  proof for the strengthened reference geometry.
- The final four motions use independent amplitude, duration, hold, back-step, width,
  direction, and seed specifications. They are not copied into the training or
  selection-validation directories.
- The official WBT-Bench description explicitly checks walking and turning fundamentals,
  not only hero tracking penalties. Four owned rehearsal motions therefore add a
  two-foot forward walk and a sequential-foot heading turn in both lead directions.
  Their root translation/heading and foot placements are solved through the same pinned
  G1 model. The frozen walk roots advance 16.4–17.2 cm and the turns finish with
  20.64–22.56° absolute heading change. No BONES-SEED motion or derivative enters the
  dataset, and these local references are not presented as an official WBT-Bench score.
- A non-identity-heading converter test exposed and fixed a dual-representation issue:
  SONIC requires root rotation in both `root_rot` quaternion form and the root slot of
  `pose_aa`. The generator now emits both consistently, NVIDIA's pinned converter
  round-trips the turn within 2e-6, and the reference validator hard-fails future drift.
- The final August 14 public Ubuntu/Python 3.11 regeneration passed all 13 tests and all
  30 validator cases
  with zero warnings in
  [run 31851632473](https://github.com/cristpierce/shadow-dance/actions/runs/31851632473).
  Against the frozen Windows/Python 3.13 bundle, maximum drift was `1e-5` in the
  inspectable degree/centimetre CSV representation, `1.20e-7` in the SONIC PKLs,
  `3.72e-9` in manifest IK values, and `2.11e-8` in validation metrics. The public gate
  enforces exact paths, schemas, dtypes, and splits; a `2e-5` CSV-schema tolerance; and
  a `1e-6` PKL/manifest/report tolerance. Published files remain bound to exact SHA-256.
- The workstation's RTX 5070 Ti Laptop GPU is visible inside WSL2 (12,227 MiB VRAM),
  with 15 GiB VM RAM and ample disk. NVIDIA's current Isaac Lab requirements call for
  at least 16 GB VRAM and 32 GB RAM for full Isaac Sim workflows. Local execution is a
  best-effort 16-environment smoke contingency after EULA acceptance, not a credible
  replacement for the supported cloud training/evidence run.
- The pinned NPA/SkyPilot operator environment passes its local status and verification
  checks. The digest-pinned public runtime-fetch SONIC image materializes into a
  no-compute RTX PRO 6000 Kubernetes task contract. No Nebius authentication or posted
  challenge credit has been observed yet, so no paid GPU was allocated and no policy
  result is claimed.
- At pinned NPA commit `43ffee689b02a117ff4eb2c32f7057b39bcef030`, the CLI's
  guaranteed no-submit `--plan-only` return path applies to `npa.workflow` specs, not
  generic SkyPilot YAML. Shadow Dance therefore uses a dedicated read-only call to the
  SONIC materializer with registry authentication disabled. This prevents a “planning”
  check from accidentally reaching SkyPilot on an authenticated operator machine.
- NVIDIA's pinned [`ImEvalCallback`](https://github.com/NVlabs/GR00T-WholeBodyControl/blob/c374bae5b9039cd0ee71377e654d11ce1bc69e1d/gear_sonic/trl/callbacks/im_eval_callback.py)
  truncates gathered results to the number of unique motions. Increasing `num_envs`
  above four therefore does not create repeated final trials for a four-motion split.
  Independent evaluator invocations with different seeds are required to substantiate
  reliability across runs.
- The upstream exporter writes graphs to `config.experiment_dir/exported`, and a copied
  checkpoint's saved config still names its original training directory. The wrapper
  must explicitly override `experiment_dir` to the selected checkpoint package;
  otherwise a successful export can be followed by a false "no graphs found" release
  failure. The exporter produces one same-prefix five-graph bundle: SMPL, G1, teleop,
  shared encoder, and G1 decoder.
- The presentation path now generates a deterministic target/before/after video only
  after `final-comparison.json` exists. A separate manifest binds the reference, every
  matched uncut stock/selected source clip, display seed, frozen metrics, and edited
  output by size and SHA-256. Model publication refuses media drift.
- The authenticated portal screenshot explicitly asks public projects to credit
  "Motion Data by Bones Studio." Public repository, dataset, model-card, and portal copy
  now include that exact acknowledgement while separately disclosing that no
  BONES-SEED motion or derivative entered `shadow-dip-v1`.
- A read-only SkyPilot catalog query on August 14 priced the exact Nebius
  `gpu-l40s-a_1gpu-16vcpu-64gb` target at $1.747/hour on demand and $0.848/hour spot,
  consistent with [Nebius component pricing](https://docs.nebius.com/compute/resources/pricing).
  At the on-demand price, $50 covers about 28.6 VM-hours before storage/controller
  costs; the configured ten-hour attempt cap is about $17.47.
- The official Nebius Linux/amd64 CLI binary was installed from the vendor object-store
  release path and verified as version `0.12.254` (83,198,114 bytes). Profile/config
  inspection then failed closed because no `~/.nebius/config.yaml` exists. This proves
  tooling readiness without implying login, posted credit, quota, or resource access.
- The immutable public
  [Shadow Dip v1.0.0 release](https://github.com/cristpierce/shadow-dance/releases/tag/shadow-dip-v1.0.0)
  was published August 14 at commit `684c6e8130505d9d85ea0a5048d8121179b6cd68`.
  GitHub reports the 2,112,908-byte archive digest as
  `94099f031b8a0b5ea36c809e705f77088342a6b54d73f9735508b146841c1370` and the explicitly
  labelled kinematic-reference MP4 digest as
  `d9f6f4284e5cecbc80349d050786b2c876a26f1a93dd4ba6e3da8f9149efe0c3`.

### Decisions

- Use `heldout` only as selection-validation: stock novelty gating, ladder stopping,
  and winner selection may inspect it.
- Freeze the winning checkpoint identity in `selection.json` before evaluating either
  stock or selected policy on `test`. Bind the final comparison to the SHA-256 of that
  selection report. Use this untouched test comparison—not validation—as the portal's
  headline result.
- Evaluate each of the four final-test motions at seeds 101, 202, and 303 for stock and
  selected policies. Report all 12 trials per policy, per-motion reliability, and the
  macro mean of per-motion local MPJPE. Bind both the motion and seed inventories into
  `final-comparison.json`.
- Keep the 22-motion training set unchanged after the test freeze. If the stock novelty
  gate fails, do not repurpose the test data; stop and preregister a separate harder
  target before generating or training anything new.
- Prefer the active public runtime-fetch image on an on-demand RTX PRO 6000 Managed
  Kubernetes node for deadline reliability and rendering support. The frozen run is
  exactly 5/250/500/4,000 iterations with 64 environments for
  the smoke and 512 for the two main candidates. This supersedes the initial
  5/25/100 debug-scale ladder: NVIDIA documents 100 iterations as a local debug run,
  while the public challenge-targeted `ultimate-bots-G1` evidence reports that its
  2,000-iteration, 512-environment first run still had a mean episode length of only
  44.17 frames and an 85.98% end-effector termination rate. The later public Tai Chi
  entry reports 7,500 total refinement iterations on two L40S GPUs. Independent
  candidates retain a clean same-base comparison, and the 10-hour worker guard gives
  the 4,000-step candidate room to finish on one GPU. Any longer ladder requires a new versioned
  protocol decision before the untouched test is opened; it is not silently enabled.
- Enforce a ten-hour worker timeout with a 15-minute recovery window and tear down
  the small jobs controller after terminal status. This bounds a stuck attempt while
  retaining enough of the $50 credit for one evidence-driven retry.
- Treat synthetic kinematic preview footage only as an explanation of the target.
  Submission “before” and “after” footage must remain real stock-policy and selected-
  policy simulator output.

## August 14 late public-source recheck

- The official challenge page still says the practice motion set and WBT-Bench “opens
  late July,” but the signed-in portal resource cards captured August 13 expose Studio,
  SONIC code, the training guide, BONES-SEED, and Nebius only. An August 14 exact-name
  GitHub code search returned zero `WBT-Bench` hits; the current NVIDIA `main` and
  `gear-sonic` trees and current Nebius `main` tree expose no matching package. This is
  evidence of public unavailability, not proof that the organizers did not post it in
  Discord. The entrant should request the organizer link; until then, the owned
  10-motion fundamentals suite remains explicitly a proxy and is never reported as an
  official WBT-Bench score.
- Nebius `main` at commit `9b3fbe506bba63c5715541258499ae2db7b0f6c5` (August 14)
  still records the L40S `npa-sonic:0.1.2` digest as
  `sha256:bdf81f5b7f1c879ac920df53588a15129b2ac71d9492e8c2fc34ce636a5373fb`,
  matching the frozen Shadow Dance contract. Its public runbook continues to prefer
  L40S for Isaac rendering-capable validation. This strengthens the image pin without
  changing the already reviewed execution path near the deadline.
  **Superseded August 16:** current NPA quarantines this exact baked digest; see the
  deadline-day correction below.
- The local read-only SkyPilot catalog lists multiple one-GPU L40S shapes in
  `eu-north1`. The 16-vCPU/64-GB fit remains `$1.747/hour`; larger compatible shapes
  range upward from that price. The task requests `L40S:1`, 16 CPUs, and 64 GB rather
  than hard-coding a provider instance type, preserving scheduler choice while the
  ten-hour wall-time remains the spend guard. Catalog presence does not prove live
  quota or capacity.
- The newly visible public Tai Chi video comparator uses separate 25.08-second,
  1920×1088, 25-fps before and after clips. Shadow Dance keeps its shorter matched
  side-by-side presentation because it makes timing differences, early terminations,
  and the stock/fine-tuned contrast easier to judge, while publishing the uncut sources
  separately.
- An August 14 anonymous-access audit used no GitHub CLI authentication. The public API,
  raw `main` README, PR #1, and both release downloads returned successfully at commit
  `f0786729907cc7cd6b18fa6b004d418ec48a40e7`. The downloaded archive and reference
  video matched their published SHA-256 values. The archive contains 70 regular files:
  30 source CSVs, 30 SONIC PKLs, the manifest and validation JSONs, three split lists,
  three Markdown documents, `LICENSE`, and `NOTICE`. The Hugging Face publisher's
  68-file inventory is deliberately two files smaller because it maps one dataset
  README and omits the archive-only `data/README.md` and `docs/dataset-card.md`; the
  motion and evidence inventories are identical. The anonymously downloaded preview
  decodes as H.264/YUV420p, 640×480, 50 fps, and 5.26 seconds. This proves public
  accessibility and packaging integrity without turning the preview into policy
  evidence.

## August 16 deadline-day runtime correction

- **Fact (current primary source):** Nebius NPA commit
  [`43ffee689b02a117ff4eb2c32f7057b39bcef030`](https://github.com/nebius/nebius-physical-ai/commit/43ffee689b02a117ff4eb2c32f7057b39bcef030)
  makes `sonic-k8s-host-mounted` the only active SONIC variant. Its
  [image manifest](https://github.com/nebius/nebius-physical-ai/blob/43ffee689b02a117ff4eb2c32f7057b39bcef030/npa/src/npa/deploy/sonic_image_manifest.json)
  marks the former L40S digest `bdf81f5...` quarantined because it inherits restricted
  NVIDIA bytes and baked driver libraries. The resolver intentionally rejects it.
- **Fact (independent locator check):** an anonymous OCI manifest request to GHCR on
  August 16 resolved the public active tag to
  `sha256:c9ba0996b28f54b013e36da689638b386a7ef9c0c8c4413fc4b3c72ff1a808bb`,
  matching the current NPA manifest. No private registry credential is required.
- **Fact (runtime contract):** the active image contains no Isaac payload and fetches
  pinned Isaac Sim/Lab wheels only at runtime. Shadow Dance still requires the entrant's
  named acceptance before setting the documented `ACCEPT_EULA=Y`; NPA's non-interactive
  default is not treated as entrant consent.
- **Fact (hardware and cost):** Nebius's current compute pricing lists RTX PRO 6000 only
  in `us-central1`, at $1.80/GPU-hour on demand. Managed Kubernetes nodes use Compute
  pricing. The existing ten-hour task guard therefore bounds the GPU component near
  $18, excluding the small CPU node, storage, and disks.
- **Decision:** migrate the launch contract, public documentation, reproducibility
  record, and model card to the active RTX PRO 6000 Kubernetes image. Do not launch or
  republish the retired L40S image. Keep 512 main environments: NVIDIA's 4,096 setting
  is its full-scale example, while the 512 setting has same-challenge public timing and
  is the defensible deadline/budget choice until a real GPU smoke says otherwise.

## August 16 deadline-day audit

### Official requirements remain unchanged

The [official challenge page](https://www.ultimatebots.com/hackathon) was rechecked on
August 16. Performance Arts remains the right track; the complete entry still requires
an ONNX policy, documented dataset and creation method, reproducible training config,
a short simulation demo, and a stock-versus-fine-tuned comparison. Judging still
combines the organizer's WBT tracking/fundamentals backbone with originality,
execution/reliability, data craft, and pipeline cleanliness. The deadline remains
August 16 at 11:59 PM PT. Exact public-source and GitHub searches still found no
organizer WBT-Bench package; the Discord request remains mandatory, and the owned
walking/turning suite must continue to be labelled a proxy.

### Visible competitive evidence

- [SONIC Capoeira V8](https://github.com/danniely/ultimate-bots-G1) published a real
  stock/fine-tuned video, Hugging Face policy and dataset links, ONNX parity evidence,
  112/112 completed Isaac screening rollouts, and a ten-run MuJoCo cross-check. Its
  strongest disclosed result is 10/10 full-motion MuJoCo rollouts, while the stricter
  final-stabilization gate passes 3/10. Its engineering journal is unusually strong:
  eight iterations diagnose launch, contact, landing, policy handoff, actuator risk,
  and cross-simulator recovery rather than presenting a single lucky render.
- [GhostTrial Scorpion](https://github.com/SpiRaiL/GhostTrial-public) published a
  polished five-minute build video, a commissioned-performer data story, a 3,750-step
  G1 ONNX policy, and source/config artifacts. Its model card openly says walking and
  turning were not separately evaluated and that the learned motion retains 97%
  double support where the reference requests 58%. This is strong storytelling and
  honest limitation disclosure, but it leaves a clear fundamentals-evidence opening.
- [G1 Taiji Form](https://github.com/qjwdlwjdl/G1-Taiji-Form-final) presents separate
  25-second before/after clips and reports large same-reference MPJPE/completion gains.
  Its public GitHub tree exposes presentation/config files but not the policy or raw
  evaluation inventory, making Shadow Dance's planned immutable evidence chain a
  potential differentiator rather than a reason to imitate its packaging.

These are public-repository observations, not claims about the private portal field or
judge ranking. The lesson is concrete: dataset quality alone cannot win this field.
Shadow Dance needs a real trained policy, a legible matched before/after, and numerical
proof. Its best distinct angle is the combination competitors do not visibly provide:
separate validation and untouched parametric test families, 12 matched final trials per
policy, explicit walking/turning retention, raw source hashes, and full regeneration.

### Deadline decision

The previous relative ten-hour timeout could expire during the 4,000-step candidate
before selection/export, stranding usable earlier checkpoints. The run now freezes a
deadline plan after the stock gate. Candidate budgets are 15 minutes for stage 5,
30 minutes for stage 250, 60 minutes for stage 500, and 6 hours for stage 4,000,
followed by a two-hour evidence reserve and 45-minute portal reserve. The 4,000-stage
training subprocess itself may run for at most 5.5 hours, matching the public 5.3-hour
linear runtime evidence while leaving evaluation/upload margin.

The initial ordered-prefix planner could leave enough time for stage 4,000 unused when
the sum of every intermediate candidate no longer fit. On August 16 it was replaced by
the auditable `smoke_then_largest_feasible_v1` policy: keep stage 5, greedily prioritize
the largest remaining candidate, fill spare time with the strongest smaller fallback,
then execute the chosen stages in increasing order. The full ladder remains available
through 13:29 PT post-baseline; quality-first 4,000-step routes remain available through
14:59 PT, followed by 5/250/500 through 19:29, 5/500 through 19:59, 5/250 through 20:29,
and stage 5 through 20:59. Cold start and baseline work occur first, so actual launch
must precede those times. The planner also enforces the remaining portion of the
ten-hour worker cap after that pre-gate work. A later timeout is recorded and only
fully completed candidates may be selected; partial weights are never renamed as a
completed stage.

This fallback changes compute breadth, not the frozen novelty/improvement/retention
thresholds or the untouched final-test rule. `ladder-plan.json` and
`ladder-outcome.json` make the reduction auditable, and the publisher recomputes their
decision before releasing weights. If no completed candidate is eligible, the correct
outcome is no policy claim—not synthetic or estimated evidence.

## Primary sources

- [Ultimate Bots Trial 03 challenge page](https://www.ultimatebots.com/hackathon)
- [Ultimate Bots Studio](https://studio.ultimatebots.com/)
- [NVIDIA GR00T Whole-Body Control repository](https://github.com/NVlabs/GR00T-WholeBodyControl)
- [NVIDIA SONIC training guide](https://nvlabs.github.io/GR00T-WholeBodyControl/user_guide/training.html)
- [NVIDIA SONIC model card](https://nvlabs.github.io/GR00T-WholeBodyControl/model_card.html)
- [NVIDIA Kimodo project](https://research.nvidia.com/labs/sil/projects/kimodo/)
- [Unitree G1 product page](https://www.unitree.com/g1/)
- [BONES-SEED dataset license](https://huggingface.co/datasets/bones-studio/seed/blob/main/LICENSE.md)
- [Nebius SONIC workflow guide](https://github.com/nebius/nebius-physical-ai/blob/main/docs/workbench/guides/g1-humanoid-walk-sonic.md)
