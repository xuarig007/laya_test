# Laya triage benchmark - backend `agent`

- dataset: `data/test.jsonl`
- rows: 10 | decisions: 40 | scored: 30
- noul asked as neutral-key choice: False

## Overall

| metric | value |
|---|---|
| `choice_accuracy` | 1 |
| `noul_accuracy` | 0.9 |
| `score_mae` | 0.3359 |
| `score_within_0.5` | 0.7 |
| `mean_confidence` | 0.8793 |
| `ece` | 0.1205 |
| `brier` | 0.0773 |
| `aurc` | 0.0205 |
| `selective_accuracy@50` | 1 |
| `selective_accuracy@80` | 0.9583 |
| `latency_p50_ms` | 146.24 |
| `latency_p95_ms` | 159.6688 |
| `cost_per_decision_p50_ms` | 36.56 |
| `n_answers` | 40 |
| `n_scored` | 30 |

## Per question

| question | type | metric | value | n |
|---|---|---|---|---|
| churn_risk | noul | `noul_accuracy` | 0.8 | 10 |
| department | choice | `choice_accuracy` | 1 | 10 |
| refund_requested | noul | `noul_accuracy` | 1 | 10 |
| urgency | score | `score_mae` | 0.3359 | 10 |

## Per language

| language | choice_acc | noul_acc | score_mae | ece | n |
|---|---|---|---|---|---|
| de | 1 | 0.75 | 0.5423 | 0.2106 | 8 |
| en | 1 | 1 | 0.3729 | 0.1098 | 12 |
| es | 1 | 1 | 0.0676 | 0.1498 | 8 |
| fr | 1 | 0.75 | 0.5102 | 0.1601 | 8 |
| hi | 1 | 1 | 0.0001 | 0.1474 | 4 |

## Honest limits (from the Laya model card)

- Base checkpoints are near chance zero-shot; this is a base to fine-tune.
- Probabilities ship over-confident: refit a temperature per (type, option count) on your own data.
- `noul` can follow its own true/false labels instead of the state; compare `--noul-as-choice`.
- `action.act_probability` carries no usable signal yet; gate on confidence.
