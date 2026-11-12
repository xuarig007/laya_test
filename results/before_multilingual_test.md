# Laya triage benchmark - backend `agent`

- dataset: `data/test.jsonl`
- rows: 10 | decisions: 40 | scored: 30
- noul asked as neutral-key choice: False

## Overall

| metric | value |
|---|---|
| `choice_accuracy` | 0.8 |
| `noul_accuracy` | 0.8 |
| `score_mae` | 0.5727 |
| `score_within_0.5` | 0.5 |
| `mean_confidence` | 0.9556 |
| `ece` | 0.1556 |
| `brier` | 0.155 |
| `aurc` | 0.0699 |
| `selective_accuracy@50` | 0.9333 |
| `selective_accuracy@80` | 0.875 |
| `latency_p50_ms` | 115.0001 |
| `latency_p95_ms` | 152.263 |
| `cost_per_decision_p50_ms` | 28.75 |
| `n_answers` | 40 |
| `n_scored` | 30 |

## Per question

| question | type | metric | value | n |
|---|---|---|---|---|
| churn_risk | noul | `noul_accuracy` | 0.6 | 10 |
| department | choice | `choice_accuracy` | 0.8 | 10 |
| refund_requested | noul | `noul_accuracy` | 1 | 10 |
| urgency | score | `score_mae` | 0.5727 | 10 |

## Per language

| language | choice_acc | noul_acc | score_mae | ece | n |
|---|---|---|---|---|---|
| de | 0 | 0.75 | 0.8673 | 0.3747 | 8 |
| en | 1 | 0.8333 | 0.8338 | 0.1051 | 12 |
| es | 1 | 0.75 | 0.2091 | 0.1843 | 8 |
| fr | 1 | 0.75 | 0.424 | 0.1592 | 8 |
| hi | 1 | 1 | 0.2247 | 0.0122 | 4 |

## Honest limits (from the Laya model card)

- Base checkpoints are near chance zero-shot; this is a base to fine-tune.
- Probabilities ship over-confident: refit a temperature per (type, option count) on your own data.
- `noul` can follow its own true/false labels instead of the state; compare `--noul-as-choice`.
- `action.act_probability` carries no usable signal yet; gate on confidence.
