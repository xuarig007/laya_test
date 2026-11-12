# Laya triage benchmark - backend `agent`

- dataset: `data/test300.jsonl`
- rows: 75 | decisions: 300 | scored: 225
- noul asked as neutral-key choice: False

## Overall

| metric | value |
|---|---|
| `choice_accuracy` | 0.56 |
| `noul_accuracy` | 0.7133 |
| `score_mae` | 0.7423 |
| `score_within_0.5` | 0.3467 |
| `mean_confidence` | 0.8716 |
| `ece` | 0.2094 |
| `brier` | 0.2423 |
| `aurc` | 0.271 |
| `selective_accuracy@50` | 0.7699 |
| `selective_accuracy@80` | 0.7333 |
| `latency_p50_ms` | 36.7589 |
| `latency_p95_ms` | 42.6284 |
| `cost_per_decision_p50_ms` | 9.1897 |
| `n_answers` | 300 |
| `n_scored` | 225 |

## Per question

| question | type | metric | value | n |
|---|---|---|---|---|
| churn_risk | noul | `noul_accuracy` | 0.8933 | 75 |
| department | choice | `choice_accuracy` | 0.56 | 75 |
| refund_requested | noul | `noul_accuracy` | 0.5333 | 75 |
| urgency | score | `score_mae` | 0.7423 | 75 |

## Per language

| language | choice_acc | noul_acc | score_mae | ece | n |
|---|---|---|---|---|---|
| de | 0.8 | 0.7 | 0.6881 | 0.1376 | 60 |
| en | 0.4667 | 0.9 | 0.7677 | 0.1773 | 60 |
| es | 0.5333 | 0.7 | 0.7937 | 0.323 | 60 |
| fr | 0.4 | 0.6667 | 0.6933 | 0.3007 | 60 |
| hi | 0.6 | 0.6 | 0.7687 | 0.2386 | 60 |

## Honest limits (from the Laya model card)

- Base checkpoints are near chance zero-shot; this is a base to fine-tune.
- Probabilities ship over-confident: refit a temperature per (type, option count) on your own data.
- `noul` can follow its own true/false labels instead of the state; compare `--noul-as-choice`.
- `action.act_probability` carries no usable signal yet; gate on confidence.
