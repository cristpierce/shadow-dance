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
summary.json
summary.csv
```

Never infer a success rate from a beauty render, and never report a train-split metric
as held-out performance.
