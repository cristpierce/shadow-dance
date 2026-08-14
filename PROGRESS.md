# SuperSONIC submission progress

**Last updated:** 2026-08-13 23:25 PT
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
- [x] Generated the complete 22-sequence `shadow-dip-v1` set: 18 train/rehearsal and
  4 independently parameterized held-out hero motions.
- [x] Passed 22/22 hard reference checks with zero warnings; independently round-tripped
  the CSV schema through NVIDIA's upstream converter; visually inspected the hero hold.
- [x] Added Linux CI that regenerates and validates the complete set from the pinned
  NVIDIA checkout.

## In progress

- [ ] Commit, push to the fork, and open a PR to `Durp06/shadow-dance`.

## External gates

- [ ] Named acceptance of the three NVIDIA/Isaac licence agreements and authorization
  for `OMNI_KIT_ACCEPT_EULA=YES` and `ISAACSIM_ACCEPT_EULA=YES`.
- [ ] Nebius challenge credit/authentication visible to the operator.
- [ ] Hugging Face authentication and choice/creation of public dataset/model repos.
- [ ] A working browser session for authenticated Ultimate Bots portal actions, or
  manual portal entry by a team member using the prepared copy and links.
- [ ] Teammate merges the PR or grants `cristpierce` write access to the canonical repo.

## Not yet claimed

- Stock SONIC failure on the hero reference.
- Any training improvement, WBT-Bench score, checkpoint, ONNX export, policy render, or
  real-robot execution.

## Next execution order

1. Commit/push/PR and publish the generated dataset once Hugging Face is authenticated.
2. Isaac sample smoke and stock held-out baseline.
3. Go/no-go novelty decision; adjust the target if stock already succeeds.
4. 5/25/100 checkpoint ladder, held-out and retention eval at every decision gate.
5. Select, export, validate, render, hash, and publish the best checkpoint.
6. Replace every bracketed submission value from raw evidence, verify public links,
   then submit the portal entry.
