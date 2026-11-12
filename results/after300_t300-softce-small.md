# Laya triage benchmark - backend `agent`

- dataset: `data/test300.jsonl`
- rows: 75 | decisions: 300 | scored: 225
- noul asked as neutral-key choice: False

## Overall

| metric | value |
|---|---|
| `choice_accuracy` | 0.72 |
| `noul_accuracy` | 1 |
| `score_mae` | 0.1264 |
| `score_within_0.5` | 0.96 |
| `mean_confidence` | 0.9067 |
| `ece` | 0.0724 |
| `brier` | 0.0573 |
| `aurc` | 0.0087 |
| `selective_accuracy@50` | 1 |
| `selective_accuracy@80` | 0.9944 |
| `latency_p50_ms` | 19.4054 |
| `latency_p95_ms` | 23.3829 |
| `cost_per_decision_p50_ms` | 4.8513 |
| `n_answers` | 300 |
| `n_scored` | 225 |

## Per question

| question | type | metric | value | n |
|---|---|---|---|---|
| churn_risk | noul | `noul_accuracy` | 1 | 75 |
| department | choice | `choice_accuracy` | 0.72 | 75 |
| refund_requested | noul | `noul_accuracy` | 1 | 75 |
| urgency | score | `score_mae` | 0.1264 | 75 |

## Per language

| language | choice_acc | noul_acc | score_mae | ece | n |
|---|---|---|---|---|---|
| de | 0.9333 | 1 | 0.1066 | 0.0821 | 60 |
| en | 0.6667 | 1 | 0.0845 | 0.1115 | 60 |
| es | 0.8 | 1 | 0.1068 | 0.093 | 60 |
| fr | 0.6667 | 1 | 0.1096 | 0.1323 | 60 |
| hi | 0.5333 | 1 | 0.2245 | 0.1176 | 60 |

## Honest limits (from the Laya model card)

- Base checkpoints are near chance zero-shot; this is a base to fine-tune.
- Probabilities ship over-confident: refit a temperature per (type, option count) on your own data.
- `noul` can follow its own true/false labels instead of the state; compare `--noul-as-choice`.
- `action.act_probability` carries no usable signal yet; gate on confidence.
