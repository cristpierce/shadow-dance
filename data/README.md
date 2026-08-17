# Data layout

`generated-v2/csv/` contains the 54 team-authored v2 source trajectories in an
inspectable degree/centimetre schema. `manifests/shadow-dance-v2.json` is authoritative
for split, provenance, phase timing, parameters, IK residuals, and hashes;
`splits-v2/` is its loader-friendly index. The original `generated/`,
`manifests/shadow-dip-v1.json`, and `splits/` paths remain frozen for v1 auditability.

SONIC-ready PKLs are committed in `generated-v2/train/`, `generated-v2/heldout/`,
`generated-v2/preflight/`, and `generated-v2/test/` so the cloud workflow has no hidden
local input. The `heldout` split is selection-validation. The four legacy motions in
`preflight` were locally explored before v2 and are excluded from training, selection,
and final reporting; `test` is opened only after checkpoint selection. Regenerate and
verify the frozen bundle with:

```powershell
shadow-generate --profile dance-v2 --sonic-root C:\path\to\GR00T-WholeBodyControl
shadow-validate --sonic-root C:\path\to\GR00T-WholeBodyControl `
  --dataset data/generated-v2 `
  --manifest data/manifests/shadow-dance-v2.json `
  --report results/reference-validation-v2.json
python scripts/verify_dataset_bundle.py --profile dance-v2
```

The eventual Hugging Face dataset revision will contain the same PKLs plus this source
and metadata. Compare every checksum to the manifest before training. The v2 manifest
SHA-256 is `20803a03d9e3ddf3c7d381f59fb35fa83faf9e0dcb22e42f6dd25d51c7d21bb1`;
the committed validation report SHA-256 is
`a9199a29d258d50eae2408bc55df3cb4989e2c5107734e684a777a15dbcec5b4`.
All 30 v1 sequences and all 60 of their CSV/PKL hashes are unchanged inside v2.

Until Hugging Face authentication is available, the immutable public distribution is
[Shadow Dip v1.0.0 on GitHub](https://github.com/cristpierce/shadow-dance/releases/tag/shadow-dip-v1.0.0).
Its 2,112,908-byte archive has SHA-256
`94099f031b8a0b5ea36c809e705f77088342a6b54d73f9735508b146841c1370` and is tagged at
commit `684c6e8130505d9d85ea0a5048d8121179b6cd68`.
