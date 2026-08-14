---
license: apache-2.0
pretty_name: Shadow Partner Dip v1
task_categories:
  - reinforcement-learning
tags:
  - robotics
  - unitree-g1
  - humanoid
  - motion-control
  - gear-sonic
---

# Shadow Partner Dip v1

Thirty team-authored synthetic Unitree G1 motion references for the Ultimate Bots
SuperSONIC challenge: 12 parameterized partnerless dip training variants, 10 conservative
rehearsal motions (including forward walk and true heading turn in both directions),
4 selection-validation dips, and 4 untouched final-test dips.

The archive includes SONIC motion-lib PKLs, transparent source CSVs, fixed split lists,
the full provenance/hash manifest, and the frozen MuJoCo validation report. No
BONES-SEED motion, third-party video, or human biometric data is included.

Reference QA at the published revision: 30/30 pass, zero warnings, no joint-limit
violation or MuJoCo self-contact, worst foot IK residual 6.66 mm / 3.57 degrees, and a
positive 7.24 cm minimum quasi-static support margin during the deepest hold. See the
validation JSON for every metric and the GitHub repository for generation code and
limitations.

Repository: https://github.com/Durp06/shadow-dance

These are desired kinematic trajectories, not policy rollouts and not proof of physical
robot execution.

Challenge acknowledgement requested by the Ultimate Bots portal: **Motion Data by
Bones Studio.** No BONES-SEED motion or derived data is included in this archive.
