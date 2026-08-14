# Data layout

`generated/csv/` contains the 22 team-authored source trajectories in an inspectable
degree/centimetre schema. `manifests/shadow-dip-v1.json` is authoritative for split,
provenance, phase timing, parameters, IK residuals, and hashes. `splits/` is a simple
loader-friendly index.

SONIC-ready PKLs are generated into `generated/train/` and `generated/heldout/`; Git
ignores them because they are binary/reproducible. Run:

```powershell
shadow-generate --sonic-root C:\path\to\GR00T-WholeBodyControl
shadow-validate --sonic-root C:\path\to\GR00T-WholeBodyControl
```

The eventual Hugging Face dataset revision will contain the same PKLs plus this source
and metadata. Compare its checksums to the manifest before training.
