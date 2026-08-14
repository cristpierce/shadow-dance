# Data layout

`generated/csv/` contains the 26 team-authored source trajectories in an inspectable
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
`3b7d91fbc4ec46c6591be3c583fba3dfbc9174045d3adb9eb8d0aa52a9abc3f0`; a clean local
regeneration reproduced the manifest and all 52 CSV/PKL files byte-for-byte.
