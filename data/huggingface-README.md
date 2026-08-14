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

Twenty-two team-authored synthetic Unitree G1 motion references for the Ultimate Bots
SuperSONIC challenge: 12 parameterized partnerless dip training variants, 6 conservative
rehearsal motions, and 4 held-out dip variants.

The archive includes SONIC motion-lib PKLs, transparent source CSVs, fixed split lists,
the full provenance/hash manifest, and the frozen MuJoCo validation report. No
BONES-SEED motion, third-party video, or human biometric data is included.

Reference QA at the published revision: 22/22 pass, zero warnings, no joint-limit
violation or MuJoCo self-contact, worst foot IK residual 6.00 mm / 3.21 degrees, and a
positive 7.0 cm minimum quasi-static support margin during the deepest hold. See the
validation JSON for every metric and the GitHub repository for generation code and
limitations.

Repository: https://github.com/Durp06/shadow-dance

These are desired kinematic trajectories, not policy rollouts and not proof of physical
robot execution.
