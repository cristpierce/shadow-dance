# SuperSONIC submission progress

**Last updated:** 2026-08-16 17:31 PT
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
  5/250/500/2,000/4,000 iteration candidates. Its quality-first scheduler keeps the smoke,
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
  5/250/500/2,000/4,000 declared ladder, switches to a quality-first subset when
  necessary, reserves two hours for final evidence plus 45 minutes for portal
  submission, and records every deadline or runtime omission in hash-bound evidence.
- [x] Rechecked the official rules and public competitive field on deadline day. The
  strongest visible entries now have real ONNX/video evidence; Shadow Dance's remaining
  differentiator is its independent validation/test design, fundamentals-retention
  check, reproducibility, and raw-evidence publication—but only if the run is unlocked.

- [x] Audited the active image's OCI build history and found its G1 visual meshes were
  Git LFS pointer stubs. Added a pre-Isaac, model-weight-excluding sparse hydration gate
  pinned to the embedded SONIC commit, with exact 69-file/68,376,574-byte/manifest-hash
  attestation. Proved the Linux-canonical empty-root hydration in the exact image
  (12.4 seconds) and from Windows (15.5 seconds), plus cached revalidation; the full
  local suite now passes 34 tests with 3 licensed-runtime
  skips. A failed checkout also leaves a structured recovery report for evidence upload.
- [x] Corrected the cloud task's baked-Python path from the retired image's
  `/opt/npa/sim/venv/bin/python` to the active OCI config's image-owned
  `NPA_IMAGE_PYTHON=/opt/npa/venv/bin/python`; the materializer now rejects drift.
- [x] Audited the active image's real filesystem ownership contract (`Config.User=root`)
  and made G1 repair portable to a non-root rebuild with narrowly scoped non-interactive
  elevation. Added a digest-pinned WSL/Docker fallback that requires the entrant-owned
  licence markers, defaults to 4/8 environments and a 5/250 ladder, retains outputs
  locally, and cannot weaken the managed workflow's mandatory S3 mode.
- [x] Installed Docker Engine 29.1.3, Git LFS 3.4.1, NVIDIA Container Toolkit 1.19.1,
  and verified public CUDA 12.8.1 GPU passthrough in WSL. The laptop remains below the
  documented Isaac 5.1 RAM, VRAM, and driver floors. The exact CUDA 13 image correctly
  refuses driver 577.13 before process startup, so local compute is blocked pending a
  user-owned driver update/reboot and is not a claimed supported runtime.
- [x] Pulled the exact 9,335,925,665-byte active image identity and completed every
  legal open-only probe available inside it: non-Isaac imports, zero baked Isaac
  packages, EULA-unaccepted cache status, 30-sequence dataset verification, anonymous
  base-model hash verification, and real G1 asset repair. The container exposed a
  Windows-CRLF attestation bug; forcing LF now passes identically on Windows and Linux
  at 69 files, 68,376,574 bytes, and manifest `4c7faab7...62399e3`.
- [x] Closed the deadline ladder's 500-to-4,000 quality gap before any training run by
  preregistering a 2,000-iteration candidate. Its 3.5-hour stage budget and 3-hour
  training timeout are grounded in public same-challenge evidence of 2,000 iterations
  at 512 environments in 9,544.61 seconds. The quality-first scheduler still prefers
  4,000 whenever it fits and otherwise exposes four new 2,000-stage routes through
  17:29 PT without changing selection or retention thresholds.
- [x] Completed a focused review of the pinned SONIC runtime at `0a87181c`: the training
  command matches the official `sonic_release` contract, the five-iteration smoke is
  guaranteed to emit an atomic `last.pt` because the callback is overridden to save
  every five global steps, evaluation writes `metrics_eval.json` to the supplied output
  directory, and the universal-token export produces the expected five ONNX graphs plus
  `model_config.yaml`. Bash syntax passed; the current full local suite reports 34 passed
  and 3 simulator-only skips, and Ruff passes. No licensed runtime was invoked.
- [x] Passed both public CI copies at the last published head before this
  progress-only update:
  `f36878bb19291e620e2571266b6485a1b038472a`: [main run
  31979929826](https://github.com/cristpierce/shadow-dance/actions/runs/31979929826)
  and [feature run
  31979929089](https://github.com/cristpierce/shadow-dance/actions/runs/31979929089).
  The main artifact was downloaded and independently checked: 69 G1 assets,
  68,376,574 bytes, zero LFS pointers, and canonical manifest `4c7faab7...62399e3`.
- [x] Updated the upstream PR body and existing owner handoff comment to the exact
  `f36878b` head and passing runs. PR #1 remains open, clean, and mergeable; merge still
  requires `Durp06` or another collaborator with write access.
- [x] Ran a secret-suppressing WSL cloud-readiness probe at 23:33 UTC. NPA/SkyPilot is
  installed, but `npa cluster list --format json` reports `NOT_CONFIGURED`; no Nebius
  project, cluster, kubeconfig, or Kubernetes context exists. SkyPilot's detailed check
  reports Nebius compute/storage disabled, and NPA preflight reports no S3 or Hugging
  Face credentials. The top-level SkyPilot `status: ok` only verifies the local
  installation and must not be treated as cloud readiness.
- [x] Removed every free local operator-tool gap found by that probe. The existing
  Nebius CLI 0.12.254 now resolves through `~/.local/bin`; checksum-verified Terraform
  1.13.3 and kubectl 1.34.10 are installed there; and SkyPilot's `socat` requirement is
  satisfied by user-local Ubuntu 24.04 `socat` 1.8.0.0 plus `libwrap0`. A fresh
  SkyPilot verification now reaches the expected missing-kubeconfig/account gate rather
  than a missing-tool gate. No account, cloud resource, licence variable, or charge was
  created by this setup.
- [x] Prepared an isolated native-Windows contingency without crossing the NVIDIA
  licence gate: uv 0.11.15, Python 3.11.15, and an empty ignored virtual environment;
  an exact detached SONIC checkout at `0a87181c`; and the verified 69-file G1 asset
  tree. No Isaac Sim or Isaac Lab package was downloaded or invoked.
- [x] Downloaded the public `nvidia/GEAR-SONIC` base checkpoint without Hugging Face
  authentication and independently rehashed both pinned files. `last.pt` is
  469,418,283 bytes with SHA-256 `e6bdab3f...ded8909`; `config.yaml` is 28,331 bytes
  with SHA-256 `f0818779...ab629c7`. The failed interactive Hugging Face login is now
  a publication gate only, not a training-input gate.
- [x] Recomputed the immutable deadline planner at 17:30 PT. A run beginning then can
  schedule stages 5/250/500 with 13,403 candidate seconds available after the two-hour
  finalization and 45-minute portal reserves. That excludes stock evaluation,
  environment installation, and cloud cold-start time, so it is an upper bound rather
  than an executable claim while both compute routes remain gated.
- [x] Identified and prepared a second below-floor local contingency based on NVIDIA's
  official Isaac Lab 2.3.2 NGC image. Its public manifest is pinned to the amd64 digest
  `f07c37e3...24be07f` (29 layers; 8,408,106,479 compressed bytes). A fail-closed ignored
  wrapper and derived Dockerfile are Bash-parse clean, do not bake acceptance, and reuse
  the already verified source/assets/checkpoint. No image layer was pulled or run.

## Ready after entrant handoff

- [ ] Run the stock novelty gate and bounded checkpoint ladder as soon as the named
  licence acceptance, Nebius authentication/credit, and publication credentials exist.

## External gates

- [ ] Named acceptance of the three NVIDIA/Isaac licence agreements and authorization
  for the documented run-scoped `ACCEPT_EULA=Y` value plus the project-owned
  `ENTRANT_NVIDIA_EULA_ACCEPTED=YES` marker.
- [ ] For either laptop fallback, treat the current 577.13 driver and 12 GB VRAM as
  below NVIDIA's documented Isaac Sim 5.1 minimums. The separate CUDA 13 NPA image was
  rejected by this driver, but the pinned official Isaac Lab 2.3.2 image has not been
  run and must not be described as incompatible in advance. After explicit licence
  acceptance, try only its cheapest import probe and stop on any driver or memory
  failure. No autonomous driver update or reboot is authorized.
- [ ] Interactive Nebius profile/login plus visible challenge credit, a `us-central1`
  project, object-storage credentials, and RTX PRO 6000 Managed Kubernetes quota. A
  23:33 UTC read-only probe positively confirmed that these are not configured; only the
  pinned local CLI/SkyPilot environment is ready. The portal's claim button opens the
  Builder Program; its terms grant an initial $25 AI Cloud code after email verification
  and a second $25 only about 30 days later. The initial code/balance has not been confirmed,
  so the advertised `$50` cannot yet be budgeted for the deadline run. Standard promo
  redemption also requires a user-owned $25 card activation; no payment is authorized
  by the general project approval. Nebius publishes a default `us-central1` regular
  RTX PRO 6000 quota of zero, and Managed Kubernetes nodes use the same Compute quota;
  the entrant must verify an actual quota of at least one or request/escalate it now.
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

1. Obtain the entrant-owned licence handoff and unlock either Nebius or a local
   contingency. Hugging Face publication can wait until a real model exists.
2. Materialize the no-compute cloud plan, try the smaller pinned official NGC 2.3.2
   container, or install the native runtime; first run only the cheapest CUDA/Isaac
   import probe, then the stock validation baseline.
3. Go/no-go novelty decision; adjust the target if stock already succeeds.
4. Run the deadline-planned checkpoint ladder with validation and retention at each
   gate. The 2,000-step route closed at 17:29 PT. The current route is 5/250/500 through
   19:29 PT, followed by 5/500 through 19:59 PT, 5/250 through 20:29 PT, and smoke-only
   through 20:59 PT. The planner refuses any route that cannot preserve finalization
   and portal reserves.
5. Freeze the winner, open the untouched test split, export, validate, render, hash,
   and publish the selected checkpoint.
6. Replace every bracketed submission value from raw evidence, verify public links,
   then submit the portal entry.
