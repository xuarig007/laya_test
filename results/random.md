# Laya triage benchmark - backend `random`

- dataset: `data/tickets.eval.jsonl`
- rows: 33 | decisions: 132 | scored: 99
- noul asked as neutral-key choice: False

## Overall

| metric | value |
|---|---|
| `choice_accuracy` | 0.303 |
| `noul_accuracy` | 0.5 |
| `score_mae` | 0.8485 |
| `score_within_0.5` | 0.2727 |
| `mean_confidence` | 0.5 |
| `ece` | 0.0657 |
| `brier` | 0.25 |
| `aurc` | 0.5657 |
| `selective_accuracy@50` | 0.4343 |
| `selective_accuracy@80` | 0.4343 |
| `latency_p50_ms` | 0.0031 |
| `latency_p95_ms` | 0.0107 |
| `cost_per_decision_p50_ms` | 0.0008 |
| `n_answers` | 132 |
| `n_scored` | 99 |

## Per question

| question | type | metric | value | n |
|---|---|---|---|---|
| churn_risk | noul | `noul_accuracy` | 0.5455 | 33 |
| department | choice | `choice_accuracy` | 0.303 | 33 |
| refund_requested | noul | `noul_accuracy` | 0.4545 | 33 |
| urgency | score | `score_mae` | 0.8485 | 33 |

## Per language

| language | choice_acc | noul_acc | score_mae | ece | n |
|---|---|---|---|---|---|
| de | 0.2857 | 0.5 | 0.8571 | 0.0714 | 28 |
| en | 0.4 | 0.4 | 1 | 0.1 | 40 |
| es | 0.4286 | 0.5 | 0.7143 | 0.0238 | 28 |
| fr | 0.125 | 0.625 | 0.875 | 0.0417 | 32 |
| hi | 0 | 0.5 | 0 | 0.1667 | 4 |

## Honest limits (from the Laya model card)

- Base checkpoints are near chance zero-shot; this is a base to fine-tune.
- Probabilities ship over-confident: refit a temperature per (type, option count) on your own data.
- `noul` can follow its own true/false labels instead of the state; compare `--noul-as-choice`.
- `action.act_probability` carries no usable signal yet; gate on confidence.
