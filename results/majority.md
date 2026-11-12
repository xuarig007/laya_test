# Laya triage benchmark - backend `majority`

- dataset: `data/tickets.eval.jsonl`
- rows: 33 | decisions: 132 | scored: 99
- noul asked as neutral-key choice: False

## Overall

| metric | value |
|---|---|
| `choice_accuracy` | 0.4848 |
| `noul_accuracy` | 0.7727 |
| `score_mae` | 0.4545 |
| `score_within_0.5` | 0.5455 |
| `mean_confidence` | 0.6768 |
| `ece` | 0 |
| `brier` | 0.2002 |
| `aurc` | 0.2542 |
| `selective_accuracy@50` | 0.7727 |
| `selective_accuracy@80` | 0.6768 |
| `latency_p50_ms` | 0.0014 |
| `latency_p95_ms` | 0.0058 |
| `cost_per_decision_p50_ms` | 0.0003 |
| `n_answers` | 132 |
| `n_scored` | 99 |

## Per question

| question | type | metric | value | n |
|---|---|---|---|---|
| churn_risk | noul | `noul_accuracy` | 0.7879 | 33 |
| department | choice | `choice_accuracy` | 0.4848 | 33 |
| refund_requested | noul | `noul_accuracy` | 0.7576 | 33 |
| urgency | score | `score_mae` | 0.4545 | 33 |

## Per language

| language | choice_acc | noul_acc | score_mae | ece | n |
|---|---|---|---|---|---|
| de | 0.4286 | 0.8571 | 0.4286 | 0.075 | 28 |
| en | 0.4 | 0.75 | 0.7 | 0.0434 | 40 |
| es | 0.5714 | 0.7143 | 0.2857 | 0.0678 | 28 |
| fr | 0.5 | 0.8125 | 0.375 | 0.0316 | 32 |
| hi | 1 | 0.5 | 0 | 0.3535 | 4 |

## Honest limits (from the Laya model card)

- Base checkpoints are near chance zero-shot; this is a base to fine-tune.
- Probabilities ship over-confident: refit a temperature per (type, option count) on your own data.
- `noul` can follow its own true/false labels instead of the state; compare `--noul-as-choice`.
- `action.act_probability` carries no usable signal yet; gate on confidence.
