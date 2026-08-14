# Ultimate Bots portal copy

Use this only after replacing every bracket from raw artifacts and testing every public
link in a logged-out/clean session.

## Project name

G1 Shadow Dance: The Unsupported Partner Dip

## Track

Performance Arts

## Writeup draft

We taught NVIDIA SONIC a five-second **Shadow Partner Dip**: the G1 establishes an
absent-partner ballroom frame, steps back and pivots, transfers its weight into a deep
off-axis dip, holds the pose for a beat, and recovers without a partner, hand support,
or floor contact.

This is not a generic “robot dances” entry. SONIC already knows broad dance motion. Our
test is the exact unsupported sequence. On identical held-out references and seeds,
stock SONIC completed **[x/n]** trials versus **[y/n]** for our selected checkpoint;
local MPJPE changed from **[a] mm** to **[b] mm**. Stand/turn retention changed by
**[z] points**, so the improvement is not purchased by discarding basic control.

Our 22-sequence dataset is team-authored and reproducible: 12 training dips spanning
direction, depth, tempo, hold, and step geometry; 6 conservative rehearsal motions;
and 4 independently parameterized held-out dips. MuJoCo inverse kinematics pins the
feet against NVIDIA's official G1 model. A public manifest records every specification,
phase, upstream commit, IK residual, and SHA-256. No BONES-SEED motion or third-party
video is included.

We fine-tuned the released `sonic_release/last.pt` checkpoint using its G1 reference
encoder and upstream-supported dummy SMPL path. We evaluated stock and candidate
checkpoints against the same frozen motions, selected from a 5/25/100/[...] checkpoint
ladder, exported the selected G1 ONNX policy, and validated the graph and I/O in ONNX
Runtime. Full commands, raw logs, configs, limitations, licenses, and uncut runs are in
the repository.

Validated in simulation; no real-robot claim is made.

## Loadout links

- GitHub: `https://github.com/Durp06/shadow-dance`
- Dataset (Hugging Face): `[PUBLIC_DATASET_URL]`
- ONNX policy/model card (Hugging Face): `[PUBLIC_MODEL_URL]`
- Before/after simulation video: `[PUBLIC_VIDEO_URL]`
- Raw evaluation evidence: `[PUBLIC_RESULTS_URL]`

## Final honesty check

- [ ] Every number is generated from frozen held-out output.
- [ ] “Before” is stock policy output, not reference playback.
- [ ] “After” uses the exact published checkpoint.
- [ ] ONNX SHA-256 in the portal matches the public file.
- [ ] No raw/derived BONES data entered the artifact.
- [ ] Both registered team members are named correctly.
- [ ] Entry is explicitly submitted, not left as DRAFT.
