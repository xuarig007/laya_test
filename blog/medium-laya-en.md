# Laya, from zero-shot to production: fine-tuning an open-source decision engine

*Routing support tickets in 5 languages in a single forward pass. From 33 to 300 examples, CPU then GPU — with the numbers, including the ones that hurt.*

> **TL;DR** — I benchmarked and then fine-tuned **Laya**, a non-autoregressive decision engine, on a real use case (multilingual support-ticket routing). Zero-shot it looks promising but misses a critical signal *with high confidence*. After fine-tuning on 300 examples: **department choice 0.65 → 0.93**, **churn risk 0.60 → 1.00**, **urgency MAE 0.67 → 0.10** — and the test set only contains phrasings never seen during training.

---

## The problem: classify, don't generate

A support organisation receives tickets in English, French, German, Spanish, Hindi. Before any human touches them, you need to *classify*: which team, how urgent, is the customer about to churn, are they asking for a refund?

The reflex is to call a generative LLM: "answer in JSON: category, urgency, …". Except that:

- you **pay to generate text you immediately throw away**;
- the **JSON breaks** (markdown fences, missing fields) and you have to repair it;
- **latency swings** with output length;
- most of all, this isn't a generation task. It's a **discrete decision**.

## Laya in three lines

**Laya** (Convai Innovations, Apache-2.0) is a **"System 1" decision engine**: you give it a *state* (text, email, ticket or JSON) and **typed questions**, and it returns typed answers **with probabilities**, in **a single forward pass** (~18–33 ms on GPU), across 100+ languages.

Three primitives are enough:

![Laya in three lines](https://raw.githubusercontent.com/xuarig007/laya_test/main/blog/assets/table-en-laya-in-three-lines.png)

It **never generates text**: nothing to parse, nothing to hallucinate. A built-in `Router` even picks the right checkpoint based on the detected language. And it all runs **locally**.

## My use case: a triage gateway

Each ticket becomes **four typed decisions**, in one pass:

![My use case: a triage gateway](https://raw.githubusercontent.com/xuarig007/laya_test/main/blog/assets/table-en-my-use-case-a-triage-gateway.png)

Routing a ticket is exactly that: picking a path, with a probability attached.

![Routing is a decision: which path does the ticket take — technical, account or billing?](https://raw.githubusercontent.com/xuarig007/laya_test/main/blog/assets/laya.jpg)

I built a small evaluation harness (metrics identical to Laya's own: accuracy, MAE, ECE, Brier, AURC, *selective accuracy*) plus a labelled dataset — first **33 hand-written tickets**, then larger versions.

---

## Step 1 — zero-shot: promising, with a blind spot

On the 33 tickets (5 languages):

- `choice` **0.909**, `noul` **0.879**, ECE **0.070**, AURC **0.032**
- but `churn_risk` **0.818** — and it's worse than that number suggests.

Reading the errors one by one, a pattern jumps out:

```
[fr] "Si elle n'est pas corrigée aujourd'hui, je résilie mon abonnement."
     churn_risk → 0.0033   (almost zero churn probability)   confidence = 1.00  ❌
[de] "Wenn das nicht sofort behoben wird, kündige ich meinen Vertrag."
     churn_risk → 0.0074                                     confidence = 0.99  ❌
[es] "Si no arreglan esto hoy, cancelo mi suscripción y me voy."
     churn_risk → 0.0518                                     confidence = 0.95  ❌
```

Tickets that explicitly threaten to leave are classified as "no churn", **with 99% confidence**. That is *exactly* the weakness the model card documents: `noul` can "follow its own labels", and negation is poorly handled.

> **Lesson #1**: a model can be great on average and **confidently wrong** on the one signal that matters. Read the errors, not just the aggregate.

---

## Step 2 — fine-tuning on 33 tickets? Not enough

I split 23 tickets for training and kept 10 aside, then fine-tuned on CPU (encoder frozen first, then full).

![Step 2 — fine-tuning on 33 tickets? Not enough](https://raw.githubusercontent.com/xuarig007/laya_test/main/blog/assets/table-en-step-2-fine-tuning-on-33-tickets-not-enough.png)

`churn` stays stuck around **0.60**. The reason: only **3 positive churn examples** in training. The problem isn't the settings, it's **the data**.

> **Lesson #2**: freezing the encoder isn't enough (the useful specialisation goes through the encoder) — and a class with 3 examples doesn't get learned.

---

## Step 3 — 100 tickets + GPU: the breakthrough

I move to **100 tickets** (the 33 hand-written ones + 67 generated, 5 languages) and train the **full model on GPU** (RTX 4070, CUDA `torch`).

Two settings change everything:
1. **`calib_frac=0.25`** makes the calibration slice big enough for the temperatures to **actually fit** (with 33 tickets they stayed pinned at 1.0);
2. more data for the class that was missing.

Results on the 21 held-out tickets (84 decisions):

![Step 3 — 100 tickets + GPU: the breakthrough](https://raw.githubusercontent.com/xuarig007/laya_test/main/blog/assets/table-en-step-3-100-tickets-gpu-the-breakthrough.png)

And above all: **`churn_risk` 0.714 → 1.000**. The blind spot from step 1 is fixed — not by swapping models, but by **giving it data**.

> **Lesson #3**: the "you need more data" conclusion holds. You go from "promising but not production-ready" to a usable triage.

---

## Step 4 — 300 tickets, and honest testing

This is where the difference between an *impressive* benchmark and a *useful* one lives.

If the test set is generated from the same templates as training, the model just learns the phrasing and the scores are inflated. So I split the dataset **by template**: one whole realisation per (language, department) is held out. The test set therefore only contains **phrasings never seen during training**.

![Results on the held-out test](https://raw.githubusercontent.com/xuarig007/laya_test/main/blog/assets/results-en.png)

Per question (soft-ce 300 vs base):

![Step 4 — 300 tickets, and honest testing](https://raw.githubusercontent.com/xuarig007/laya_test/main/blog/assets/table-en-step-4-300-tickets-and-honest-testing.png)

What these numbers really say:

- **It generalises.** On **unseen phrasings**, fine-tuning lifts `choice` from 0.653 to **0.933** and drops `AURC` from 0.149 to **0.004**. That's not memorisation.
- **`soft-ce` vs `rlcd`**: `soft-ce` wins on the **categorical** decision and on **calibration** (ECE 0.067 vs 0.092); `rlcd` wins slightly on the **ordinal** one (urgency MAE 0.075 vs 0.098) and at high coverage. Nothing is decided in the abstract — measure on your own data.
- **Data curve**: at 65 tickets the binary flags (`churn`, `refund`) are **already at 1.000**. It's the **multi-class** decision (`department`) that needs volume (0.720 → 0.933 from 65 to 300 tickets).

> **Lesson #4**: binary decisions are learned fast; picking among several classes is not. Size your data per *primitive*, not on average.

### What about calibration?

It's the part people forget. A decision engine that says 0.95 and is wrong is *dangerous* if you use it to trigger an automated action. Hence the calibration metrics:

- **ECE** (confidence vs accuracy gap): 0.222 → **0.067**
- **AURC** (does confidence *rank* right from wrong?): 0.149 → **0.004**
- **`selective_accuracy@80`**: accepting only the most confident 80%, accuracy goes from 0.75 to **0.99**.

In other words: after fine-tuning you can **gate** on confidence and only auto-route what is actually safe.

> **Lesson #5**: calibration is a **deliverable**, not an implementation detail. Publish ECE alongside accuracy.

---

## My five takeaways

1. **Laya is a base, not a plug-and-play engine.** Zero-shot it nearly matches a hand-written rules engine — and the docs say it themselves: *"fine-tuning is where most of the value is"*.
2. **Full fine-tuning changes everything**; freezing the encoder does not.
3. **Data size scales with the primitive**: yes/no flags need little, multi-class choice needs volume.
4. **Test on unseen phrasings**, otherwise you're measuring memorisation.
5. **Calibration is the real story** if you want to automate: it's what makes a decision *gateable*.

## Bonus: a tiny UI to see it with your own eyes

![The tester: without fine-tuning vs with fine-tuning](https://raw.githubusercontent.com/xuarig007/laya_test/main/blog/assets/shot-en.png)

Rather than trusting tables, I built myself a local web page: paste a ticket, hit **Analyze**, and you get **two columns side by side** — "without fine-tuning" vs "with fine-tuning" — with the full probability breakdown, the confidence, and a **"differs" badge** whenever the two models disagree. A collapsible guide documents every category (definition, domain of application, downstream action) and shows up as a hover tooltip.

The interface is **multilingual**: picking a language (EN, FR, DE, ES, HI) switches the whole UI *and* the category guide, and loads a matching example ticket — the same page, in German:

![The same page in German](https://raw.githubusercontent.com/xuarig007/laya_test/main/blog/assets/shot-de.png)

It's the best way to catch the cases where the base model is **confident and wrong** (the `churn` blind spot from step 1) — and to confirm that fine-tuning actually fixes *that* case.

## Reproduce it

The full code is on GitHub: **[github.com/xuarig007/laya_test](https://github.com/xuarig007/laya_test)** — evaluation harness, datasets and tools:

```bash
# the evaluation harness (metrics identical to laya.evals)
python -m layabench run --data data/test300.jsonl --backend agent \
    --checkpoint checkpoints/t300-softce --device cuda --warmup

# compare two reports
python -m layabench compare results/after300_t300-softce.json \
    --baseline results/before300_multilingual_test.json

# fine-tune on GPU
python tools/train_laya.py --data data/train300.jsonl --eval data/test300.jsonl \
    --out checkpoints/t300-softce --base multilingual --device cuda \
    --epochs 12 --micro-batch 16 --grad-accum 1 --calib-frac 0.25 --loss soft-ce
```

## Conclusion

Laya isn't just another LLM: it's a **decision engine** — one forward pass, calibrated probabilities, zero generated text. Zero-shot it's a decent base; fine-tuned, on 300 examples and an hour of GPU, it's a multilingual triage that actually holds up.

If you have **classification / routing / gating** tasks in a multilingual stream, it's worth a look: faster, cheaper and more predictable than calling a generative model.

## Sources & inspirations

This project builds directly on Laya and on a few well-known ideas. Here is what it draws from.

**The model and its documentation**

- Model card — [huggingface.co/convaiinnovations/laya](https://huggingface.co/convaiinnovations/laya)
- Source and docs — [github.com/NandhaKishorM/laya](https://github.com/NandhaKishorM/laya) and
  [nandhakishorm.github.io/laya](https://nandhakishorm.github.io/laya/), in particular `docs/evals.md`
  (dataset format and metric definitions) and `docs/finetune.md` (the training recipe)
- Multilingual checkpoint — [convaiinnovations/laya-multilingual](https://huggingface.co/convaiinnovations/laya-multilingual);
  live demo — [convaiinnovations/laya-demo](https://huggingface.co/spaces/convaiinnovations/laya-demo);
  PyPI — [pypi.org/project/laya](https://pypi.org/project/laya/)
- Paper — M, N.; M, A., *From Laya to Vega: Open Non-Autoregressive Decision Models with Calibrated
  Probabilities*, Preprints 2026, 2026110781 ([doi:10.20944/preprints202611.0781.v1](https://doi.org/10.20944/preprints202611.0781.v1))
  — where the RLCD objective and the calibrated-probability stance come from

**Borrowed from Laya**: the `laya-evals` dataset format and its metric definitions (re-implemented in
numpy here), the fine-tuning recipe (soft-CE vs RLCD, temperature fitting on a held-out calibration
slice), and the "honest limits" framing (over-confident checkpoints, `noul` following its labels,
accuracy falling off past ~20 options).

**Calibration and evaluation literature**: Guo et al., *On Calibration of Modern Neural Networks*
(ICML 2017 — ECE and temperature scaling); Brier (1950) for the Brier score; El-Yaniv & Wiener (2010)
and Geifman & El-Yaniv (2017) for risk–coverage and selective prediction (AURC, selective accuracy);
Kahneman's *Thinking, Fast and Slow* for the "System 1" framing.

**Reference datasets behind Laya's own benchmarks** (design inspiration, not used here): MASSIVE,
XNLI, Banking77, SST-5, AG News — and TypeSafe/Jev as the third-party comparator.

**Tooling**: PyTorch, Hugging Face `transformers`, uv, reportlab + Pillow, DejaVu fonts.

*If this was useful, a clap 👏 helps others find it. And if you fine-tuned Laya on your own decisions, tell me how it went in the comments.*

---

*About the author — **CTO 3D/IA at Atos**. I build decision and applied-AI systems; the code for this article is open: [github.com/xuarig007/laya_test](https://github.com/xuarig007/laya_test).*
