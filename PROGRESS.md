# SuperSONIC submission progress

**Last updated:** 2026-08-16 13:55 PT
**Branch:** `feature/supersonic-submission`
**Deadline:** 2026-08-16 23:59 PT

This is the concise multi-session execution ledger. Evidence belongs in linked files;
status here must remain truthful.

## Complete

- [x] Audited official challenge requirements, judging signals, portal fields, SONIC
  training/export path, BONES licensing, and Nebius workflow.
- [x] Confirmed portal team `SELTZER` has 2 members, Performance Arts is selected,
  GitHub/Discord are connected, and the entry remains a draft.
- [x] Forked `Durp06/shadow-dance` to `cristpierce/shadow-dance`; upstream grants the
  current account read-only access, so changes must arrive via PR unless access changes.
- [x] Pinned GR00T-WholeBodyControl commit
  `c374bae5b9039cd0ee71377e654d11ce1bc69e1d`.
- [x] Implemented generator, MuJoCo IK, frozen split contract, validator, reference
  renderer, training/eval/render/export wrappers, and ONNX checker.
- [x] Generated the complete 30-sequence `shadow-dip-v1` set: 22 train/rehearsal,
  4 independently parameterized selection-validation hero motions, and 4 independently
  parameterized final-test hero motions.
- [x] Passed 30/30 hard reference checks with zero warnings; independently round-tripped
  both identity and non-identity-heading CSVs through NVIDIA's upstream converter;
  visually inspected the hero hold.
- [x] Added Linux CI that regenerates and validates from the pinned NVIDIA checkout,
  then checks exact inventories/schemas/splits and cross-platform numeric equivalence
  of every CSV field at `2e-5` in its degree/centimetre schema and every SONIC PKL,
  manifest IK value, and QA metric at `1e-6` absolute tolerance.
- [x] Committed and pushed the implementation to `cristpierce/shadow-dance` and opened
  [upstream PR #1](https://github.com/Durp06/shadow-dance/pull/1).
- [x] Passed the complete public Linux CI run, including NVIDIA Git LFS assets:
  [run 31775796089](https://github.com/cristpierce/shadow-dance/actions/runs/31775796089).
- [x] Pinned the public SONIC base model revision, byte size, and SHA-256 independently
  from Hugging Face metadata.
- [x] Replaced the now-quarantined NPA L40S image with the public active
  `sonic-k8s-host-mounted` RTX PRO 6000 image, pinned its verified GHCR digest, updated
  the operator to commit `43ffee6`, and retained a no-compute materialization gate.
- [x] Installed and verified the pinned NPA/SkyPilot operator environment in WSL2,
  including the no-sudo bootstrap fallback required by this machine.
- [x] Implemented a fail-closed cloud pipeline with incremental S3 recovery, novelty
  and retention gates, validation-only checkpoint selection, untouched final testing,
  ONNX Runtime verification, release hashes, and optional Hugging Face publication.
- [x] Added three-seed final evaluation: 12 untouched trials per policy with exact
  motion/seed inventories and source-summary hashes bound into the final comparison.
- [x] Freshly regenerated all 30 motions in an isolated directory: the manifest and all
  60 CSV/PKL payloads are byte-identical; the QA report is identical after normalizing
  its recorded temporary dataset and manifest paths.
- [x] Strengthened the hero geometry to a 14.7 cm pelvis drop and 28.1-degree waist
  roll while retaining 30/30 clean reference checks and zero warnings.
- [x] Added owned forward-walk and true heading-turn references for both lead directions,
  closing the official WBT fundamentals gap without importing restricted BONES-SEED data.
- [x] Verified the public dataset publisher in fail-closed dry-run mode: 68 files,
  30 PKLs, 3,732,169 bytes, and manifest/validation hashes bound into the plan.
- [x] Confirmed the motion converter, G1 MJCF, training entrypoint, evaluation entrypoint,
  and configuration used by the dataset are compatible with the SONIC commit embedded
  in the pinned cloud image; the only motion-loader delta is post-load memory cleanup.
- [x] Expanded the frozen ladder from debug-only budgets to independent
  5/250/500/4,000 iteration candidates. Its quality-first scheduler keeps the smoke,
  targets the largest candidate that fits, and fills spare time with the strongest
  smaller fallback while preserving the 10-hour worker cap.
- [x] Passed 23 local tests with 3 licensed-runtime skips, plus Ruff, Bash, YAML,
  dataset-inventory, publication dry-run, and read-only cloud-plan checks. The skipped
  probes require the still-gated Isaac runtime and are not represented as passes.
- [x] Added a deterministic target/before/after video builder and a publication gate
  that hashes every uncut source clip, the frozen comparison, and edited output.
- [x] Installed and verified official Nebius CLI `0.12.254` for Linux/amd64; no profile,
  cloud authentication, or paid resource was created.
- [x] Passed the frozen training contract's public Ubuntu/Python 3.11 evidence run:
  13/13 tests, 30/30 regenerated reference validations, zero warnings, and exact
  inventory/schema/split plus cross-platform numeric reproduction checks
  ([run 31851632473](https://github.com/cristpierce/shadow-dance/actions/runs/31851632473)).
  The same workflow reruns on every push; use the repository's Actions status for the
  post-documentation/video-label commit rather than treating this run ID as mutable.
- [x] Published the immutable public
  [Shadow Dip v1.0.0 reference release](https://github.com/cristpierce/shadow-dance/releases/tag/shadow-dip-v1.0.0)
  with GitHub-verified asset digests, full generated data, QA report, provenance, and a
  clearly labelled non-policy kinematic preview.
- [x] Reverified the public fallback without GitHub authentication: fork `main`, PR #1,
  raw README, release metadata, and both release downloads are anonymously readable;
  downloaded asset hashes match; the archive contains 30 CSVs, 30 PKLs, both JSON
  evidence files, all three split lists, documentation, `LICENSE`, and `NOTICE`; and the
  reference MP4 decodes as H.264/YUV420p at 640×480, 50 fps, and 5.26 seconds.
- [x] Finished the diff/security review, pushed the frozen implementation, and updated
  [upstream PR #1](https://github.com/Durp06/shadow-dance/pull/1).
- [x] Added and locally verified a deadline-aware ladder plan. It preserves the full
  5/250/500/4,000 protocol when time permits, switches to a quality-first subset when
  necessary, reserves two hours for final evidence plus 45 minutes for portal
  submission, and records every deadline or runtime omission in hash-bound evidence.
- [x] Rechecked the official rules and public competitive field on deadline day. The
  strongest visible entries now have real ONNX/video evidence; Shadow Dance's remaining
  differentiator is its independent validation/test design, fundamentals-retention
  check, reproducibility, and raw-evidence publication—but only if the run is unlocked.

## Ready after entrant handoff

- [ ] Run the stock novelty gate and bounded checkpoint ladder as soon as the named
  licence acceptance, Nebius authentication/credit, and publication credentials exist.

## External gates

- [ ] Named acceptance of the three NVIDIA/Isaac licence agreements and authorization
  for the documented run-scoped `ACCEPT_EULA=Y` value plus the project-owned
  `ENTRANT_NVIDIA_EULA_ACCEPTED=YES` marker.
- [ ] Interactive Nebius profile/login plus visible challenge credit, a `us-central1`
  project, object-storage credentials, and RTX PRO 6000 Managed Kubernetes quota. The
  current pinned CLI itself is installed.
- [ ] Hugging Face account/handle confirmation, write-capable authentication, and
  creation of public dataset/model repositories.
- [ ] Organizer WBT-Bench package or Discord release link. The official page still
  promises it, but no public package was discoverable in the challenge portal resources,
  NVIDIA/Nebius repositories, or exact-name GitHub search as of August 16.
- [ ] A working browser session for authenticated Ultimate Bots portal actions, or
  manual portal entry by a team member using the prepared copy and links.
- [ ] Teammate's exact registered name plus merge of the PR or write access for
  `cristpierce` on the canonical repo.

## Not yet claimed

- Stock SONIC failure on the hero reference.
- Any training improvement, WBT-Bench score, checkpoint, ONNX export, policy render, or
  real-robot execution.

## Next execution order

1. Obtain the entrant-owned licence/authentication handoff and mirror the immutable
   GitHub dataset release to Hugging Face.
2. Materialize the no-compute plan, then run the Isaac sample smoke and stock validation
   baseline once NVIDIA acceptance and Nebius authentication are present.
3. Go/no-go novelty decision; adjust the target if stock already succeeds.
4. Run the deadline-planned checkpoint ladder with validation and retention at each
   gate. The post-baseline scheduler can still target 4,000 steps through 14:59 PT by
   omitting lower-value intermediate candidates as time shrinks; later routes are
   5/250/500 through 19:29, 5/500 through 19:59, 5/250 through 20:29, and smoke-only
   through 20:59. The planner refuses any route that cannot preserve finalization and
   portal reserves.
5. Freeze the winner, open the untouched test split, export, validate, render, hash,
   and publish the selected checkpoint.
6. Replace every bracketed submission value from raw evidence, verify public links,
   then submit the portal entry.
