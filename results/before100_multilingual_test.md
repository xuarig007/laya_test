# Laya triage benchmark - backend `agent`

- dataset: `data/test100.jsonl`
- rows: 21 | decisions: 84 | scored: 63
- noul asked as neutral-key choice: False

## Overall

| metric | value |
|---|---|
| `choice_accuracy` | 0.7143 |
| `noul_accuracy` | 0.8333 |
| `score_mae` | 0.8234 |
| `score_within_0.5` | 0.1905 |
| `mean_confidence` | 0.9246 |
| `ece` | 0.1335 |
| `brier` | 0.1351 |
| `aurc` | 0.0595 |
| `selective_accuracy@50` | 0.9688 |
| `selective_accuracy@80` | 0.8824 |
| `latency_p50_ms` | 23.5374 |
| `latency_p95_ms` | 28.874 |
| `cost_per_decision_p50_ms` | 5.8843 |
| `n_answers` | 84 |
| `n_scored` | 63 |

## Per question

| question | type | metric | value | n |
|---|---|---|---|---|
| churn_risk | noul | `noul_accuracy` | 0.7143 | 21 |
| department | choice | `choice_accuracy` | 0.7143 | 21 |
| refund_requested | noul | `noul_accuracy` | 0.9524 | 21 |
| urgency | score | `score_mae` | 0.8234 | 21 |

## Per language

| language | choice_acc | noul_acc | score_mae | ece | n |
|---|---|---|---|---|---|
| de | 0.75 | 0.875 | 0.8239 | 0.1291 | 16 |
| en | 1 | 0.8 | 0.8811 | 0.1512 | 20 |
| es | 0.75 | 0.875 | 0.968 | 0.1228 | 16 |
| fr | 0.8 | 0.8 | 0.722 | 0.1864 | 20 |
| hi | 0 | 0.8333 | 0.7028 | 0.2565 | 12 |

## Honest limits (from the Laya model card)

- Base checkpoints are near chance zero-shot; this is a base to fine-tune.
- Probabilities ship over-confident: refit a temperature per (type, option count) on your own data.
- `noul` can follow its own true/false labels instead of the state; compare `--noul-as-choice`.
- `action.act_probability` carries no usable signal yet; gate on confidence.
