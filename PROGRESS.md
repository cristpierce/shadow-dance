# SuperSONIC submission progress

**Last updated:** 2026-08-14 16:57 PT
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
- [x] Pinned the NPA SONIC L40S image by digest and verified its direct-image SkyPilot
  materialization locally without allocating compute.
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
- [x] Expanded the frozen ladder from debug-only budgets to independent 5/500/4,000
  iteration candidates with a 10-hour and approximately $17.47 worker cap.
- [x] Passed 14/14 local tests against the pinned NVIDIA converter/MJCF plus Ruff, Bash,
  YAML, dataset-inventory, publication dry-run, and read-only cloud-plan checks.
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
- [x] Finished the diff/security review, pushed the frozen implementation, and updated
  [upstream PR #1](https://github.com/Durp06/shadow-dance/pull/1).

## Ready after entrant handoff

- [ ] Run the stock novelty gate and bounded checkpoint ladder as soon as the named
  licence acceptance, Nebius authentication/credit, and publication credentials exist.

## External gates

- [ ] Named acceptance of the three NVIDIA/Isaac licence agreements and authorization
  for `OMNI_KIT_ACCEPT_EULA=YES` and `ISAACSIM_ACCEPT_EULA=YES`.
- [ ] Interactive Nebius profile/login plus visible challenge credit, project, object
  storage credentials, and L40S quota. The pinned CLI itself is installed.
- [ ] Hugging Face account/handle confirmation, write-capable authentication, and
  creation of public dataset/model repositories.
- [ ] Organizer WBT-Bench package or Discord release link. The official page still
  promises it, but no public package was discoverable in the challenge portal resources,
  NVIDIA/Nebius repositories, or exact-name GitHub search as of August 14.
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
4. Run the 5/500/4,000 checkpoint ladder with validation and retention at each gate.
5. Freeze the winner, open the untouched test split, export, validate, render, hash,
   and publish the selected checkpoint.
6. Replace every bracketed submission value from raw evidence, verify public links,
   then submit the portal entry.
