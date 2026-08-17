---
license: other
library_name: onnxruntime
tags:
  - robotics
  - unitree-g1
  - onnx
  - mujoco
  - experimental
---

# Shadow Dance affine deployment adapter (experimental proxy)

> **Not the official SuperSONIC fine-tune.** This is a small supervised affine
> calibration appended to NVIDIA's public GEAR-SONIC decoder. It was not trained with
> Isaac Lab/PPO, was not evaluated with WBT-Bench, and must not be reported as an
> official challenge score or as evidence that the required fine-tune was completed.

Team SELTZER built this transparent account-free fallback while licensed compute was
unavailable. It keeps the public decoder's `obs_dict [1,994] -> action [1,29]` contract,
so it can replace the stock decoder in NVIDIA's public deployment loop. Use the bundled
unchanged `model_encoder.onnx` for the G1 reference encoder.

## Method and leakage control

- Parent: `nvidia/GEAR-SONIC`, revision
  `9c0ff22b4ffec27c5392e8e284eb2f2df7a5b4e2`.
- Parent decoder SHA-256:
  `c7241a123eaa36b5d64bad19540efde93cac1ad443bd4572fd12ca99898118ed`.
- Twelve authored gancho **training** motions (3,046 frames) supplied stock actions and
  authored joint targets to a per-joint least-squares calibration.
- Gain and bias were bounded, then shrunk 90% toward the identity transform
  (`alpha=0.10`).
- Selection used four separate gancho validation motions. The adapter was hash-frozen
  before any of the eight v2 final-test motions were opened.
- Final tests contain four dips and four ganchos and are reported completely; there was
  no post-test retuning.

The exported decoder SHA-256 is
`caf8b40ca7de141498b3d1160654a2531ce45c149f6768d6cc0a2474bd5add27`.
ONNX checker passes, five CPU Runtime probes are finite, and the appended affine graph
matches the specified gain/bias with zero feed-forward numerical error.

## Frozen deterministic MuJoCo proxy result

| Metric, macro over 8 fresh motions | Stock | Adapter | Change |
|---|---:|---:|---:|
| Upright completion | 8/8 | 8/8 | unchanged |
| Local MPJPE | 29.229 mm | 29.448 mm | **+0.75% (worse)** |
| Global MPJPE | 85.427 mm | 84.810 mm | -0.72% |
| Root-position error | 77.687 mm | 76.706 mm | -1.26% |
| Joint RMSE | 9.544 deg | 8.628 deg | -9.60% |

This is a mixed result, not a headline win: joint tracking improves materially, global
and root errors improve slightly, and local MPJPE becomes modestly worse. The proxy uses
MuJoCo 3.x and CPU ONNX Runtime with one deterministic run per motion. It does not model
Isaac/WBT-Bench robustness or the required three-seed evaluation.

## Files

- `model_encoder.onnx`: unchanged public GEAR-SONIC G1 encoder.
- `shadow-dance-affine-proxy-decoder.onnx`: derivative decoder with the adapter appended.
- `adapter.json`: training provenance and frozen gain/bias.
- `selection.json`: validation-only selection record.
- `final-comparison.json`: all eight fresh test motions and bound report hashes.
- `onnx-validation.json`: graph/runtime validation and exact hashes.
- `evidence/`: all 12 training-statistic reports, all heldout selection/export reports,
  and all 16 stock/selected fresh-test reports.
- `observation_config.yaml`: parent deployment observation contract.
- `LICENSE` and `NOTICE`: required model license and attribution.

Dataset and generator:
https://github.com/cristpierce/shadow-dance/releases/tag/shadow-dance-v2.0.0

## Safety and license

Simulation only. No real-robot deployment or safety claim is made. The Unitree G1 can
fall or damage hardware if an unvalidated controller is deployed. Real-robot use needs
independent limits, fall protection, an emergency stop, and qualified supervision.

The parent model and this derivative are distributed under the bundled NVIDIA Open
Model License. **Licensed by NVIDIA Corporation under the NVIDIA Open Model License.**

Challenge acknowledgement: **Motion Data by Bones Studio.** No BONES-SEED motion or
derivative is included or used by this independently authored dataset.
