# Shadow Dance — Ghost Trial 03 (SuperSONIC Challenge)

> **August 13 update:** use the
> [deadline-focused submission improvement plan](../docs/research/2026-08-13-supersonic-submission-improvement-plan.md)
> as the current source of truth where it conflicts with this original design, especially
> for data format, BONES-SEED usage, evidence gates, and schedule.

**Status:** 22-sequence synthetic reference set and QA complete; stock-policy baseline pending Isaac
**Deadline:** Aug 16 2026, 11:59 PM PDT — **internal target: submit Aug 15**
**Track:** Performance Arts (confirmed in the portal on August 13)
**Entry:** one hero move + full phrase demo

---

## 1. The claim

Teach a Unitree G1 the **solo partner-dance lead** — Texas two-step / swing performed
without a follow. Hero move: **the shadow dip**, a deep asymmetric lean with large
centre-of-mass excursion, held and recovered with no partner counterweight.

Why it's a good claim:

- **Original.** Stock SONIC has generic dance in its training distribution, but not
  lead-frame partner dance, and not a dip. The arm frame held for an absent partner is
  what makes it read as partner dance rather than freestyle.
- **Tractable.** A *solo* dip has no external contact and no partner load, so there is
  nothing to model beyond the robot's own balance. Easier in sim than it looks.
- **Aligned with the benchmark.** Two-step is rhythmic weight-transfer locomotion.
  WBT-Bench includes a fundamentals check on walking and turning, so the surrounding
  phrase reinforces the objective score instead of fighting it.

## 2. Hard constraints

| Constraint | Value | Consequence |
|---|---|---|
| Compute budget | $50 Nebius (~15–25 GPU-hr) | One real fine-tune. No from-scratch training. |
| Docs recommend | 64+ GPUs, 100K iters to converge | We are doing a *short* fine-tune off `sonic_release/last.pt`. |
| Local GPU | RTX 3060 Ti, 8 GB VRAM, 32 GB RAM | QA and smoke tests only (`num_envs` 4–16). Not training. |
| Training OS | Ubuntu 22.04+, CUDA 12.x, Python 3.11 | **Day-1 risk if the gaming PC is Windows.** See §7. |
| Calendar | 14 days | Capture must finish by Aug 9. |

**The strategy that follows from this:** the dataset is the submission. Compute is fixed
and small; the only lever we control is data quality and curation.

## 3. Pipeline

Config is **`sonic_release`** (encoders: G1, teleop, SMPL). Not `sonic_bones_seed` — the
SOMA/BVH encoder needs 64+ GPUs, which rules out the entire BVH route.

Fine-tuning takes **two paired motion libraries**:

```
++manager_env.commands.motion.motion_lib_cfg.motion_file=<robot_filtered>    # G1 retargeted
++manager_env.commands.motion.motion_lib_cfg.smpl_motion_file=<smpl_filtered> # SMPL human
```

Every clip must exist in both. So the road is **SMPL** — which is what monocular
video-to-motion models emit natively.

```
video (multi-cam)
  → SMPL sequences            [Studio import  OR  GVHMR / WHAM]
  → retarget to G1 29-DoF     [→ Bones-SEED-style CSV, 120 fps]
  → motion_lib PKL            [convert_soma_csv_to_motion_lib.py --fps 30 --fps_source 120]
  → replay QA                 [++replay=True — LOCAL, free]
  → mix with BONES-SEED       [see §5]
  → fine-tune                 [Nebius, +checkpoint=sonic_release/last.pt]
  → eval + ONNX export        [local]
```

Note: `gear_sonic/data_process/` scripts **do not require Isaac Lab** and run on any
machine with `pip install -e gear_sonic/`. Conversion work can happen on the Mac.

## 4. Capture protocol

Target: **20–40 curated clips, 2–6 s each.** Small on purpose — matched to the budget.

### Rig
- 2–3 static cameras on tripods at ~0°, 45°, 90°. Never directly behind.
- 60 fps minimum; 120 fps for spins and the dip.
- **Lock exposure and focus.** Auto-exposure hunting wrecks pose estimation.
- Fast shutter (1/250 s+) — motion blur is the enemy of HMR.
- Bright, even, diffuse light. No windows or lamps behind you.
- Plain background that contrasts with your clothing.
- **Fitted clothing.** Baggy jeans and loose western shirts are the single most common
  cause of bad SMPL fits. This conflicts with normal two-step attire — dress for the
  tracker, not the dance floor.
- Full body in frame with headroom and floor visible. Tape-mark the floor so your feet
  never leave frame.

### Per take
1. Loud clap at the head of every take (multi-cam sync).
2. Two-second A-pose (arms ~45°, feet shoulder width) — clean init and scale reference.
3. Say the move name out loud (free labelling).
4. Fixed metronome BPM. Two-step ~170–190; swing ~136–180.

### Move list
Each move isolated, 8–12 clean reps, with a beat of stillness before and after.

1. Basic two-step, traveling
2. Rock step / triple step
3. Inside turn prep + travel
4. Outside turn
5. Lead's own 360° spin
6. **Dip: entry → hold → recover** (hero)
7. Transitions between the above
8. **Neutral take** — plain walking, turning in place, standing. Cheap insurance for the
   WBT-Bench fundamentals check.
9. One continuous 30–45 s freestyle phrase, for the demo video.

### Shooting the dip specifically
- Break into three phases and shoot each separately: entry (weight commit), hold
  (static 2–3 s), recovery.
- Shoot the **hold as a static pose** too — trivially easy for the tracker, gives a clean
  target keyframe.
- Shoot at **three amplitudes** (shallow / medium / full). If full exceeds G1's joint
  limits you already have fallbacks and don't reshoot.
- Shoot every move at three tempos (50%, 75%, performance). Slow versions retarget more
  reliably *and* give a natural training curriculum.
- **Keep the arm frame.** It's what makes it read as partner dance, and it's what a
  3-point teleop rig would drive.

## 5. Fine-tune set — the catastrophic-forgetting problem

WBT-Bench scores walking and turning fundamentals. Fine-tuning on nothing but dips will
degrade locomotion and tank the objective score while acing the subjective one.

The fine-tune set must be a **mix**: custom dance clips plus a rehearsal buffer of
general BONES-SEED motion.

- Starting point: **~25% custom / ~75% BONES-SEED**, sampled to include locomotion.
- This is an experiment, not a known constant. Sweep it if budget allows.
- **Signal to watch:** if `tracking_anchor_pos` or the walking/turning rewards fall while
  dip tracking improves, the custom ratio is too high.
- Document the sweep. This is exactly the "pipeline cleanliness" the rubric rewards.

## 6. Targets

| Metric | Target | Source |
|---|---|---|
| `success_rate` | > 0.97 | eval_agent_trl.py |
| `mpjpe_l` | < 30 mm | eval_agent_trl.py |
| `mpjpe_g` | < 200 mm | eval_agent_trl.py |
| `rewards/total` | 3.0+ | W&B |
| `rewards/anchor_pos_err` | < 0.15 m | W&B |
| `rewards/body_pos_err` | < 0.10 m | W&B |

Realistically a short fine-tune will not hit full-convergence numbers. What matters is
**delta vs the stock checkpoint on our dance clips**, with fundamentals held roughly flat.
Measure the stock baseline on our clips first so the before/after is quantitative, not
just visual.

## 7. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Gaming PC is Windows; stack needs Ubuntu 22.04+ | **High** | Dual-boot or WSL2 on day 1. Fallback: MuJoCo `visualize_motion.py` locally for QA, Isaac Lab only on Nebius. |
| 8 GB VRAM below Isaac Sim comfort | Medium | Headless, `num_envs` 4–16. Rendering is the VRAM hog. |
| Dip exceeds G1 waist/ankle range | Medium | Amplitude sweep already captured. Retarget → replay → scale down. Document the envelope — it's a finding, not a failure. |
| Monocular HMR fails on fast spins | Medium | Multi-cam; slow-tempo takes; 120 fps. |
| Catastrophic forgetting | Medium | §5 mixed set. |
| $50 burns out mid-run | Medium | Prove the entire path on `sample_data` locally first. Reserve ~30% of credits for one recovery run. |
| **Quest 2 teleop demo** | **Low value / high cost** | Documented VR path is **PICO 4 Ultra + XRoboToolkit**, or CloudXR — *not* Quest. The teleop encoder (head + 2 wrists) is real, but the Quest plumbing is not provided. **Stretch goal only. Do not let it touch the critical path.** |

## 8. Licensing

- Own footage → clean. Do not use third-party dance video.
- Check BONES-SEED terms before redistributing any derived clips.
- SMPL body model has its own non-commercial license — check before publishing the dataset.
- Winners grant Ultimate Bots the right to run the winning skill on real robots.

## 9. Schedule

| Date | Work |
|---|---|
| Aug 2 | Portal housekeeping. Toolchain: Ubuntu, Isaac Lab, `check_environment.py --training`. |
| Aug 3 | Prove the path end-to-end on NVIDIA `sample_data`: replay → smoke train → eval → ONNX export. **No custom data yet.** |
| Aug 4 | Studio-vs-OSS bake-off on one 10 s test clip. Pick a pipeline. |
| Aug 5–7 | Capture sessions. Reshoot window Aug 8–9. |
| Aug 7–9 | video → SMPL → retarget → PKL. Replay QA loop. Baseline the stock checkpoint on our clips. |
| Aug 9–10 | Build the mixed fine-tune set. |
| Aug 10–13 | Nebius fine-tune. Main run + one recovery run held in reserve. |
| Aug 13–14 | Eval, ONNX export, before/after renders. |
| Aug 14–15 | Writeup, HF uploads, GitHub repo, **submit Aug 15**. |
| Aug 16 | Buffer only. Never plan to submit on deadline day. |

## 10. Submission checklist (7 portal fields)

- [ ] Track → **Performance Arts**
- [ ] Project name — the move
- [ ] Writeup — what, why it's hard, how
- [ ] GitHub repo — code + training config
- [ ] ONNX policy — Hugging Face
- [ ] Dataset — Hugging Face
- [ ] Sim video — before and after
