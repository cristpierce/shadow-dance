# BONES-SEED corpus analysis

**Date:** 2026-08-03 (reviewed and corrected 2026-08-13)
**Dataset:** [`bones-studio/seed`](https://huggingface.co/datasets/bones-studio/seed) — v004 metadata
**Why this exists:** the originality claim in [`specs/shadow-dance.md`](../specs/shadow-dance.md) §1
asserts that stock SONIC "has generic dance in its training distribution, but not
lead-frame partner dance, and not a dip." BONES-SEED is that training distribution.
This note tests the assertion instead of restating it.

---

## 1. What the corpus contains

142,220 motions — 71,132 originals plus 71,088 mirrored duplicates (`is_mirror`).
~288 hours at 120 fps, 522 actors.

| Package | Motions |
|---|---:|
| Locomotion | 74,488 |
| Communication | 21,493 |
| Interactions | 14,643 |
| **Dances** | **11,006** |
| Gaming | 8,700 |
| Everyday | 5,816 |
| Sport | 3,993 |
| Other | 2,081 |

Movement types (top): walking 20,222 · jogging 16,437 · gesture 15,862 ·
action 13,507 · dancing 12,593 · jumping 11,475 · turning 3,472 ·
walking+turning 2,236 · standing idle 3,190.

**The base model has seen a lot of dance.** 11,006 motions is not a rounding error.
The originality claim cannot rest on "SONIC doesn't know how to dance" — it plainly does.

## 2. What it does *not* contain

Searched every descriptive field (`content_natural_desc_1..4`,
`content_technical_description`, `content_short_description*`, `move_name`) across
**all 142,220 motions**:

| Term | Hits |
|---|---:|
| waltz | **0** |
| tango | **0** |
| ballroom | **0** |
| foxtrot | **0** |
| partner dance | **0** |
| lead and follow | **0** |
| closed hold | **0** |
| dance frame | **0** |
| hold hands | **0** |

Apparent near-misses, checked by inspecting the matched text rather than the count:

- **"two-step"** → *"a lively two-step latin dance sequence with hip switches"*.
  A Latin step pattern, not Texas two-step.
- **"swing"** → *"swinging them"*, *"swinging the arms rhythmically"*.
  Arm motion, not swing dance.
- **"dip"** → 32 search results, mostly box/object dips plus a misleadingly named
  `dance_dip_001` family. That family contains four original takes (actors A464–A467)
  and four mirrored variants. The public descriptions/temporal labels describe arm
  swings or an “air spank”; A464/A465 also jump and bend into a low wide stance. They do
  not describe a couple/partner dip.

The dance styles that *are* present: lasso dancing, Egyptian, kozak, krakowiak,
latino (salsa / mambo / jive), vogue. All solo or folk idiom. None of it is
couple-frame dance.

**Conclusion:** the corpus contains substantial solo and folk dance and no indexed
partner-dance vocabulary in the searched descriptive fields. This supports a hypothesis,
not proof of policy novelty. Metadata can omit semantics, and a generalist policy can
generalize beyond named training examples. The submission must demonstrate originality
geometrically and behaviorally: compare the target with its nearest corpus motions, show
the exact stock-policy failure, and then show fine-tuned success.

## 3. `dance_dip_001` follow-up

The public search API exposed eight records: four source performances and their mirrors,
not one record as the first analysis stated. Their text and temporal segments do not
encode a partner dip, but the actual G1 trajectories should still be visualized before
making a nearest-motion claim. Names alone are not reliable evidence of motion geometry.

## 4. Implications for the fine-tune mix

§5 of the original spec calls for ~25% custom / ~75% BONES-SEED, “sampled to include
locomotion,” to prevent catastrophic forgetting of the WBT-Bench fundamentals. That is
an unvalidated starting hypothesis, not a known good ratio. The current SONIC loader
starts with approximately equal sequence exposure and uses adaptive sampling to focus on
failing segments, so file counts and failure patterns both affect the realized mix.

For the deadline plan, prefer owned hero motions plus owned stand/walk/turn retention
motions. This avoids a gated dependency and simplifies provenance and redistribution,
subject to the terms of the retargeting tool used. Use BONES-SEED only if eligibility is
established and the restricted inputs can be handled reproducibly without
redistribution.

If eligibility is confirmed and BONES-SEED is used, the metadata makes locomotion
selection precise rather than arbitrary. Locomotion-package originals alone number
**37,260**, broken down as walking 7,980 · jogging 7,853 · jumping 5,418 · turning
1,415 · walking+turning 964 · standing idle 1,367.

Useful selection columns: `package`, `category`, `content_type_of_movement`,
`content_body_position`, `is_mirror`, `move_g1_path`.

Mirrors should probably be excluded from the buffer by default (`is_mirror == False`)
and reintroduced only as deliberate augmentation — otherwise half the "diversity" in
the rehearsal set is the same motions reflected.

## 5. Licensing gate

The current [BONES-SEED license](https://huggingface.co/datasets/bones-studio/seed/blob/main/LICENSE.md)
limits use to qualifying academic users and qualifying startups (defined there as
entities below $1 million annual gross revenue), prohibits redistribution of the raw
dataset, and requires specific attribution for public models and software. An individual
entrant should not assume eligibility merely because the challenge links the dataset.
Confirm status before accepting/downloading it, do not put raw BONES motions in the
submission dataset, and include the required “Motion Data by Bones Studio” credit if it
is used.

## 6. Reproducing the metadata analysis

Requires accepting the dataset's gate (it asks you to share contact information and
accept the BONES-SEED licence), then `huggingface-cli login`.

```python
import pandas as pd
from huggingface_hub import hf_hub_download

p = hf_hub_download(
    repo_id="bones-studio/seed", repo_type="dataset",
    filename="metadata/seed_metadata_v004.parquet",
)
df = pd.read_parquet(p)          # 142,220 rows, no motion data downloaded

TEXT = ["content_natural_desc_1", "content_natural_desc_2", "content_natural_desc_3",
        "content_natural_desc_4", "content_technical_description",
        "content_short_description", "content_short_description_2", "move_name"]

# NOTE: select text columns by NAME. Filtering on `dtype == object` silently selects
# nothing under pandas 3.x (dedicated string dtype) and every search returns 0 hits.
blob = df[TEXT].astype(str).apply(lambda s: s.str.lower()).agg(" ".join, axis=1)

for term in ["waltz", "tango", "ballroom", "partner dance", "closed hold"]:
    print(term, int(blob.str.contains(term, regex=False).sum()))
```

Sanity check any such search against a term you *know* is common — `"walk"` should
return ~30,000. If it returns 0, the column selection is broken, not the corpus.

## 7. Download notes

The repo layout is three tarballs plus metadata, **not** per-motion files — so there
is no way to download a subset selectively. Filter after extraction.

| File | Size |
|---|---:|
| `g1.tar.gz` — Unitree G1 MuJoCo-compatible CSVs | 23.50 GB |
| `soma_proportional.tar.gz` | 45.47 GB |
| `soma_uniform.tar.gz` | 45.19 GB |
| `metadata/seed_metadata_v004.parquet` | ~4 MB |

Only `g1.tar.gz` is needed for a `sonic_release` fine-tune that uses G1 reference
motions. The SOMA archives are needed only when actually adding SOMA skeleton data, for
example with `sonic_bones_seed`; they add about 90 GB and unnecessary deadline risk.

Paths inside resolve as `g1/csv/{take_date}/{move_name}.csv`, matching the
`--input` that `gear_sonic/data_process/convert_soma_csv_to_motion_lib.py` expects.
