# Dataset card — Shadow Dip v1

## Summary

`shadow-dip-v1` is a small synthetic Unitree G1 reference-motion dataset authored for
Ultimate Bots Ghost Trial 03. It targets one five-second skill and deliberately favors
controlled variation and provenance over volume.

| Property | Value |
|---|---|
| Robot | Unitree G1, 29 DOF |
| Reference rate | 50 Hz |
| Train | 12 Shadow Partner Dip variants + 10 conservative rehearsal motions |
| Selection-validation (`heldout`) | 4 Shadow Partner Dip variants |
| Untouched final test | 4 independently parameterized Shadow Partner Dip variants |
| Human footage | None |
| BONES-SEED | Not used |
| SMPL | `dummy` in SONIC; no invented human skeleton |
| License | Apache-2.0 for team-authored generator and generated trajectories |

## Creation

Team-authored keyframes specify the arm-frame narrative and root path. For every frame,
bounded nonlinear least squares solves the two six-DOF legs against foot position and
orientation targets in NVIDIA's pinned G1 MJCF. A moving foot follows a smooth lift arc
during the step and is fixed through the deepest hold. The rehearsal suite includes
two-foot forward translations and sequential-foot heading turns with non-identity root
quaternions; these are actual locomotion references rather than in-place gestures. All
interpolation uses a C2-continuous smootherstep curve.

At the frozen parameters, the walk roots advance 16.4 cm and 17.2 cm, while the turn
roots finish at 20.64° and 22.56° absolute heading change. These kinematic measurements
describe the reference data only; policy tracking remains a separate evaluation.

The final manifest records the specification, source type, upstream commit, phase
windows, IK residual, file paths, and SHA-256 for every sequence. CSV uses the public
Bones-style column convention only as an interoperable schema; it contains no Bones
data.

Both an identity-heading hero and a non-identity-heading turn are round-tripped through
NVIDIA's pinned CSV converter in the test suite. The validator also hard-fails any PKL
whose root axis-angle in `pose_aa` disagrees with `root_rot`, preventing a visually
plausible CSV from hiding an internally inconsistent SONIC motion library.

## Splits and leakage

Validation and final-test sequences use amplitude, duration, hold time, and step geometry
not present as an identical training specification. They are generated as separate
sequences and are never copied into the training directory. The four `heldout` motions
are validation data: they may be used for novelty gating and checkpoint selection. The
four `test` motions are evaluated exactly once after the winning checkpoint label and
hash are frozen. Their summaries are cryptographically bound to `selection.json` in
`final-comparison.json`.

The hero-family parameter coverage is explicit rather than hidden in an augmentation
pipeline:

| Parameter | Train range | Selection-validation range | Final-test range |
|---|---:|---:|---:|
| Amplitude scale | 0.62–0.94 | 0.82–0.95 | 0.78–0.98 |
| Duration (s) | 4.50–5.70 | 4.65–5.35 | 4.85–5.45 |
| Back step (m) | 0.120–0.160 | 0.135–0.155 | 0.142–0.158 |
| Step width (m) | 0.050 | 0.050 | 0.045–0.062 |
| Held dip (s) | 0.38–0.62 | 0.47–0.60 | 0.51–0.65 |

The final test deliberately introduces unseen step widths and extends the amplitude and
hold envelopes. It remains an interpolation/extrapolation test within the declared
Shadow Partner Dip family, not a claim of broad dance generalization.

Because every sequence shares one parametric generator, the untouched result measures
interpolation within a declared motion family—not generalization to unrelated
choreography. The final report must say so.

## Quality gates

The validator hard-fails malformed shapes, non-finite data, wrong FPS, invalid
quaternions, joint-limit violations, excessive joint speed, floor penetration, a hero
without sufficient pelvis drop/waist roll/step excursion, or a sequence that does not
settle. It reports (without disguising dynamics as statics) quasi-static COM support
margin, planted-foot speed, acceleration, and MuJoCo self-contact count.

Passing reference QA means the desired trajectory is coherent enough to attempt in
simulation. It does not prove a SONIC policy can track it. That requires the separate
stock and fine-tuned evaluations.

At the frozen revision, all 30 sequences pass with zero warnings. Worst cases across
the complete set are 6.66 mm / 3.57° foot-IK residual, 4.24 mm floor penetration,
15.9% of the Isaac joint-speed limit, 54.71 rad/s² joint acceleration, +5.32 cm
two-foot support margin, +7.24 cm deep-hold support margin, and zero self contacts.
The complete per-sequence values—not only these extrema—are in
`results/reference-validation.json`.

## Intended and out-of-scope uses

Intended: focused SONIC checkpoint adaptation, validation-based selection, and
equal-condition final testing in Isaac Lab. Out of scope: safety certification, direct
motor command, clinical or biomechanical inference, or proof of real-robot feasibility
without further testing.

## Reproduction

Use the commands in the root README. The authoritative machine-readable record is
`data/manifests/shadow-dip-v1.json`; it is regenerated rather than manually edited. A
clean isolated generation reproduced all 60 CSV/PKL payloads byte-for-byte and the
manifest SHA-256 is
`1b2045380e09e6276c5ac4ff4c2bb1c7bd5903a974940f9928d7351b5f90a5d1`.
