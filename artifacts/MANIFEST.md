# Model artifact manifest

No fine-tuned model artifact exists yet. After checkpoint selection this directory will
contain the generated ONNX validation report and checksums, while large `.pt` and
`.onnx` files live in versioned Hugging Face model storage.

Required release set:

- selected checkpoint and its original Hydra `config.yaml`;
- combined G1 ONNX policy (the portal nominee);
- encoder and decoder ONNX files;
- `model_config.yaml` / observation contract;
- `onnx-report.json` with graph checker, I/O, finite probe where possible, sizes, and
  SHA-256;
- NVIDIA Open Model License and attribution; and
- immutable public URLs tested from a clean download.
