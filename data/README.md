# Data layout

`generated/csv/` contains the 30 team-authored source trajectories in an inspectable
degree/centimetre schema. `manifests/shadow-dip-v1.json` is authoritative for split,
provenance, phase timing, parameters, IK residuals, and hashes. `splits/` is a simple
loader-friendly index.

SONIC-ready PKLs are committed in `generated/train/`, `generated/heldout/`, and
`generated/test/` so the cloud workflow has no hidden local input. The `heldout` split
is selection-validation; `test` is opened only after checkpoint selection. Regenerate
and verify the frozen bundle with:

```powershell
shadow-generate --sonic-root C:\path\to\GR00T-WholeBodyControl
shadow-validate --sonic-root C:\path\to\GR00T-WholeBodyControl
```

The eventual Hugging Face dataset revision will contain the same PKLs plus this source
and metadata. Compare every checksum to the manifest before training. The frozen
manifest SHA-256 is
`1b2045380e09e6276c5ac4ff4c2bb1c7bd5903a974940f9928d7351b5f90a5d1`; a clean local
regeneration reproduced the manifest and all 60 CSV/PKL files byte-for-byte. The
committed validation report SHA-256 is
`5aedeedee8d775c34c0b5c67f235591829da281cfa9385b8b8a15b8c10a6b999`.
