# Laya triage benchmark - backend `laya`

- dataset: `data/tickets.eval.jsonl`
- rows: 33 | decisions: 132 | scored: 99
- noul asked as neutral-key choice: True

## Overall

| metric | value |
|---|---|
| `choice_accuracy` | 0.9091 |
| `noul_accuracy` | 0.8485 |
| `score_mae` | 0.5671 |
| `score_within_0.5` | 0.4545 |
| `mean_confidence` | 0.8552 |
| `ece` | 0.0787 |
| `brier` | 0.0947 |
| `aurc` | 0.04 |
| `selective_accuracy@50` | 0.98 |
| `selective_accuracy@80` | 0.925 |
| `latency_p50_ms` | 160.193 |
| `latency_p95_ms` | 493.3643 |
| `cost_per_decision_p50_ms` | 40.0483 |
| `n_answers` | 132 |
| `n_scored` | 99 |

## Per question

| question | type | metric | value | n |
|---|---|---|---|---|
| churn_risk | noul | `noul_accuracy` | 0.8485 | 33 |
| department | choice | `choice_accuracy` | 0.9091 | 33 |
| refund_requested | noul | `noul_accuracy` | 0.8485 | 33 |
| urgency | score | `score_mae` | 0.5671 | 33 |

## Per language

| language | choice_acc | noul_acc | score_mae | ece | n |
|---|---|---|---|---|---|
| de | 0.7143 | 0.7857 | 0.4693 | 0.1891 | 28 |
| en | 1 | 0.85 | 0.6068 | 0.1773 | 40 |
| es | 1 | 0.7857 | 0.6249 | 0.1122 | 28 |
| fr | 0.875 | 0.9375 | 0.5952 | 0.0875 | 32 |
| hi | 1 | 1 | 0.2247 | 0.1102 | 4 |

## Honest limits (from the Laya model card)

- Base checkpoints are near chance zero-shot; this is a base to fine-tune.
- Probabilities ship over-confident: refit a temperature per (type, option count) on your own data.
- `noul` can follow its own true/false labels instead of the state; compare `--noul-as-choice`.
- `action.act_probability` carries no usable signal yet; gate on confidence.
