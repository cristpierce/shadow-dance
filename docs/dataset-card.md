# Dataset card — Shadow Dip v1

## Summary

`shadow-dip-v1` is a small synthetic Unitree G1 reference-motion dataset authored for
Ultimate Bots Ghost Trial 03. It targets one five-second skill and deliberately favors
controlled variation and provenance over volume.

| Property | Value |
|---|---|
| Robot | Unitree G1, 29 DOF |
| Reference rate | 50 Hz |
| Train | 12 Shadow Partner Dip variants + 6 conservative rehearsal motions |
| Held-out | 4 Shadow Partner Dip variants |
| Human footage | None |
| BONES-SEED | Not used |
| SMPL | `dummy` in SONIC; no invented human skeleton |
| License | Apache-2.0 for team-authored generator and generated trajectories |

## Creation

Team-authored keyframes specify the arm-frame narrative and root path. For every frame,
bounded nonlinear least squares solves the two six-DOF legs against foot position and
orientation targets in NVIDIA's pinned G1 MJCF. A moving foot follows a smooth lift arc
during the step and is fixed through the deepest hold. All interpolation uses a
C2-continuous smootherstep curve.

The final manifest records the specification, source type, upstream commit, phase
windows, IK residual, file paths, and SHA-256 for every sequence. CSV uses the public
Bones-style column convention only as an interoperable schema; it contains no Bones
data.

## Splits and leakage

Held-out sequences use amplitude, duration, hold time, and step geometry not present as
an identical training specification. They are generated as separate sequences and are
never copied into the training directory. Because all sequences share one parametric
generator, this measures interpolation across a motion family—not generalization to
unrelated choreography. The final report must say so.

## Quality gates

The validator hard-fails malformed shapes, non-finite data, wrong FPS, invalid
quaternions, joint-limit violations, excessive joint speed, floor penetration, a hero
without sufficient pelvis drop/waist roll/step excursion, or a sequence that does not
settle. It reports (without disguising dynamics as statics) quasi-static COM support
margin, planted-foot speed, acceleration, and MuJoCo self-contact count.

Passing reference QA means the desired trajectory is coherent enough to attempt in
simulation. It does not prove a SONIC policy can track it. That requires the separate
stock and fine-tuned evaluations.

## Intended and out-of-scope uses

Intended: focused SONIC checkpoint adaptation and equal-condition held-out evaluation
in Isaac Lab. Out of scope: safety certification, direct motor command, clinical or
biomechanical inference, or proof of real-robot feasibility without further testing.

## Reproduction

Use the commands in the root README. The authoritative machine-readable record is
`data/manifests/shadow-dip-v1.json`; it is regenerated rather than manually edited.
