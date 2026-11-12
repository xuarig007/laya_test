# Laya triage benchmark - backend `agent`

- dataset: `data/test300.jsonl`
- rows: 75 | decisions: 300 | scored: 225
- noul asked as neutral-key choice: False

## Overall

| metric | value |
|---|---|
| `choice_accuracy` | 0.9333 |
| `noul_accuracy` | 1 |
| `score_mae` | 0.0983 |
| `score_within_0.5` | 0.9867 |
| `mean_confidence` | 0.9166 |
| `ece` | 0.0673 |
| `brier` | 0.0309 |
| `aurc` | 0.0039 |
| `selective_accuracy@50` | 1 |
| `selective_accuracy@80` | 0.989 |
| `latency_p50_ms` | 18.4271 |
| `latency_p95_ms` | 39.3194 |
| `cost_per_decision_p50_ms` | 4.6068 |
| `n_answers` | 300 |
| `n_scored` | 225 |

## Per question

| question | type | metric | value | n |
|---|---|---|---|---|
| churn_risk | noul | `noul_accuracy` | 1 | 75 |
| department | choice | `choice_accuracy` | 0.9333 | 75 |
| refund_requested | noul | `noul_accuracy` | 1 | 75 |
| urgency | score | `score_mae` | 0.0983 | 75 |

## Per language

| language | choice_acc | noul_acc | score_mae | ece | n |
|---|---|---|---|---|---|
| de | 1 | 1 | 0.0785 | 0.0672 | 60 |
| en | 1 | 1 | 0.0977 | 0.0848 | 60 |
| es | 1 | 1 | 0.1485 | 0.0864 | 60 |
| fr | 1 | 1 | 0.0875 | 0.0666 | 60 |
| hi | 0.6667 | 1 | 0.0792 | 0.1749 | 60 |

## Honest limits (from the Laya model card)

- Base checkpoints are near chance zero-shot; this is a base to fine-tune.
- Probabilities ship over-confident: refit a temperature per (type, option count) on your own data.
- `noul` can follow its own true/false labels instead of the state; compare `--noul-as-choice`.
- `action.act_probability` carries no usable signal yet; gate on confidence.
