# Final submission checklist

## Portal

- [x] Team exists: `SELTZER`, 2 members.
- [x] Track: Performance Arts.
- [x] GitHub and Discord connected; country set.
- [ ] Initial $25 **AI Cloud** promotional code is email-verified, redeemed, and visible
  in the Nebius console (claim/application alone is not availability; Builder Program
  terms schedule the second $25 about 30 days later, outside the usable deadline window).
- [ ] Entrant explicitly chooses the standard $25 card activation, or the organizer
  supplies a fee-free Trial 03 redemption. Do not infer payment authorization from
  general project approval.
- [ ] In **Administration -> Limits -> Quotas -> Compute**, actual `us-central1`
  regular RTX PRO 6000 quota is at least **1**. The public default is zero and Managed
  Kubernetes uses the same quota; request/escalate quota 1 immediately if unchanged.
- [ ] Project name saved.
- [ ] Final writeup saved with no brackets.
- [ ] Canonical GitHub link points to merged current commit.
- [x] Public fork fallback points to the complete current commit on default `main`.
- [ ] Public Hugging Face ONNX/model link saved.
- [ ] Public Hugging Face dataset link saved.
- [ ] Stock/fine-tuned simulation video link saved.
- [ ] Portal readiness meter says `7 of 7 complete`; all four URLs were opened and
  checked rather than counted merely because they contain text.
- [ ] Click **Submit entry**, confirm the status is submitted and the action changes to
  **Resubmit entry**, and capture the confirmation before 2026-08-16 23:59 PT. A saved
  7/7 draft is not submitted.
- [x] Immutable public v2 reference-dataset fallback release works anonymously: both
  assets return HTTP 200 with matching SHA-256, and the extracted 108-file bundle
  passes the manifest verifier.

## Evidence

- [x] Combined v2 reference validator passes 54/54 with zero warnings; all original v1
  payload hashes remain identical. Four previously explored v1 tests are disclosed as
  preflight-only. The eight v2 test inputs were opened only after the experimental
  affine proxy adapter was frozen; they are no longer previously unopened for a later
  official run.
- [x] Account-free public stock ONNX/MuJoCo preflight motivated the gancho revision and
  shows 114.50 mm mean root error across its four validation motions. It is labelled a
  proxy and does not satisfy the official Isaac novelty gate.
- [x] Experimental affine proxy adapter is fully disclosed: 8/8 upright, joint RMSE
  -9.60%, global MPJPE -0.72%, root error -1.26%, and local MPJPE +0.75% (worse).
  Its checked ONNX/video are supplemental only and are not called an Isaac/PPO fine-tune.
- [ ] Official stock Isaac baseline establishes the preregistered novelty gap.
- [ ] `ladder-plan.json` preserves the evidence/portal reserves and
  `ladder-outcome.json` exactly discloses every completed or omitted candidate.
- [ ] Selected checkpoint wins on validation—not only train—references.
- [ ] Official final headline comes from a newly reserved test family (preferred), or
  explicitly discloses that v2 test was previously used once after proxy-adapter freeze.
- [ ] Stock and selected policy each have all 24 final trials (8 motions × 3 seeds).
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
- [ ] Stop artifact work by 23:14 PT and leave the final 45 minutes for logged-out link
  verification, teammate review, saving every field, and changing DRAFT to submitted.

## Licensing and safety

- [ ] Named NVIDIA/Isaac EULA acceptance recorded before Isaac provisioning.
- [ ] `sonic-assets.json` reports the pinned SONIC revision, 69 files, 68,376,574 bytes,
  zero Git LFS pointers, and manifest SHA-256 `4c7faab7...62399e3` before Isaac starts.
- [ ] NVIDIA Open Model License accompanies derivative weights.
- [ ] Apache-2.0 and third-party notices included.
- [x] Dataset card says no BONES-SEED and accurately describes synthetic generation.
- [x] Public copy includes the portal-requested exact acknowledgement, "Motion Data by
  Bones Studio," without implying BONES-SEED was used.
- [x] Simulation-only and real-robot safety limitations are visible.
