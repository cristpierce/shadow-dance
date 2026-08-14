# Historical handoff — superseded

> **Do not execute this document as the current plan.** Use
> [PROGRESS.md](PROGRESS.md) for live status and
> [docs/cloud-runbook.md](docs/cloud-runbook.md) for the verified operator commands.
> The August 13 deadline-focused
> [submission improvement plan](docs/research/2026-08-13-supersonic-submission-improvement-plan.md)
> supersedes this document where they conflict, especially on paired SMPL, BONES-SEED,
> local hardware, and schedule assumptions.

Continuing work started on the Mac mini (session `ddf7a70f`, Aug 2 2026). This file is
the original handoff and remains useful historical context.

## What this is

Ultimate Bots **Ghost Trial 03 — SuperSONIC Challenge**. Fine-tune NVIDIA's SONIC
whole-body controller (`NVlabs/GR00T-WholeBodyControl`) so a Unitree G1 performs
**solo partner-dance lead** — Texas two-step / swing with no follow.
Hero move: **the shadow dip**. Track: **Performance Arts**. $1,000.

Deadline **Aug 16 2026, 11:59 PM PDT**. Internal target: submit **Aug 15**.

## Decisions already made (don't re-litigate)

1. **Config is `sonic_release`**, not `sonic_bones_seed`. The SOMA/BVH encoder needs
   64+ GPUs. This rules out the entire BVH ingestion route.
2. **The road is SMPL.** Fine-tuning needs paired `motion_file` (G1 retargeted) +
   `smpl_motion_file` (SMPL human) — every clip must exist in both formats. SMPL is
   what monocular video-to-motion models emit natively.
3. **Data is the submission.** $50 of Nebius ≈ 15–25 GPU-hr against docs that recommend
   64+ GPUs and 100K iterations. There is exactly one real fine-tune. Curation is the lever.
4. **The 3060 Ti is the QA machine, not the training machine.** 8 GB VRAM → `num_envs`
   4–16, headless. It exists to prove the pipeline is correct before credits are spent.
5. **Quest 2 teleop is a stretch goal, explicitly off the critical path.** The teleop
   encoder (head + 2 wrists) is real, but the shipped VR plumbing is PICO 4 Ultra /
   XRoboToolkit / CloudXR. There is no Quest path. Do not let this eat the two weeks.
6. **Hero move = the dip; demo = the full phrase** (step → turn → spin → dip → recover).

## Hardware

| Machine | Role |
|---|---|
| Gaming PC — RTX 3060 Ti 8 GB, 32 GB RAM | Isaac Lab: replay QA, smoke tests, ONNX export |
| Mac mini | `gear_sonic/data_process/` conversion (no Isaac Lab needed), writing, portal |
| Nebius $50 | The one fine-tune run (+ ~30% held for one recovery run) |

## Open items

- [ ] **OS on the gaming PC?** Training stack requires Ubuntu 22.04+, CUDA 12.x, Python 3.11.
      If Windows → dual-boot or WSL2. **This is the day-1 blocker.**
- [ ] Portal housekeeping: start a team, claim $50 Nebius, connect Discord + GitHub,
      set country, **switch track Martial Arts → Performance Arts**.
- [ ] Toolchain on `sample_data` before any custom capture.
- [ ] Studio-vs-OSS bake-off on one 10 s test clip.

## Next commands (on the GPU box, after Isaac Lab install)

```bash
python check_environment.py --training
pip install huggingface_hub && python download_from_hf.py --training

# smoke test — should print reward metrics after ~1 min
python gear_sonic/train_agent_trl.py \
  +exp=manager/universal_token/all_modes/sonic_release \
  num_envs=16 headless=True ++algo.config.num_learning_iterations=5

# the tool the whole data strategy rests on
python gear_sonic/train_agent_trl.py \
  +exp=manager/universal_token/all_modes/sonic_release \
  ++replay=True num_envs=4 headless=False
```

## Portal state as of Aug 2

Signed in as durpsalt@gmail.com ("Myles"), GHOST branch active — registration is done.
Entry is **DRAFT, 1 of 7 fields complete** (only Track, and it's set to the wrong one).
No team started, compute unclaimed, Discord and GitHub unconnected, country empty.
The entry form stays locked until a team exists — solo counts as a team of one.
