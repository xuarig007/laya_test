# Laya triage benchmark - backend `agent`

- dataset: `data/test300.jsonl`
- rows: 75 | decisions: 300 | scored: 225
- noul asked as neutral-key choice: False

## Overall

| metric | value |
|---|---|
| `choice_accuracy` | 0.8667 |
| `noul_accuracy` | 1 |
| `score_mae` | 0.0747 |
| `score_within_0.5` | 1 |
| `mean_confidence` | 0.9238 |
| `ece` | 0.0916 |
| `brier` | 0.0459 |
| `aurc` | 0.008 |
| `selective_accuracy@50` | 1 |
| `selective_accuracy@80` | 0.9944 |
| `latency_p50_ms` | 18.3292 |
| `latency_p95_ms` | 20.0585 |
| `cost_per_decision_p50_ms` | 4.5823 |
| `n_answers` | 300 |
| `n_scored` | 225 |

## Per question

| question | type | metric | value | n |
|---|---|---|---|---|
| churn_risk | noul | `noul_accuracy` | 1 | 75 |
| department | choice | `choice_accuracy` | 0.8667 | 75 |
| refund_requested | noul | `noul_accuracy` | 1 | 75 |
| urgency | score | `score_mae` | 0.0747 | 75 |

## Per language

| language | choice_acc | noul_acc | score_mae | ece | n |
|---|---|---|---|---|---|
| de | 1 | 1 | 0.0721 | 0.0695 | 60 |
| en | 0.6667 | 1 | 0.0759 | 0.1501 | 60 |
| es | 1 | 1 | 0.0788 | 0.0832 | 60 |
| fr | 1 | 1 | 0.0751 | 0.0642 | 60 |
| hi | 0.6667 | 1 | 0.0718 | 0.1744 | 60 |

## Honest limits (from the Laya model card)

- Base checkpoints are near chance zero-shot; this is a base to fine-tune.
- Probabilities ship over-confident: refit a temperature per (type, option count) on your own data.
- `noul` can follow its own true/false labels instead of the state; compare `--noul-as-choice`.
- `action.act_probability` carries no usable signal yet; gate on confidence.
