# Ultimate Bots portal copy

Use this only after replacing every bracket from raw artifacts and testing every public
link in a logged-out/clean session.

## Project name

G1 Shadow Partner Dip

## Track

Performance Arts

## Writeup draft

We taught NVIDIA SONIC a five-second **Shadow Partner Dip**: the G1 establishes an
absent-partner ballroom frame, steps back and pivots, transfers its weight into a deep
off-axis dip, holds the pose for a beat, and recovers without a partner, hand support,
or floor contact. The authored target reaches a 14.7 cm pelvis drop and 28.1-degree
waist roll; all 30 generated references pass the preregistered kinematic checks with
zero self-contacts.

This is not a generic “robot dances” entry. SONIC already knows broad dance motion. Our
test is the exact unsupported sequence. After selecting the checkpoint on separate
validation motions, we opened an untouched final-test family. Across 12 matched test
trials per policy (4 motions × 3 simulator seeds), stock SONIC completed **[x/12]**
versus **[y/12]** for our selected checkpoint;
local MPJPE changed from **[a] mm** to **[b] mm**. A 10-motion fundamentals suite,
including real forward walking and heading turns in both directions, changed by
**[z] points**, so the improvement is not purchased by discarding basic control.

Our 30-sequence dataset is team-authored and reproducible: 12 training dips spanning
direction, depth, tempo, hold, and step geometry; 10 conservative rehearsal motions;
4 independently parameterized validation dips; and 4 independently parameterized
final-test dips. MuJoCo inverse kinematics pins the feet against NVIDIA's official G1
model. A public manifest records every specification, phase, upstream commit, IK
residual, and SHA-256. No BONES-SEED motion or third-party video is included.

We fine-tuned the released `sonic_release/last.pt` checkpoint using its G1 reference
encoder and upstream-supported dummy SMPL path. We evaluated stock and candidate
checkpoints against the same frozen motions, selected from the completed
**[COMPLETED_LADDER]** stages of a deadline-bounded 5/250/500/2,000/4,000 plan, exported the
selected G1 ONNX policy, and validated the graph and I/O in ONNX Runtime. The plan and
outcome files disclose every omitted stage. Full commands, raw logs, configs,
limitations, licenses, and uncut runs are in the repository.

Validated in simulation; no real-robot claim is made.

Challenge acknowledgement: **Motion Data by Bones Studio.** No BONES-SEED motion or
derived data was used in our independently authored dataset.

## Loadout links

- GitHub if upstream PR #1 is merged: `https://github.com/Durp06/shadow-dance`
- Ready public fallback if it is not merged: `https://github.com/cristpierce/shadow-dance`
- Dataset (Hugging Face): `[PUBLIC_DATASET_URL]`
- ONNX policy/model card (Hugging Face): `[PUBLIC_MODEL_URL]`
- Before/after simulation video: `[PUBLIC_VIDEO_URL]`
- Raw evaluation evidence: `[PUBLIC_RESULTS_URL]`

## Final honesty check

- [ ] Headline numbers come from all 12 untouched final-test trials bound to selection.
- [ ] “Before” is stock policy output, not reference playback.
- [ ] “After” uses the exact published checkpoint.
- [ ] ONNX SHA-256 in the portal matches the public file.
- [ ] No raw/derived BONES data entered the artifact.
- [ ] Both registered team members are named correctly.
- [ ] Entry is explicitly submitted, not left as DRAFT.
