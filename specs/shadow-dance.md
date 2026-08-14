# Shadow Dance experiment specification

- **Challenge:** Ultimate Bots Trial 03, SuperSONIC
- **Team:** SELTZER
- **Track:** Performance Arts
- **Robot/policy:** Unitree G1, NVIDIA GEAR-SONIC
- **Status:** reference/data pipeline complete; stock-policy baseline awaits authorized
  Isaac/Nebius access
- **Deadline:** 2026-08-16 23:59 PT

This is the current experiment contract. Historical capture, SMPL, and BONES-SEED ideas
were discarded before training and are not part of the submission dataset or claim.

## 1. Falsifiable claim

Teach stock SONIC a single readable move it has not already mastered: the **Shadow
Partner Dip**. The G1 establishes an absent-partner ballroom frame, steps back and
pivots, transfers its weight into an unsupported off-axis dip, holds the pose, then
recovers without partner counterweight, hand support, or floor contact.

The entry succeeds only if all of the following are true:

1. Stock SONIC shows a measured novelty gap on the frozen selection-validation family.
2. A fine-tuned checkpoint materially improves that family under preregistered gates.
3. The 10-motion stand/squat/sway/walk/turn fundamentals suite remains within the
   preregistered regression bounds.
4. The frozen winner improves an independently parameterized final-test family across
   three simulator seeds.
5. The exact selected checkpoint exports as a coherent five-graph SONIC ONNX bundle and
   every graph passes checker, load, and finite CPU inference probes.

If stock already masters the validation family, the current motion is not claimed as a
new skill and training stops. If no candidate clears the gates, no winner is published.

## 2. Owned data contract

`shadow-dip-v1` contains 30 team-authored procedural G1 sequences:

| Split | Count | Purpose |
|---|---:|---|
| Train hero dips | 12 | Direction, amplitude, tempo, hold, and step-geometry variation |
| Train rehearsal | 10 | Stand, squat, sway, torso turn, forward walk, and heading turn |
| Selection validation | 4 | Novelty gate and candidate selection only |
| Final test | 4 | First policy evaluation after the winner is frozen |

The keyframed artistic trajectory is solved against NVIDIA's pinned G1 MJCF with
MuJoCo leg inverse kinematics. Source CSVs, SONIC-ready PKLs, split lists, generator
parameters, validation results, upstream identity, and SHA-256 hashes are committed.

No BONES-SEED motion, human video, SMPL body data, or third-party dance asset is used.
The official `smpl_motion_file=dummy` path is deliberate: training uses the G1 motion
library without inventing paired human data.

The reference validator must pass joint limits, foot IK, velocity, acceleration, floor,
planted-foot, support-margin, and self-contact checks. Reference playback proves only
that the target is coherent; it is never presented as policy execution.

## 3. Frozen training contract

- Base model: `nvidia/GEAR-SONIC`, revision
  `9c0ff22b4ffec27c5392e8e284eb2f2df7a5b4e2`.
- Base checkpoint SHA-256:
  `e6bdab3f64a39336b3d41877d4f497d05f58af275f288ec0e6746c283ded8909`.
- Runtime: `npa-sonic:0.1.2` L40S image at digest
  `sha256:bdf81f5b7f1c879ac920df53588a15129b2ac71d9492e8c2fc34ce636a5373fb`.
- Runtime SONIC commit: `0a87181c9106d0e49293400714b157676e0ec664`.
- Candidate budgets: independent 5, 500, and 4,000 iteration fine-tunes from the same base.
- Seed for selection evaluation: 42.
- No W&B dependency, no hidden data, and no training/test overlap.
- One on-demand Nebius L40S worker with a 10-hour hard wall-time guard.

The five-iteration run is also the data/environment smoke. Each surviving candidate is
packaged with its original config and checkpoint hash before evaluation. Longer stages
may be added only by an explicit documented decision after inspecting genuine evidence;
they are not silently included in the headline comparison.

## 4. Selection and test protocol

### Novelty gate

Stock must have validation success at or below 75%, or local MPJPE at or above 50 mm.
The stock report and raw metrics are hash-bound into `novelty.json`.

### Candidate eligibility

A candidate must satisfy both:

- hero improvement: at least +25 percentage points success, or no success regression
  plus at least 10% local-MPJPE improvement; and
- retention: no more than 1/6 success loss and no more than 15% local-MPJPE increase.

Eligible checkpoints are ranked by validation success, validation MPJPE, retention
success, then retention MPJPE. `selection.json` records the frozen winner, every source
summary hash, and the winning checkpoint's byte size and SHA-256.

### Untouched final test

Only after `selection.json` exists are stock and the selected checkpoint evaluated on
the four final-test motions at seeds 101, 202, and 303. Upstream SONIC truncates one
evaluation result to its unique-motion inventory, so the pipeline runs three distinct
evaluator invocations per policy rather than pretending extra environments are repeats.

The headline therefore contains 12 trials per policy. `final-comparison.json` binds the
selection report, exact motion inventory, exact seed inventory, every per-seed summary,
and the raw metrics chain. The final test never changes the selected checkpoint.

## 5. Artifact and video contract

The selected release contains:

- the exact `last.pt` and training `config.yaml` named by `selection.json`;
- five same-prefix SONIC graphs: SMPL, G1, teleop, shared encoder, and G1 decoder;
- `model_config.yaml`, graph I/O metadata, ONNX checker/runtime results, and hashes;
- selection, final comparison, compact summaries, raw logs/metrics, and environment
  identity; and
- the NVIDIA Open Model License text and required attribution.

The `_g1.onnx` graph is the portal nominee. Publication refuses checkpoint, raw metric,
aggregate, ONNX, release-checksum, or media-manifest drift.

The judge-facing video is built only from real simulator output after final evaluation:

1. a clearly labelled team-authored kinematic target that says it is not policy output;
2. matched, fixed-camera stock and selected renders for all four test motions at display
   seed 303; and
3. frozen aggregate success/MPJPE numbers covering all 12 trials per policy.

When one run ends first, the shorter panel freezes and displays `RUN ENDED`; footage is
not cut around falls or resets. `video-manifest.json` hashes the reference, every uncut
source clip, the final comparison, and the edited output.

## 6. Compute and failure policy

The exact target currently prices at $1.747 per L40S worker-hour on demand. The 10-hour
worker ceiling is about $17.47 before the small controller cost, leaving room inside a
$50 challenge credit for one diagnosed recovery run. On-demand is preferred near the
deadline because interruption would cost more evidence time than spot savings justify.

The workflow uploads checkpoints, configs, logs, summaries, and evidence incrementally
to a run-scoped S3 prefix. On failure it uploads the recoverable state before exit. A
rerun syncs unchanged hash-matching objects rather than duplicating them.

The workflow is not launchable until the entrant explicitly accepts the applicable
NVIDIA Omniverse, Isaac Sim materials, and software licences. It never interprets a
generic project approval as licence acceptance.

## 7. Reporting and safety

- Never fill a result placeholder from an estimate, beauty render, reference playback,
  train metric, or validation metric.
- Report stock and selected failures as well as successes.
- State that results are simulation-only; do not claim real-G1 validation.
- A physical run requires vendor limits, an operator emergency stop, a clear fall zone,
  and independent safety review.
- Public dataset/model links and hashes must be tested while logged out before portal
  submission.
- The Ultimate Bots entry must be moved from DRAFT to submitted before the deadline by
  an authenticated team member.
