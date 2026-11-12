# Laya triage benchmark - backend `agent`

- dataset: `data/test300.jsonl`
- rows: 75 | decisions: 300 | scored: 225
- noul asked as neutral-key choice: False

## Overall

| metric | value |
|---|---|
| `choice_accuracy` | 0.6533 |
| `noul_accuracy` | 0.7533 |
| `score_mae` | 0.6721 |
| `score_within_0.5` | 0.3867 |
| `mean_confidence` | 0.9281 |
| `ece` | 0.2223 |
| `brier` | 0.237 |
| `aurc` | 0.1491 |
| `selective_accuracy@50` | 0.9035 |
| `selective_accuracy@80` | 0.75 |
| `latency_p50_ms` | 18.1723 |
| `latency_p95_ms` | 20.469 |
| `cost_per_decision_p50_ms` | 4.5431 |
| `n_answers` | 300 |
| `n_scored` | 225 |

## Per question

| question | type | metric | value | n |
|---|---|---|---|---|
| churn_risk | noul | `noul_accuracy` | 0.6 | 75 |
| department | choice | `choice_accuracy` | 0.6533 | 75 |
| refund_requested | noul | `noul_accuracy` | 0.9067 | 75 |
| urgency | score | `score_mae` | 0.6721 | 75 |

## Per language

| language | choice_acc | noul_acc | score_mae | ece | n |
|---|---|---|---|---|---|
| de | 0.8 | 0.8 | 0.6078 | 0.1919 | 60 |
| en | 0.6 | 0.8 | 0.58 | 0.2877 | 60 |
| es | 0.6 | 0.6667 | 0.7627 | 0.2801 | 60 |
| fr | 0.6667 | 0.7 | 0.7244 | 0.2755 | 60 |
| hi | 0.6 | 0.8 | 0.6854 | 0.2236 | 60 |

## Honest limits (from the Laya model card)

- Base checkpoints are near chance zero-shot; this is a base to fine-tune.
- Probabilities ship over-confident: refit a temperature per (type, option count) on your own data.
- `noul` can follow its own true/false labels instead of the state; compare `--noul-as-choice`.
- `action.act_probability` carries no usable signal yet; gate on confidence.
