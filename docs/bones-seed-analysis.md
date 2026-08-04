# BONES-SEED corpus analysis

**Date:** 2026-08-03
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
- **"dip"** → matches only the filename `dance_dip_001__A464`, whose own
  description is *"spanks the air"*.

The dance styles that *are* present: lasso dancing, Egyptian, kozak, krakowiak,
latino (salsa / mambo / jive), vogue. All solo or folk idiom. None of it is
couple-frame dance.

**Conclusion:** the corpus contains substantial solo and folk dance and **no partner-dance
vocabulary whatsoever**. The claim in §1 holds — the novelty is not "dance", it is
*lead frame held for an absent partner*, and the deep asymmetric dip.

## 3. Open item

There is a motion family literally named `dance_dip_001`. Its description
("spanks the air") suggests it is not a partner dip, but this should be **inspected
visually in MuJoCo** once the G1 CSVs are extracted, since it is the single piece of
data that could complicate the hero-move claim. Do not assume; look at it.

## 4. Implications for the fine-tune mix

§5 of the spec calls for ~25% custom / ~75% BONES-SEED, "sampled to include
locomotion", to prevent catastrophic forgetting of the WBT-Bench fundamentals.

The metadata makes that selection precise rather than arbitrary. Locomotion-package
originals alone number **37,260**, broken down as walking 7,980 · jogging 7,853 ·
jumping 5,418 · turning 1,415 · walking+turning 964 · standing idle 1,367.

Useful selection columns: `package`, `category`, `content_type_of_movement`,
`content_body_position`, `is_mirror`, `move_g1_path`.

Mirrors should probably be excluded from the buffer by default (`is_mirror == False`)
and reintroduced only as deliberate augmentation — otherwise half the "diversity" in
the rehearsal set is the same motions reflected.

## 5. Reproducing this

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

## 6. Download notes

The repo layout is three tarballs plus metadata, **not** per-motion files — so there
is no way to download a subset selectively. Filter after extraction.

| File | Size |
|---|---:|
| `g1.tar.gz` — Unitree G1 MuJoCo-compatible CSVs | 23.50 GB |
| `soma_proportional.tar.gz` | 45.47 GB |
| `soma_uniform.tar.gz` | 45.19 GB |
| `metadata/seed_metadata_v004.parquet` | ~4 MB |

Only `g1.tar.gz` is needed. The SOMA archives serve the BVH ingestion route, which
§3 of the spec rules out (its encoder needs 64+ GPUs). Skipping them saves 90 GB.

Paths inside resolve as `g1/csv/{take_date}/{move_name}.csv`, matching the
`--input` that `gear_sonic/data_process/convert_soma_csv_to_motion_lib.py` expects.
