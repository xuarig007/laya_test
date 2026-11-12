# Laya triage benchmark - backend `heuristic`

- dataset: `data/tickets.eval.jsonl`
- rows: 33 | decisions: 132 | scored: 99
- noul asked as neutral-key choice: False

## Overall

| metric | value |
|---|---|
| `choice_accuracy` | 0.9394 |
| `noul_accuracy` | 0.9697 |
| `score_mae` | 0.5455 |
| `score_within_0.5` | 0.4848 |
| `mean_confidence` | 0.8364 |
| `ece` | 0.1273 |
| `brier` | 0.0428 |
| `aurc` | 0.0214 |
| `selective_accuracy@50` | 0.9792 |
| `selective_accuracy@80` | 0.9792 |
| `latency_p50_ms` | 0.0205 |
| `latency_p95_ms` | 0.0258 |
| `cost_per_decision_p50_ms` | 0.0051 |
| `n_answers` | 132 |
| `n_scored` | 99 |

## Per question

| question | type | metric | value | n |
|---|---|---|---|---|
| churn_risk | noul | `noul_accuracy` | 1 | 33 |
| department | choice | `choice_accuracy` | 0.9394 | 33 |
| refund_requested | noul | `noul_accuracy` | 0.9394 | 33 |
| urgency | score | `score_mae` | 0.5455 | 33 |

## Per language

| language | choice_acc | noul_acc | score_mae | ece | n |
|---|---|---|---|---|---|
| de | 0.8571 | 0.9286 | 0.8571 | 0.1143 | 28 |
| en | 1 | 1 | 0.6 | 0.15 | 40 |
| es | 1 | 1 | 0.4286 | 0.15 | 28 |
| fr | 0.875 | 1 | 0.25 | 0.1604 | 32 |
| hi | 1 | 0.5 | 1 | 0.4333 | 4 |

## Honest limits (from the Laya model card)

- Base checkpoints are near chance zero-shot; this is a base to fine-tune.
- Probabilities ship over-confident: refit a temperature per (type, option count) on your own data.
- `noul` can follow its own true/false labels instead of the state; compare `--noul-as-choice`.
- `action.act_probability` carries no usable signal yet; gate on confidence.
