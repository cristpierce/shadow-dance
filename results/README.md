# Results contract

Generated reference QA may be committed here. Policy metrics must come from an actual
current-session command and preserve its raw log/config before any summary is written.

Expected final layout:

```text
reference-validation.json
raw/stock-heldout/{eval.log,.hydra/...}
raw/finetuned-heldout/{eval.log,.hydra/...}
raw/stock-retention/{eval.log,.hydra/...}
raw/finetuned-retention/{eval.log,.hydra/...}
raw/stock-test/{eval.log,.hydra/...}
raw/selected-test/{eval.log,.hydra/...}
summaries/*.json
selection.json
final-comparison.json
```

Never infer a success rate from a beauty render, and never report a train-split metric
as validation or test performance. The `heldout` directory is selection-validation;
the `test` directory must remain unevaluated until the selected checkpoint is frozen.
Final reporting aggregates the same four test motions at seeds 101, 202, and 303 for
both stock and selected policies (12 trials each).
