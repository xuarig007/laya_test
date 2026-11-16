# layabench — multilingual support-ticket triage benchmark for **Laya**

> Use case and benchmark *imagined* from the model card of
> [`convaiinnovations/laya`](https://huggingface.co/convaiinnovations/laya) and its
> [documentation](https://nandhakishorm.github.io/laya/). Everything here is runnable and
> reproducible: a labelled dataset, compared backends, metrics, reports.
>
> **Français :** see [`README.fr.md`](README.fr.md).

**Repo:** https://github.com/xuarig007/laya_test

Laya is a **decision engine** (*System 1*, non-autoregressive): you give it a *state* (text, email,
ticket or JSON) and **typed questions**, and it returns typed answers with probabilities in **a
single forward pass (~33 ms on GPU)**, across 100+ languages. It never generates text — nothing to
parse, nothing to hallucinate — and a `Router` picks the right checkpoint (`english` /
`multilingual`) on its own from the detected language.

---

## 1. The imagined use case: a multilingual triage gateway

**A triage gateway at the support front door (smart ingress).**
An organisation receives tickets in several languages (EN / FR / DE / ES / HI…). Before any
processing, each ticket is turned into **four typed decisions**, in a single forward pass:

| question (`id`) | Laya type | output | downstream role |
|---|---|---|---|
| `department` | `choice` | `billing` \| `technical` \| `account` | route to the right queue |
| `urgency` | `score` | `0` \| `1` \| `2` | prioritisation / SLA |
| `churn_risk` | `noul` | probability of "yes" | retention alert |
| `refund_requested` | `noul` | probability of "yes" | trigger the refund policy |

```
ticket ──▶ laya.Router.predict(state, QUESTION_POLICY) ──▶ { department, urgency, churn_risk, refund_requested }
              │                                                    │
              └─ route by language (english | multilingual)         └─ confidence per answer ─▶ auto-pass if high
```

**Why Laya rather than a generative LLM here?** It's a **discrete decision** (no text to produce),
the schema is **fixed** (nothing to repair on the JSON side), inference is **short and predictable**
(one forward pass, no decoding loop), **multilingual routing is built in**, and everything runs
**locally, on CPU** — customer data never leaves the perimeter.

The question policy is defined **once** in
[`layabench/schema.py`](layabench/schema.py) and injected into the dataset by the generator, so the
dataset and the harness can never drift apart.

---

## 2. The imagined benchmark

### Hypotheses under test

- **H1.** Is **zero-shot** Laya usable to triage tickets in several languages?
- **H2.** Is its **confidence** reliable enough for an automatic pass ("auto-resolution" when
  confidence is high)? → `ece`, `brier`, `aurc`, `selective_accuracy@*`.
- **H3.** Does the documented `noul` workaround (re-asking the boolean question as a `choice` with
  neutral keys) actually **improve** results *on our data*?

### Dataset

33 hand-labelled tickets, split by language: **EN 10, FR 8, DE 7, ES 7, HI 1** (the Hindi ticket is
provided as a **JSON document**, to show that the state can be something other than a string).
132 decisions in total.

The format is `laya-evals`: one JSON line per case, with `state`, `questions`, `expected` (a label
for `choice`, a number for `score`, a boolean for `noul`), plus `language` and `tags` for slicing.

- editable source: `data/tickets.source.jsonl`
- canonical dataset (generated): `data/tickets.eval.jsonl` — via `python tools/build_dataset.py`

### Backends compared

| backend | weights | description |
|---|---|---|
| `laya` | yes | the real `laya.Router` (automatic routing by language) |
| `heuristic` | no | a **keyword** engine — the fallback a team hand-writes (domain baseline) |
| `majority` | no | always the majority class (Laya's own reference line) |
| `random` | no | uniform random (Laya's own reference line) |

### Metrics (identical to `laya.evals`)

`choice_accuracy`, `noul_accuracy`, `score_mae`, `score_within_0.5`, `mean_confidence`,
`ece` (15 bins), `brier`, `aurc`, `selective_accuracy@50` / `@80`, `latency_p50_ms` /
`latency_p95_ms`, `cost_per_decision_p50_ms` — plus **slices** by `language`, by `qid` and by
`tag`. The maths lives in [`layabench/metrics.py`](layabench/metrics.py) and uses numpy only (like
the Laya docs), so it runs **without weights**.

---

## 3. Measured results

Machine: **CPU** only, `torch 2.15.0+cpu`, `laya 0.4.31`, 33 tickets / 132 decisions, one warmup
forward pass so model loading isn't charged to the latency.

### Overview

| backend | choice_acc | noul_acc | score_mae | ece ↓ | brier ↓ | aurc ↓ | sel@50 | p50 (ms) ↓ | p95 (ms) ↓ |
|---|---|---|---|---|---|---|---|---|---|
| `heuristic` | 0.939 | 0.970 | 0.545 | 0.127 | 0.043 | 0.021 | 0.979 | 0.02 | 0.04 |
| `heuristic` *[noul→choice]* | 0.939 | 0.970 | 0.545 | 0.256 | 0.109 | 0.022 | 0.979 | 0.02 | 0.03 |
| **`laya` (CPU)** | **0.909** | **0.879** | **0.567** | **0.070** | **0.075** | **0.032** | **0.960** | **164.7** | **498.7** |
| `laya` *[noul→choice]* | 0.909 | 0.848 | 0.567 | 0.079 | 0.095 | 0.040 | 0.980 | 160.2 | 493.4 |
| `majority` | 0.485 | 0.773 | 0.455 | 0.000 | 0.200 | 0.254 | 0.773 | 0.001 | 0.006 |
| `random` | 0.303 | 0.500 | 0.848 | 0.066 | 0.250 | 0.566 | 0.434 | 0.003 | 0.011 |

Full reports are in `results/*.json` (raw data) and `results/*.md` (summary).

### Per language — `laya` backend

| language | choice_acc | noul_acc | score_mae | ece | decisions |
|---|---|---|---|---|---|
| `de` | 0.714 | 0.929 | 0.469 | 0.141 | 28 |
| `en` | 1.000 | 0.850 | 0.607 | 0.134 | 40 |
| `es` | 1.000 | 0.857 | 0.625 | 0.106 | 28 |
| `fr` | 0.875 | 0.875 | 0.595 | 0.067 | 32 |
| `hi` | 1.000 | 1.000 | 0.225 | 0.012 | 4 |

### Per question — `laya` backend

| question | type | metric | value |
|---|---|---|---|
| `department` | choice | `choice_accuracy` | 0.909 |
| `urgency` | score | `score_mae` | 0.567 |
| `churn_risk` | noul | `noul_accuracy` | 0.818 |
| `refund_requested` | noul | `noul_accuracy` | 0.939 |

### Automatic routing (no forward pass)

```
I was charged twice for my March subscription…            english       English Latin text
J'ai été facturé deux fois pour mon abonnement de mars…   multilingual  Latin script but language looks like 'fr', not English
Mir wurde der Betrag zweimal abgebucht…                   multilingual  Latin script but language looks like 'de', not English
Me cobraron dos veces este mes…                           multilingual  Latin script but language looks like 'es', not English
{"body": "मुझसे दो बार शुल्क लिया गया…"}                    multilingual  non-Latin script (devanagari, 82% of letters)…
Quero cancelar                                            multilingual  Latin script, language not identified … using default
```

The `Router` sends English to `english`, everything else to `multilingual`, and falls back to
`default` when a very short Latin text carries no language information — exactly the behaviour the
docs describe. Reproducible with `python tools/routing_demo.py`.

---

## 4. What the benchmark shows

- **H1 — yes, but it's a base to specialise.** Zero-shot, on a very specific domain, Laya reaches
  `choice_accuracy` 0.909 and `noul_accuracy` 0.879 with no training at all: well above `majority`
  (0.485 / 0.773) and `random` (0.303 / 0.500). It **nearly matches** the keyword engine we wrote by
  hand *for this exact domain* — an unfair advantage, since the `heuristic` baseline is literally
  cut to these tickets, while Laya only sees public weights. The model card is explicit: the base
  checkpoints are near chance on typed-decisions zero-shot and **serve as a base to fine-tune** —
  consistent with what we observe.
- **H2 — the confidence is usable.** `ece` 0.070, `aurc` 0.032 and above all
  `selective_accuracy@50` 0.960: accepting only the most confident half lifts accuracy to 96%.
  That's the signal that matters for an automatic pass — the docs recommend gating on `confidence`
  (not on `action.act_probability`, which carries no usable signal).
- **H3 — the `noul` workaround doesn't help here.** Re-asking `churn_risk` / `refund_requested` as a
  `choice` with neutral keys *lowers* `noul_accuracy` from 0.879 to 0.848 and `ece` from 0.070 to
  0.079. The documented problem (a `noul` that "follows its labels") **does not materialise** on
  this data — hence the value of measuring it rather than applying it blindly.
- **The `score` primitive is the weakest.** `score_mae` 0.567 and `score_within_0.5` only 0.455:
  urgency is the worst-ranked decision, which the model card already warns about (`score` = weakest
  primitive). A production design would use a coarse `choice` first (low/medium/high) or a
  re-trained head.
- **Multilingual in a single artefact.** One `Router` covers EN/FR/DE/ES/HI with transparent routing;
  the measured weak spot is German `choice_accuracy` (0.714).

---

## 5. Reproduce

```bash
# in /appli/laya_test
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python --index-url https://download.pytorch.org/whl/cpu torch
uv pip install --python .venv/bin/python laya          # the Laya engine (0.4.31)

# 1) build and check the dataset (no weights)
.venv/bin/python tools/build_dataset.py
.venv/bin/python -m layabench validate data/tickets.eval.jsonl

# 2) weight-free baselines
for b in heuristic majority random; do
  .venv/bin/python -m layabench run --data data/tickets.eval.jsonl --backend $b \
      --json results/$b.json --markdown results/$b.md
done

# 3) the real engine (downloads the checkpoints on first call), then the noul→choice variant
.venv/bin/python -m layabench run --data data/tickets.eval.jsonl --backend laya \
    --device cpu --warmup --json results/laya_cpu.json --markdown results/laya_cpu.md
.venv/bin/python -m layabench run --data data/tickets.eval.jsonl --backend laya \
    --device cpu --warmup --noul-as-choice \
    --json results/laya_cpu_noulchoice.json --markdown results/laya_cpu_noulchoice.md

# 4) compare a candidate against a baseline (CI gate: non-zero exit on regression)
.venv/bin/python -m layabench compare results/laya_cpu.json --baseline results/heuristic.json

# bonus: routing decisions, with no forward pass
.venv/bin/python tools/routing_demo.py
```

For a GPU, replace `--index-url .../cpu` with the CUDA build and pass `--device cuda` (the test
machine has an RTX 4070; the figures above are CPU figures).

---

## 6. Layout

```
laya_test/
├── README.md                      # this file (English)
├── README.fr.md                   # French version
├── pyproject.toml                 # `layabench` package (numpy required, laya as an extra)
├── layabench/
│   ├── schema.py                  # the question policy + the eval-set loader
│   ├── metrics.py                 # metrics (mirror of laya.evals, numpy only)
│   ├── backends.py                # laya | heuristic | majority | random
│   ├── harness.py                 # runs a dataset against a backend
│   ├── report.py                  # Markdown rendering + report diff
│   └── cli.py                     # `python -m layabench run|validate|compare`
├── data/
│   ├── tickets.source.jsonl          # editable source (33 hand-written tickets)
│   ├── tickets.eval.jsonl            # canonical laya-evals dataset (33 lines)
│   ├── tickets100.*                  # 33 written + 67 generated (100 lines)
│   ├── tickets300.*                  # 33 written + 300 generated / 60 templates (333 lines)
│   ├── train.jsonl / test.jsonl      # split 33 (23/10)
│   ├── train100.jsonl / test100.jsonl    # split 100 (79/21, stratified)
│   ├── train300.jsonl / test300.jsonl    # split 300 by TEMPLATE (258/75, unseen phrasings)
│   └── train300-small.jsonl          # 65-ticket subset (data curve)
├── tools/
│   ├── build_dataset.py              # source → canonical dataset (--source / --out)
│   ├── gen_dataset.py                # 33 written + 67 generated = 100 tickets
│   ├── gen_dataset_big.py            # template variant (300 tickets, `tpl`)
│   ├── make_split.py                 # deterministic split (explicit | stratified | template)
│   ├── finetune.sh                   # fine-tune via the laya-train CLI (33 tickets)
│   ├── train_laya.py                 # fine-tune via the Python API (GPU, calib_frac, loss)
│   ├── make_onepager.py              # generates laya_onepager.pdf (reportlab, 1 page)
│   ├── make_table_images.py          # renders the article tables as PNGs + writes the *.medium.md import variants
│   ├── serve_model.py                # small local server + UI (/predict /guide /models /onepager.pdf)
│   ├── serve.sh                      # start / restart the test server (port 9999 by default)
│   ├── tester.html                   # web page: without FT / with FT comparison, category guide
│   └── routing_demo.py               # prints the Router's decisions
├── checkpoints/                      # t300-softce kept (the most efficient); others regenerable
├── blog/                             # Medium article: medium-laya-en/fr.md + assets/ + PUBLISHING.md
├── laya_onepager.pdf                 # one-pager summary (presentation + results)
└── results/                          # generated reports (JSON + Markdown)
```

> The harness's `agent` backend scores **one** checkpoint (`laya.load` + `agent.predict`), which is
> how a fine-tuned model is benchmarked next to the public checkpoints: see section 8.

---

## 7. Honest limits

- **Tiny dataset (33 tickets).** Enough to demonstrate the harness and the trends, not for a
  statistical conclusion. Replace it with a real labelled set (the Laya docs show how to wire up a
  `baseline.json` and a CI gate).
- **The `heuristic` baseline is tailored to this domain** (keywords chosen for these tickets): it's an
  optimistic ceiling for hand-written rules, not a "fair" competitor. The useful exercise is to
  **fine-tune Laya** on the same split, then replay the benchmark.
- **CPU latencies only.** ~165 ms/ticket on CPU (p95 ~0.5 s) against the ~33 ms claimed on GPU; these
  are the harness's end-to-end times (tokenisation included).
- **The base checkpoints are over-confident on their own benchmarks** (the card reports ECE
  0.466 → 0.081 after refitting a temperature). Our ECE of 0.070 is measured on *this* small set, not
  a guarantee: **refit the temperature on your own data** before trusting the probabilities.
- **`noul` can follow its labels** instead of the state (documented issue); our H3 shows it is not
  systematic — check it case by case, as we did.
- **High-cardinality choice.** Beyond ~20 options, accuracy collapses if the per-option prompt budget
  is too small; our `department` has only 3 options, which masks this limit.

---

## 8. The logical next step: fine-tuning on our labels

Section 4 said "it's a base to fine-tune". So we did, with the official `laya-train` API (the Python
equivalent is `laya.train.finetune`).

### Protocol

- **Deterministic, documented split** (`tools/make_split.py`): **23 train / 10 test**. The test set is
  chosen (not sampled) to cover the 5 languages, the 3 departments, and to keep **4 of the 7 churn
  threats** — otherwise the weak spot couldn't be measured.
- **Base `multilingual`** (mmBERT), `--loss soft-ce --label-smoothing 0.1`, on **CPU**.
- **Two variants**: **frozen** encoder (heads only, fast) and **full**.

### Results — on the 10 held-out tickets

| run | choice_acc | noul_acc | score_mae ↓ | ece ↓ | aurc ↓ | sel@50 |
|---|---|---|---|---|---|---|
| before — `Router` (prod) | 0.800 | 0.800 | 0.508 | 0.118 | 0.100 | 0.867 |
| before — base `multilingual` | 0.800 | 0.800 | 0.573 | 0.156 | 0.070 | 0.933 |
| after — fine-tune **frozen** | 0.900 | 0.800 | 0.550 | 0.123 | 0.067 | 0.933 |
| after — fine-tune **full** | **1.000** | **0.900** | **0.336** | **0.120** | **0.021** | **1.000** |

Per question, the sensitive `churn_risk`: **0.60 → 0.60 → 0.80** (base → frozen → full).

### What fine-tuning shows

- **Full fine-tuning improves everything**, cleanly: `choice` 0.80→1.00, `urgency` MAE 0.573→0.336,
  `ece` 0.156→0.121, `aurc` 0.070→**0.021**, `selective@50` 0.933→1.000. The docs' thesis holds on our
  data: *fine-tuning is where most of the value is*.
- **Freezing the encoder is not enough.** Training the heads only: +0.10 on `choice` but `noul`
  unchanged. The useful specialisation goes through the **encoder**.
- **`churn` stays the weak spot** (0.60→0.80): with **3 positive churn examples** in training, even a
  full fine-tune doesn't fix negation. The lesson is clear — it's solved with **more labelled data**,
  not more epochs.
- **Calibration needs a real dedicated set.** With 33 tickets, the calibration slice holds fewer than
  10 items per type → `laya-train` **does not fit** the temperatures (they stay at 1.0, with an
  explicit warning). ECE still drops, because the head becomes intrinsically less over-confident.

### Reproducing the fine-tune

```bash
# split + fine-tune (frozen encoder) + Laya's own before/after evaluation
bash tools/finetune.sh

# full fine-tune variant
FREEZE="" bash tools/finetune.sh

# score the checkpoint with our harness, then compare against the base
.venv/bin/python -m layabench run --data data/test.jsonl --backend agent \
    --checkpoint checkpoints/tickets-ft-full --device cpu --warmup \
    --json results/after_ft_full_test.json --markdown results/after_ft_full_test.md
.venv/bin/python -m layabench compare results/after_ft_full_test.json \
    --baseline results/before_multilingual_test.json
```

The resulting checkpoint loads like any other: `laya.load("checkpoints/tickets-ft-full")`.

---

## 9. Scaling up: 100 tickets, full fine-tune **on GPU**

A follow-up to section 8: the dataset moves to **100 tickets** and training (full) runs **on GPU** —
RTX 4070 12 GB, `torch 2.15.0+cu132`.

### What changes

- **100 tickets**: the 33 hand-written ones **+ 67 generated** by `tools/gen_dataset.py`
  (per-language phrase banks; labels derived from the assembled components).
  *Acknowledged limit: those 67 are synthetic and more repetitive than the 33; the set stays a
  demonstration set, not a public benchmark.*
- **Stratified split** (`--strategy stratified`): **79 train / 21 test** (~20%, all languages).
- `tools/train_laya.py` (Python API `laya.train.finetune`) with **`calib_frac=0.25`**: the calibration
  slice becomes big enough (79 items) to **actually fit** the temperatures (T ≈ 0.93 / 1.11 / 1.10).
- **Full fine-tune** (encoder not frozen), 15 epochs, `--micro-batch 16`.

### Results — 21 held-out tickets (84 decisions)

| metric | base `multilingual` | fine-tuned (100, GPU) | delta |
|---|---|---|---|
| `choice_accuracy` | 0.7143 | **0.9048** | **+0.1905** |
| `noul_accuracy` | 0.8333 | **0.9524** | **+0.1190** |
| `score_mae` ↓ | 0.8234 | **0.3326** | **-0.4908** |
| `score_within_0.5` | 0.1905 | **0.7619** | **+0.5714** |
| `ece` ↓ | 0.1335 | **0.1001** | -0.0334 |
| `brier` ↓ | 0.1351 | **0.0316** | -0.1035 |
| `aurc` ↓ | 0.0595 | **0.0028** | -0.0567 |
| `selective_accuracy@50` | 0.9688 | **1.000** | +0.0312 |
| `selective_accuracy@80` | 0.8824 | **1.000** | +0.1176 |
| `latency_p50_ms` ↓ | 23.5 | **18.3** | -5.3 |

Per question:

| question | base | fine-tuned |
|---|---|---|
| `churn_risk` (noul) | 0.714 | **1.000** |
| `department` (choice) | 0.714 | **0.905** |
| `refund_requested` (noul) | 0.952 | 0.905 |
| `urgency` (MAE) | 0.823 | **0.333** |

### What it shows

- **Scaling fixes the weak spot**: `churn_risk` goes from **0.714 to 1.000**. That's exactly the
  signal the 33-ticket run (section 8) could not repair — the conclusion of section 8 ("it's solved
  with more data") is confirmed.
- **Improvement everywhere**: `choice` +0.19, `urgency` MAE −0.49, `aurc` 0.060→**0.003**,
  `selective@80` 0.88→**1.00**. Only `refund` slips very slightly (0.952→0.905) — noise on 21 tickets.
- **Calibration finally fits**, because `calib_frac=0.25` provides enough items per type (unlike the 33
  tickets, where the temperatures stayed pinned at 1.0).
- **GPU latency ~18–24 ms/ticket**, consistent with the ~33 ms claimed (versus ~165 ms on CPU).

### Reproduce

```bash
# 100 tickets: 33 written + 67 generated -> dataset -> stratified split
.venv/bin/python tools/gen_dataset.py
.venv/bin/python tools/build_dataset.py --source data/tickets100.source.jsonl --out data/tickets100.eval.jsonl
.venv/bin/python tools/make_split.py --data data/tickets100.eval.jsonl --strategy stratified \
    --holdout-frac 0.2 --train-out data/train100.jsonl --test-out data/test100.jsonl

# FULL fine-tune on GPU (encoder not frozen, calib_frac=0.25)
.venv/bin/python tools/train_laya.py --data data/train100.jsonl --eval data/test100.jsonl \
    --out checkpoints/tickets100-ft --base multilingual --device cuda \
    --epochs 15 --micro-batch 16 --grad-accum 1 --calib-frac 0.25

# evaluate "before" (base) then "after" (fine-tuned), on the same test
.venv/bin/python -m layabench run --data data/test100.jsonl --backend agent \
    --checkpoint convaiinnovations/laya --subfolder multilingual --device cuda --warmup \
    --json results/before100_multilingual_test.json
.venv/bin/python -m layabench run --data data/test100.jsonl --backend agent \
    --checkpoint checkpoints/tickets100-ft --device cuda --warmup \
    --json results/after100_ft_test.json
.venv/bin/python -m layabench compare results/after100_ft_test.json \
    --baseline results/before100_multilingual_test.json
```

---

## 10. Study: generalisation on unseen phrasings, `soft-ce` vs `rlcd`, data curve

Goal: answer two questions an engineer actually asks — **which loss function?** and **how much data?** —
while making sure the gain is **generalisation**, not memorisation.

### Protocol

- **333 tickets** = 33 hand-written + 300 generated, split into **60 templates**
  (`tools/gen_dataset_big.py`). Each template is one realisation of a (language, department).
- **Split by template** (`make_split.py --strategy template`): one **whole realisation** per (language,
  department) is held out. The test set therefore uses **phrasings never seen during training** →
  258 train / 75 test.
- **3 GPU runs** identical except for the variable under study: `soft-ce` (300), `rlcd` (300),
  `soft-ce` on 65 tickets. Same test300 for all.
- Evaluation with **our harness** (300 decisions) alongside Laya's own report.

### Results (our harness)

| run | choice_acc | noul_acc | score_mae ↓ | ece ↓ | brier ↓ | aurc ↓ | sel@80 |
|---|---|---|---|---|---|---|---|
| base `multilingual` | 0.653 | 0.753 | 0.672 | 0.222 | 0.237 | 0.149 | 0.750 |
| FT **`soft-ce` (300)** | **0.933** | 1.000 | 0.098 | **0.067** | 0.031 | **0.004** | 0.989 |
| FT `rlcd` (300) | 0.867 | 1.000 | **0.075** | 0.092 | 0.046 | 0.008 | **0.994** |
| FT `soft-ce` (65) | 0.720 | 1.000 | 0.126 | 0.072 | 0.057 | 0.009 | 0.994 |

Per question:

| run | `churn_risk` | `department` | `refund_requested` | `urgency` (MAE) |
|---|---|---|---|---|
| base | 0.600 | 0.653 | 0.907 | 0.672 |
| FT `soft-ce` (300) | 1.000 | **0.933** | 1.000 | 0.098 |
| FT `rlcd` (300) | 1.000 | 0.867 | 1.000 | **0.075** |
| FT `soft-ce` (65) | 1.000 | 0.720 | 1.000 | 0.126 |

### Laya's own report (same runs)

| run | Accuracy | ECE | Brier top-1 |
|---|---|---|---|
| `soft-ce` (300) | 0.6367 → **0.9800** | 0.2111 → 0.0686 | 0.2441 → 0.0295 |
| `rlcd` (300) | 0.6367 → 0.9667 | 0.2111 → **0.0486** | 0.2441 → 0.0362 |
| `soft-ce` (65) | 0.6367 → 0.9233 | 0.2111 → 0.0623 | 0.2441 → 0.0507 |

### Conclusions

- **Fine-tuning really generalises.** On **unseen phrasings**, `soft-ce` lifts `choice` from 0.653 to
  **0.933**, `noul` to **1.000**, `urgency` MAE from 0.672 to **0.098** and `aurc` from 0.149 to
  **0.004**. That's not memorisation: the test set never saw the phrasing.
- **`soft-ce` vs `rlcd`**: `soft-ce` wins on the **categorical** (`department` 0.933 vs 0.867) and on
  **calibration** (ECE 0.067 vs 0.092); `rlcd` wins slightly on the **ordinal** (`urgency` MAE 0.075
  vs 0.098) and `sel@80`. Consistent with the Laya docs (0.790 vs 0.7715 on typed-decisions) →
  **`soft-ce` by default**, `rlcd` if fine ordering matters most.
- **Data curve**: at 65 tickets, `churn`/`refund` are already at 1.000; it's the hardest
  **categorical** decision (`department`) that needs volume (0.720 → 0.933 from 65 to 300 tickets).
  In other words: binary flags are learned fast, multi-class choice is not.
- Latency ~18 ms/ticket (GPU), unchanged by fine-tuning.

**Limit**: even with templates held out, the 300 generated tickets share one style; the absolute
values (0.93–0.98) remain optimistic against real traffic. The **relative comparisons** (loss, size)
are solid.

### Reproduce

```bash
.venv/bin/python tools/gen_dataset_big.py --target 300
.venv/bin/python tools/build_dataset.py --source data/tickets300.source.jsonl --out data/tickets300.eval.jsonl
.venv/bin/python tools/make_split.py --data data/tickets300.eval.jsonl --strategy template \
    --train-out data/train300.jsonl --test-out data/test300.jsonl
awk 'NR%4==1' data/train300.jsonl > data/train300-small.jsonl     # 65-ticket curve

for loss in soft-ce rlcd; do
  .venv/bin/python tools/train_laya.py --data data/train300.jsonl --eval data/test300.jsonl \
      --out checkpoints/t300-$loss --base multilingual --device cuda \
      --epochs 12 --micro-batch 16 --grad-accum 1 --calib-frac 0.25 --loss $loss
done
```

---

## 11. Sources & inspirations

### The model and its documentation

- **Model card** — [huggingface.co/convaiinnovations/laya](https://huggingface.co/convaiinnovations/laya)
- **Source** — [github.com/NandhaKishorM/laya](https://github.com/NandhaKishorM/laya); notably
  `docs/evals.md` (dataset/question format and metric definitions), `docs/finetune.md` (training
  recipe) and `BENCHMARKS.md` (reference figures)
- **Documentation** — [nandhakishorm.github.io/laya](https://nandhakishorm.github.io/laya/)
- **Multilingual checkpoint** — [convaiinnovations/laya-multilingual](https://huggingface.co/convaiinnovations/laya-multilingual)
  · **demo Space** — [convaiinnovations/laya-demo](https://huggingface.co/spaces/convaiinnovations/laya-demo)
  · **PyPI** — [pypi.org/project/laya](https://pypi.org/project/laya/)
- **Paper** — M, N.; M, A. *From Laya to Vega: Open Non-Autoregressive Decision Models with Calibrated
  Probabilities*, Preprints 2026, 2026110781 —
  [doi:10.20944/preprints202611.0781.v1](https://doi.org/10.20944/preprints202611.0781.v1) (this is
  where the RLCD objective and the calibrated-probability stance come from)

### What this project borrows from Laya

- the **`laya-evals` format** — one JSON line per case (`state`, `questions`, `expected`, `language`,
  `tags`) and its metric definitions (`choice_accuracy`, `noul_accuracy`, `score_mae`, `ece`, `brier`,
  `aurc`, `selective_accuracy@*`, latencies) — reimplemented in numpy in `layabench/metrics.py`;
- the **fine-tuning recipe** — `laya-train` / `laya.train.finetune`, RLCD versus soft-CE, temperature
  fitting on a held-out calibration slice;
- the **"honest limits" framing** — over-confident base checkpoints, `noul` following its labels,
  accuracy falling off past ~20 options, `action.act_probability` carrying no usable signal.

### Calibration and evaluation literature

- Guo et al., *On Calibration of Modern Neural Networks* (ECE, temperature scaling), ICML 2017
- Brier (1950), *Verification of forecasts expressed in terms of probability* — the Brier score
- Risk–coverage / selective prediction: El-Yaniv & Wiener (2010); Geifman & El-Yaniv (2017) — the AURC
  and selective-accuracy family
- Kahneman, *Thinking, Fast and Slow* — the "System 1 / System 2" framing the model card uses

### Reference datasets behind Laya's own benchmarks

Design inspiration only — **not used here**: MASSIVE (intent, 51 languages), XNLI (15 languages),
Banking77, SST-5, AG News, plus **TypeSafe / Jev**, whose published numbers are the third-party
comparator in Laya's tables.

### Tooling

PyTorch, Hugging Face `transformers` / `huggingface_hub`, **uv**, `reportlab` + Pillow (the one-pager
and the blog visuals), `pypdfium2` (PDF render checks), DejaVu fonts.

### Produced by this project

The multilingual ticket dataset (33 hand-written tickets plus generated variants), the tiered splits
(`explicit` / `stratified` / `template`), the evaluation harness, the local web tester and the
one-pager. All figures are measured on the hardware described in each section (CPU, and an RTX 4070
for the GPU runs).

---

*Author: **CTO 3D/IA at Atos** · repo: [github.com/xuarig007/laya_test](https://github.com/xuarig007/laya_test)*





