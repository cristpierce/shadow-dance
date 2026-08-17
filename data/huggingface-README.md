---
license: apache-2.0
pretty_name: Shadow Dance v2
task_categories:
  - reinforcement-learning
tags:
  - robotics
  - unitree-g1
  - humanoid
  - motion-control
  - gear-sonic
---

# Shadow Dance v2

Fifty-four team-authored synthetic Unitree G1 motion references for the Ultimate Bots
SuperSONIC challenge: 12 parameterized partnerless dip training variants, 12 Shadow
Gancho training variants, 10 conservative rehearsal motions (including forward walk
and true heading turn in both directions), eight selection-validation motions, four
disclosed preflight-only legacy v1 tests, and eight fresh untouched final-test motions.

The archive includes SONIC motion-lib PKLs, transparent source CSVs, fixed split lists,
the full provenance/hash manifest, and the frozen MuJoCo validation report. No
BONES-SEED motion, third-party video, or human biometric data is included.

Reference QA at the published revision: 54/54 pass, zero warnings, no joint-limit
violation or MuJoCo self-contact, worst support/foot IK residual 6.96 mm / 3.74 degrees,
and a positive 1.73 cm minimum hero support margin during the deepest hold. Gancho feet
rise 29.4–31.4 cm. See the validation JSON for every metric and the GitHub repository
for generation code and limitations.

Repository: https://github.com/Durp06/shadow-dance

The 30 v1 sequences and all 60 CSV/PKL payloads remain byte-identical to the immutable
source release:
https://github.com/cristpierce/shadow-dance/releases/tag/shadow-dip-v1.0.0
(archive SHA-256
`94099f031b8a0b5ea36c809e705f77088342a6b54d73f9735508b146841c1370`).

These are desired kinematic trajectories, not policy rollouts and not proof of physical
robot execution.

Challenge acknowledgement requested by the Ultimate Bots portal: **Motion Data by
Bones Studio.** No BONES-SEED motion or derived data is included in this archive.
