# Dataset card — Shadow Dance v2

## Summary

`shadow-dance-v2` is Team SELTZER's synthetic Unitree G1 motion bundle for Ultimate
Bots SuperSONIC Trial 03. It extends the immutable Shadow Dip v1 payloads with a
Shadow Gancho family: the robot establishes a partner frame, pivots into an off-axis
one-foot hold, raises and hooks the free leg, then returns to neutral.

| Property | Value |
|---|---|
| Robot | Unitree G1, 29 DOF |
| Reference rate | 50 Hz |
| Train | 12 dips + 12 ganchos + 10 fundamentals rehearsals |
| Selection-validation (`heldout`) | 4 dips + 4 ganchos |
| Disclosed preflight | 4 legacy v1 dip tests; excluded from training and reporting |
| Untouched final test | 4 dips + 4 ganchos |
| Human footage | None |
| BONES-SEED | Not used |
| SMPL | `dummy` in SONIC; no invented human skeleton |
| License | Apache-2.0 for team-authored code and trajectories |

All 30 v1 sequences and all 60 of their motion-library/CSV hashes are unchanged in v2.
The v1 GitHub release
therefore remains an immutable audit anchor while the combined v2 directory is the
default training input.

## Creation

The dip family is unchanged from v1. Its authored root, torso, arm, and step keyframes
use bounded MuJoCo inverse kinematics for both legs.

The gancho adds nine C2-continuous phase keyframes:

1. establish the absent-partner frame;
2. transfer weight and step the free foot back;
3. pivot and lift;
4. descend over the planted stance foot;
5. sweep the free leg into a hooked pose;
6. hold, recover, replace the foot, and settle.

The continuously planted stance foot and both landings are solved against NVIDIA's
pinned G1 MJCF. Once the free leg is airborne, its pose is authored in joint space; it
is checked for joint limits, velocity, floor clearance, self-contact, and one-foot
support instead of being over-constrained to an arbitrary six-DOF sole orientation.
The gancho foot rises 29.4–31.4 cm across the published family.

Every PKL has a degree/centimetre CSV counterpart. The manifest records its exact
specification, phase windows, support-foot IK residual, file paths, upstream MJCF
commit, and SHA-256. The Bones-style CSV columns are an interoperability format only;
they contain no Bones motion data.

## Splits and leakage

The 34 training motions, eight checkpoint-selection motions, four disclosed preflight
motions, and eight final-test motions are physically separate files. Gancho selection
and test values use distinct amplitude, duration, back-step, and cross-body geometry.
The v2 test split must remain unopened by the official policy evaluator until a
checkpoint label and hash have been frozen from validation results.

Before v2 was designed, the four v1 test payloads were explored with a local stock
deployment proxy. They are therefore relabelled `preflight` in v2 and excluded from
training, checkpoint selection, and final reporting. The proxy was subsequently run
on all eight v2 `heldout` files to compare the dip and gancho families. It is not a
final-test or organizer benchmark result, and none of the fresh v2 final-test payloads
has been supplied to a policy evaluator.

## Quality gates

`results/reference-validation-v2.json` is bound to the manifest and payload hashes.
All 54 sequences pass with zero warnings. Worst cases across the full bundle are:

| Check | Result |
|---|---:|
| Support/foot IK position and orientation residual | 6.957 mm / 3.736° |
| Joint-limit violation | 0 rad |
| Peak pelvis drop / waist roll | 0.147 m / 0.495 rad |
| Gancho foot height | 0.314 m |
| Peak joint speed vs Isaac limit | 45.36% |
| Peak reported joint acceleration | 226.10 rad/s² |
| Floor penetration tolerance | 7.923 mm |
| Planted-foot horizontal speed, p95 | 0.0752 m/s |
| Two-foot support margin | +0.0242 m minimum |
| Hero deep-hold support margin | +0.0173 m minimum |
| MuJoCo self contacts | 0 |

Reference QA shows that the desired trajectory is internally coherent. It does not
prove that a stock or fine-tuned policy executes it, and it is not real-robot safety
certification.

## Account-free stock preflight

The public NVIDIA GEAR-SONIC deployment encoder and decoder at revision
`9c0ff22b4ffec27c5392e8e284eb2f2df7a5b4e2` were run through ONNX Runtime in a Python
port of NVIDIA's public MuJoCo deployment observation/action contract. Across the four
gancho validation motions, stock completed without the proxy fall cutoff and averaged
28.881 mm local MPJPE, 10.139° joint RMSE, and 114.498 mm root-position error. One of
four exceeded the training guide's 30 mm local target. The corresponding four dip
validation runs averaged 28.958 mm local MPJPE and 42.709 mm root error.

This is useful preflight evidence that the gancho stresses global tracking much more
than the dip. It is explicitly **not** Isaac Lab, the organizer's WBT-Bench, or a final
challenge score. Only matched official stock/fine-tuned runs may populate the portal's
before/after claims.

## Reproduction

With the pinned SONIC source/assets available:

```powershell
.venv\Scripts\shadow-generate --profile dance-v2 --sonic-root $env:SONIC_ROOT
.venv\Scripts\shadow-validate --sonic-root $env:SONIC_ROOT `
  --dataset data/generated-v2 `
  --manifest data/manifests/shadow-dance-v2.json `
  --report results/reference-validation-v2.json
.venv\Scripts\python scripts/verify_dataset_bundle.py --profile dance-v2
```

The authoritative manifest SHA-256 is
`20803a03d9e3ddf3c7d381f59fb35fa83faf9e0dcb22e42f6dd25d51c7d21bb1`; the committed
validation report SHA-256 is
`a9199a29d258d50eae2408bc55df3cb4989e2c5107734e684a777a15dbcec5b4`.

## Limitations

- The data is procedural and measures interpolation within two declared motion
  families, not broad dance generalization.
- Peak acceleration is reported transparently but is not a real-hardware actuation
  guarantee.
- The public proxy uses CPU ONNX Runtime and MuJoCo, not TensorRT or Isaac Lab.
- Real deployment requires vendor limits, a fall zone, an operator stop, and separate
  hardware testing.
