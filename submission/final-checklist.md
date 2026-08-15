# Final submission checklist

## Portal

- [x] Team exists: `SELTZER`, 2 members.
- [x] Track: Performance Arts.
- [x] GitHub and Discord connected; country set.
- [ ] Compute credit actually available (claim/application alone is not availability).
- [ ] Project name saved.
- [ ] Final writeup saved with no brackets.
- [ ] Canonical GitHub link points to merged current commit.
- [x] Public fork fallback points to the complete current commit on default `main`.
- [ ] Public Hugging Face ONNX/model link saved.
- [ ] Public Hugging Face dataset link saved.
- [ ] Stock/fine-tuned simulation video link saved.
- [ ] Entry status changed from DRAFT to submitted before 2026-08-16 23:59 PT.
- [x] Immutable public reference-dataset fallback release works anonymously: both
  assets return HTTP 200 with matching SHA-256, and the archive inventory was inspected.

## Evidence

- [x] Reference validator overall pass and visual inspection.
- [ ] Stock baseline establishes a real novelty gap; otherwise revise hero before train.
- [ ] Selected checkpoint wins on validation—not only train—references.
- [ ] Final headline comes from test motions first opened after the winner was frozen.
- [ ] Stock and selected policy each have all 12 final trials (4 motions × 3 seeds).
- [ ] `final-comparison.json` hash-binds test summaries to `selection.json`.
- [ ] The complete 10-motion fundamentals-retention result is disclosed, including
  forward walking and heading turns in both directions.
- [ ] Run the official WBT-Bench package if organizers provide it; otherwise disclose
  that it was unavailable and label the owned fundamentals suite as a proxy, never as
  an official WBT-Bench score.
- [ ] Uncut repeated attempts accompany the edited comparison.
- [ ] `video-manifest.json` verifies the reference, all matched stock/selected source
  clips, display seed, final metrics report, and edited video hash.
- [ ] Exact five-graph SONIC ONNX bundle passes checker/Runtime inference; `_g1.onnx`
  nominee, I/O contract, and hashes are published.
- [ ] Public URLs work when logged out and point to immutable revisions/tags.

## Licensing and safety

- [ ] Named NVIDIA/Isaac EULA acceptance recorded before Isaac provisioning.
- [ ] NVIDIA Open Model License accompanies derivative weights.
- [ ] Apache-2.0 and third-party notices included.
- [x] Dataset card says no BONES-SEED and accurately describes synthetic generation.
- [x] Public copy includes the portal-requested exact acknowledgement, "Motion Data by
  Bones Studio," without implying BONES-SEED was used.
- [x] Simulation-only and real-robot safety limitations are visible.
