# Laya triage benchmark - backend `agent`

- dataset: `data/test100.jsonl`
- rows: 21 | decisions: 84 | scored: 63
- noul asked as neutral-key choice: False

## Overall

| metric | value |
|---|---|
| `choice_accuracy` | 0.9048 |
| `noul_accuracy` | 0.9524 |
| `score_mae` | 0.3326 |
| `score_within_0.5` | 0.7619 |
| `mean_confidence` | 0.9064 |
| `ece` | 0.1001 |
| `brier` | 0.0316 |
| `aurc` | 0.0028 |
| `selective_accuracy@50` | 1 |
| `selective_accuracy@80` | 1 |
| `latency_p50_ms` | 18.2783 |
| `latency_p95_ms` | 19.428 |
| `cost_per_decision_p50_ms` | 4.5696 |
| `n_answers` | 84 |
| `n_scored` | 63 |

## Per question

| question | type | metric | value | n |
|---|---|---|---|---|
| churn_risk | noul | `noul_accuracy` | 1 | 21 |
| department | choice | `choice_accuracy` | 0.9048 | 21 |
| refund_requested | noul | `noul_accuracy` | 0.9048 | 21 |
| urgency | score | `score_mae` | 0.3326 | 21 |

## Per language

| language | choice_acc | noul_acc | score_mae | ece | n |
|---|---|---|---|---|---|
| de | 1 | 0.875 | 0.3604 | 0.1127 | 16 |
| en | 1 | 1 | 0.4434 | 0.0724 | 20 |
| es | 1 | 1 | 0.3645 | 0.0768 | 16 |
| fr | 0.8 | 0.9 | 0.3157 | 0.1351 | 20 |
| hi | 0.6667 | 1 | 0.0963 | 0.1635 | 12 |

## Honest limits (from the Laya model card)

- Base checkpoints are near chance zero-shot; this is a base to fine-tune.
- Probabilities ship over-confident: refit a temperature per (type, option count) on your own data.
- `noul` can follow its own true/false labels instead of the state; compare `--noul-as-choice`.
- `action.act_probability` carries no usable signal yet; gate on confidence.
