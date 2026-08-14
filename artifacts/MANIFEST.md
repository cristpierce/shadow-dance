# Model artifact manifest

No fine-tuned model artifact exists yet. After checkpoint selection this directory will
contain the generated ONNX validation report and checksums, while large `.pt` and
`.onnx` files live in versioned Hugging Face model storage.

Required release set:

- selected checkpoint and its original Hydra `config.yaml`;
- `novelty.json` bound to the stock validation summary and preregistered thresholds;
- `selection.json` with every validation/retention summary hash and the selected
  checkpoint's byte size and SHA-256;
- `final-comparison.json` bound to the frozen selection plus all 12 stock and 12
  selected final-test trials;
- combined G1 ONNX policy (the `_g1.onnx` portal nominee);
- combined SMPL and teleop ONNX policies;
- shared encoder and G1 decoder ONNX files (one coherent five-graph export prefix);
- `model_config.yaml` / observation contract;
- `onnx-report.json` with graph checker, I/O, finite probe where possible, sizes, and
  SHA-256;
- NVIDIA Open Model License and attribution; and
- immutable public URLs tested from a clean download.

The public model repository also carries compact summaries and raw `metrics_eval.json`
files. Kinematic reference playback is not a model artifact or policy result.

## Pinned base model

- Hugging Face repo: `nvidia/GEAR-SONIC`
- revision: `9c0ff22b4ffec27c5392e8e284eb2f2df7a5b4e2`
- file: `sonic_release/last.pt`
- size: `469418283` bytes
- SHA-256: `e6bdab3f64a39336b3d41877d4f497d05f58af275f288ec0e6746c283ded8909`

These values come from the public Hugging Face file metadata and must be checked after
download before training. The model is governed by the NVIDIA Open Model License.

## Pinned cloud runtime

- image: `npa-sonic:0.1.2`
- L40S digest: `sha256:bdf81f5b7f1c879ac920df53588a15129b2ac71d9492e8c2fc34ce636a5373fb`
- embedded SONIC commit: `0a87181c9106d0e49293400714b157676e0ec664`
- NPA operator commit: `1e8acb921aa953c1e2ce018bcbc6417611768a16`
