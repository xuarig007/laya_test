# layabench — benchmark de triage de tickets support multilingue pour **Laya**

> Cas d'usage et benchmark *imaginés* à partir de la carte de modèle
> [`convaiinnovations/laya`](https://huggingface.co/convaiinnovations/laya) et de sa
> [documentation](https://nandhakishorm.github.io/laya/). Tout ici est exécutable et
> reproductible : jeu de données étiqueté, backends comparés, métriques, rapports.
>
> **English version:** see [`README.md`](README.md) (the default).

**Dépôt :** https://github.com/xuarig007/laya_test

Laya est un **moteur de décision** (*System 1*, non-autorégressif) : on lui donne un *état*
(texte, e-mail, ticket ou JSON) et des **questions typées**, et il renvoie des réponses typées
avec des probabilités dans **un seul forward pass (~33 ms GPU)**, en 100+ langues. Il ne génère
jamais de texte — donc rien à parser, rien à halluciner — et un `Router` choisit tout seul le
checkpoint (`english` / `multilingual`) selon la langue détectée.

---

## 1. Le cas d'usage imaginé : une passerelle de triage multilingue

**Une passerelle de triage à l'entrée du support (smart ingress).**
Une organisation reçoit des tickets dans plusieurs langues (EN / FR / DE / ES / HI…). Avant
tout traitement, chaque ticket est transformé en **quatre décisions typées**, en un seul
forward pass :

| question (`id`) | type Laya | sortie | rôle en aval |
|---|---|---|---|
| `department` | `choice` | `billing` \| `technical` \| `account` | router vers la bonne file |
| `urgency` | `score` | `0` \| `1` \| `2` | priorisation / SLA |
| `churn_risk` | `noul` | probabilité de « oui » | alerte rétention |
| `refund_requested` | `noul` | probabilité de « oui » | déclencher la politique de remboursement |

```
ticket ──▶ laya.Router.predict(state, QUESTION_POLICY) ──▶ { department, urgency, churn_risk, refund_requested }
              │                                                    │
              └─ route selon la langue (english | multilingual)     └─ confiance par réponse ─▶ passe auto si confiance élevée
```

**Pourquoi Laya plutôt qu'un LLM génératif ici ?** C'est une **décision discrète** (pas de texte
à produire), le schéma est **fixe** (rien à réparer côté JSON), l'inférence est **courte et
prévisible** (un forward pass, pas de boucle de décodage), le **routage multilingue est intégré**,
et tout tourne **en local, sur CPU** — les données clients ne sortent pas du périmètre.

La politique de questions est définie **une seule fois** dans
[`layabench/schema.py`](layabench/schema.py) et injectée dans le jeu de données par le générateur,
pour que le dataset et le harness ne puissent jamais diverger.

---

## 2. Le benchmark imaginé

### Hypothèses testées

- **H1.** Laya **zero-shot** est-il exploitable pour trier des tickets en plusieurs langues ?
- **H2.** Sa **confiance** est-elle assez fiable pour une passe automatique (« auto-résolution »
  quand la confiance est haute) ? → `ece`, `brier`, `aurc`, `selective_accuracy@*`.
- **H3.** Le contournement documenté de `noul` (reposer la question booléenne en `choice` à clés
  neutres) **améliore-t-il** vraiment les résultats *sur nos données* ?

### Jeu de données

33 tickets étiquetés à la main, répartis par langue : **EN 10, FR 8, DE 7, ES 7, HI 1**
(le ticket hindi est fourni sous forme de **document JSON**, pour montrer que l'état peut être
autre chose qu'une chaîne). 132 décisions au total.

Le format est celui de `laya-evals` : une ligne JSON par cas, avec `state`, `questions`,
`expected` (étiquette pour `choice`, nombre pour `score`, booléen pour `noul`), plus `language`
et `tags` pour le découpage.

- source éditable : `data/tickets.source.jsonl`
- dataset canonique (généré) : `data/tickets.eval.jsonl` — via `python tools/build_dataset.py`

### Backends comparés

| backend | poids | description |
|---|---|---|
| `laya` | oui | le vrai `laya.Router` (routage automatique par langue) |
| `heuristic` | non | moteur **à mots-clés**, le fallback qu'une équipe écrit à la main (baseline « domaine ») |
| `majority` | non | toujours la classe majoritaire (ligne de référence de Laya) |
| `random` | non | aléatoire uniforme (ligne de référence de Laya) |

### Métriques (identiques à `laya.evals`)

`choice_accuracy`, `noul_accuracy`, `score_mae`, `score_within_0.5`, `mean_confidence`,
`ece` (15 bins), `brier`, `aurc`, `selective_accuracy@50` / `@80`, `latency_p50_ms` /
`latency_p95_ms`, `cost_per_decision_p50_ms` — plus des **slices** par `language`, par `qid` et
par `tag`. Le calcul vit dans [`layabench/metrics.py`](layabench/metrics.py) et n'utilise que
numpy (comme la doc Laya), donc il tourne **sans poids**.

---

## 3. Résultats mesurés

Machine : **CPU** uniquement, `torch 2.15.0+cpu`, `laya 0.4.31`, 33 tickets / 132 décisions,
un warmup d'un forward pass pour ne pas imputer le chargement du modèle à la latence.

### Vue d'ensemble

| backend | choice_acc | noul_acc | score_mae | ece ↓ | brier ↓ | aurc ↓ | sel@50 | p50 (ms) ↓ | p95 (ms) ↓ |
|---|---|---|---|---|---|---|---|---|---|
| `heuristic` | 0.939 | 0.970 | 0.545 | 0.127 | 0.043 | 0.021 | 0.979 | 0.02 | 0.04 |
| `heuristic` *[noul→choice]* | 0.939 | 0.970 | 0.545 | 0.256 | 0.109 | 0.022 | 0.979 | 0.02 | 0.03 |
| **`laya` (CPU)** | **0.909** | **0.879** | **0.567** | **0.070** | **0.075** | **0.032** | **0.960** | **164.7** | **498.7** |
| `laya` *[noul→choice]* | 0.909 | 0.848 | 0.567 | 0.079 | 0.095 | 0.040 | 0.980 | 160.2 | 493.4 |
| `majority` | 0.485 | 0.773 | 0.455 | 0.000 | 0.200 | 0.254 | 0.773 | 0.001 | 0.006 |
| `random` | 0.303 | 0.500 | 0.848 | 0.066 | 0.250 | 0.566 | 0.434 | 0.003 | 0.011 |

Les rapports complets sont dans `results/*.json` (données brutes) et `results/*.md` (résumé).

### Par langue — backend `laya`

| langue | choice_acc | noul_acc | score_mae | ece | n décisions |
|---|---|---|---|---|---|
| `de` | 0.714 | 0.929 | 0.469 | 0.141 | 28 |
| `en` | 1.000 | 0.850 | 0.607 | 0.134 | 40 |
| `es` | 1.000 | 0.857 | 0.625 | 0.106 | 28 |
| `fr` | 0.875 | 0.875 | 0.595 | 0.067 | 32 |
| `hi` | 1.000 | 1.000 | 0.225 | 0.012 | 4 |

### Par question — backend `laya`

| question | type | métrique | valeur |
|---|---|---|---|
| `department` | choice | `choice_accuracy` | 0.909 |
| `urgency` | score | `score_mae` | 0.567 |
| `churn_risk` | noul | `noul_accuracy` | 0.818 |
| `refund_requested` | noul | `noul_accuracy` | 0.939 |

### Routage automatique (aucun forward pass)

```
I was charged twice for my March subscription…            english       English Latin text
J'ai été facturé deux fois pour mon abonnement de mars…   multilingual  Latin script but language looks like 'fr', not English
Mir wurde der Betrag zweimal abgebucht…                   multilingual  Latin script but language looks like 'de', not English
Me cobraron dos veces este mes…                           multilingual  Latin script but language looks like 'es', not English
{"body": "मुझसे दो बार शुल्क लिया गया…"}                    multilingual  non-Latin script (devanagari, 82% of letters)…
Quero cancelar                                            multilingual  Latin script, language not identified … using default
```

Le `Router` place l'anglais sur `english`, tout le reste sur `multilingual`, et bascule sur le
`default` quand un texte latin très court ne porte aucune information de langue — exactement le
comportement décrit par la doc. Reproductible avec `python tools/routing_demo.py`.

---

## 4. Ce que le benchmark montre

- **H1 — oui, mais c'est une base à affiner.** En **zero-shot**, sur un domaine très spécifique,
  Laya atteint `choice_accuracy` 0.909 et `noul_accuracy` 0.879 sans aucun entraînement : très
  au-dessus de `majority` (0.485 / 0.773) et `random` (0.303 / 0.500). Il **égale presque** le
  moteur à mots-clés que nous avons écrit à la main *pour ce domaine précis* — un avantage
  déloyal, puisque la baseline `heuristic` est littéralement taillée sur ces tickets, alors que
  Laya ne voit que des poids publics. La carte de modèle est explicite : les checkpoints de base
  sont proches du hasard sur `typed-decisions` zero-shot et **servent de base à fine-tuner** ;
  c'est cohérent avec ce que l'on observe.
- **H2 — la confiance est exploitable.** `ece` 0.070, `aurc` 0.032 et surtout
  `selective_accuracy@50` 0.960 : en n'acceptant que la moitié la plus confiante, on monte
  à 96 % de justesse. C'est le signal qui compte pour une passe automatique — la doc recommande
  de gater sur `confidence` (et non sur `action.act_probability`, sans signal utile).
- **H3 — le contournement `noul` n'aide pas ici.** Reposer `churn_risk` / `refund_requested` en
  `choice` à clés neutres fait *baisser* `noul_accuracy` de 0.879 à 0.848 et `ece` de 0.070 à
  0.079. Le problème documenté (le `noul` qui « suit ses étiquettes ») **ne se matérialise pas**
  sur ces données — d'où l'intérêt de le mesurer plutôt que de l'appliquer systématiquement.
- **La primitive `score` est la plus faible.** `score_mae` 0.567 et `score_within_0.5` seulement
  0.455 : l'urgence est la décision la moins bien classée, ce que la carte de modèle annonce déjà
  (`score` = primitive la plus faible). Une architecture de prod utiliserait ici une première
  décision `choice` grossière (basse/moyenne/haute) ou un head ré-entraîné.
- **Multilingue en un seul artefact.** Un seul `Router` couvre EN/FR/DE/ES/HI avec un routage
  transparent ; le point faible mesuré est l'`choice_accuracy` allemand (0.714).

---

## 5. Reproduire

```bash
# dans /appli/laya_test
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python --index-url https://download.pytorch.org/whl/cpu torch
uv pip install --python .venv/bin/python laya          # moteur Laya (0.4.31)

# 1) construire et vérifier le jeu de données (sans poids)
.venv/bin/python tools/build_dataset.py
.venv/bin/python -m layabench validate data/tickets.eval.jsonl

# 2) baselines sans poids
for b in heuristic majority random; do
  .venv/bin/python -m layabench run --data data/tickets.eval.jsonl --backend $b \
      --json results/$b.json --markdown results/$b.md
done

# 3) le vrai moteur (télécharge les checkpoints au 1er appel), puis la variante noul→choice
.venv/bin/python -m layabench run --data data/tickets.eval.jsonl --backend laya \
    --device cpu --warmup --json results/laya_cpu.json --markdown results/laya_cpu.md
.venv/bin/python -m layabench run --data data/tickets.eval.jsonl --backend laya \
    --device cpu --warmup --noul-as-choice \
    --json results/laya_cpu_noulchoice.json --markdown results/laya_cpu_noulchoice.md

# 4) comparer un candidat à une baseline (gate de CI : sortie non nulle si régression)
.venv/bin/python -m layabench compare results/laya_cpu.json --baseline results/heuristic.json

# bonus : décisions de routage, sans forward pass
.venv/bin/python tools/routing_demo.py
```

Pour un GPU, remplacer `--index-url .../cpu` par le build CUDA et passer `--device cuda`
(la machine de test possède une RTX 4070 ; les chiffres ci-dessus sont des chiffres CPU).

---

## 6. Arborescence

```
laya_test/
├── README.md
├── pyproject.toml                 # paquet `layabench` (numpy requis, laya en extra)
├── layabench/
│   ├── schema.py                  # la politique de questions + le loader d'évalset
│   ├── metrics.py                 # métriques (miroir de laya.evals, numpy seul)
│   ├── backends.py                # laya | heuristic | majority | random
│   ├── harness.py                 # exécute un dataset contre un backend
│   ├── report.py                  # rendu Markdown + diff de rapports
│   └── cli.py                     # `python -m layabench run|validate|compare`
├── data/
│   ├── tickets.source.jsonl          # source éditable (33 tickets écrits à la main)
│   ├── tickets.eval.jsonl            # dataset canonique laya-evals (33 lignes)
│   ├── tickets100.*                  # 33 écrits + 67 générés (100 lignes)
│   ├── tickets300.*                  # 33 écrits + 300 générés / 60 templates (333 lignes)
│   ├── train.jsonl / test.jsonl      # split 33 (23/10)
│   ├── train100.jsonl / test100.jsonl    # split 100 (79/21, stratifié)
│   ├── train300.jsonl / test300.jsonl    # split 300 par TEMPLATE (258/75, formulations inédites)
│   └── train300-small.jsonl          # sous-ensemble 65 (courbe de données)
├── tools/
│   ├── build_dataset.py              # source → dataset canonique (--source / --out)
│   ├── gen_dataset.py                # 33 écrits + 67 générés = 100 tickets
│   ├── gen_dataset_big.py            # variante à templates (300 tickets, `tpl`)
│   ├── make_split.py                 # split déterministe (explicit | stratified | template)
│   ├── finetune.sh                   # fine-tune via le CLI laya-train (33 tickets)
│   ├── train_laya.py                 # fine-tune via l'API Python (GPU, calib_frac, loss)
│   ├── make_onepager.py              # génère laya_onepager.pdf (reportlab, 1 page)
│   ├── serve_model.py                # petit serveur local + UI (endpoints /predict /guide /models /onepager.pdf)
│   ├── serve.sh                      # démarre / redémarre le serveur de test (port 9999 par défaut)
│   ├── tester.html                   # page web : comparaison sans FT / avec FT, guide des catégories
│   └── routing_demo.py               # affiche les décisions du Router
├── checkpoints/                      # t300-softce conservé (le plus efficient) ; autres régénérables via tools/
├── blog/                             # article Medium : medium-laya-fr.md + assets/ (couverture, tableau) + PUBLISHING.md
├── laya_onepager.pdf                 # one-pager de synthèse (présentation + résultats)
└── results/                          # rapports générés (JSON + Markdown)
```

> Le backend `agent` du harness évalue **un** checkpoint (`laya.load` + `agent.predict`), ce qui
> permet de scorer un modèle fine-tuné à côté des checkpoints publics : voir section 8.


---

## 7. Limites honnêtes

- **Jeu de données minuscule (33 tickets).** Suffisant pour démontrer le harnais et les
  tendances, pas pour une conclusion statistique. À remplacer par un vrai set labellisé
  (la doc Laya montre comment brancher un `baseline.json` et un gate de CI).
- **La baseline `heuristic` est taillée sur ce domaine** (mots-clés choisis pour ces tickets) :
  c'est un plafond optimiste pour des règles manuelles, pas un concurrent « équitable ».
  L'exercice utile est de **fine-tuner Laya** sur le même split, puis de rejouer le benchmark.
- **Latences CPU seulement.** ~165 ms/ticket sur CPU (p95 ~0.5 s) contre les ~33 ms annoncés
  sur GPU ; ce sont les temps « bout-en-bout » du harnais (tokenisation incluse).
- **Les checkpoints de base sont sur-confiants sur leurs propres benchmarks** (la carte annonce
  ECE 0.466 → 0.081 après refit d'une température). Notre ECE de 0.070 est mesuré sur *ce* petit
  set, pas une garantie : **recalibrer la température sur vos données** avant de faire confiance
  aux probabilités.
- **`noul` peut suivre ses étiquettes** au lieu de l'état (issue documentée) ; notre H3 montre
  que ce n'est pas systématique — à vérifier cas par cas, comme ici.
- **Choix à cardinalité élevée.** Au-delà de ~20 options, la précision s'effondre si le budget de
  prompt par option est trop faible ; notre `department` n'a que 3 options, ce qui masque cette
  limite.

---

## 8. Suite logique : fine-tuner sur nos labels

La section 4 disait « c'est une base à fine-tuner ». On l'a fait, avec l'API officielle
`laya-train` (l'équivalent Python est `laya.train.finetune`).

### Protocole

- **Split déterministe et documenté** (`tools/make_split.py`) : **23 train / 10 test**. Le test
  est choisi (pas tiré au hasard) pour couvrir les 5 langues, les 3 départements, et garder
  **4 des 7 menaces de churn** — sinon on ne pourrait pas mesurer le point faible.
- **Base `multilingual`** (mmBERT), `--loss soft-ce --label-smoothing 0.1`, sur **CPU**.
- **Deux variantes** : encodeur **gelé** (têtes seules, rapide) et **complet**.

### Résultats — sur les 10 tickets tenus à l'écart

| run | choice_acc | noul_acc | score_mae ↓ | ece ↓ | aurc ↓ | sel@50 |
|---|---|---|---|---|---|---|
| avant — `Router` (prod) | 0.800 | 0.800 | 0.508 | 0.118 | 0.100 | 0.867 |
| avant — base `multilingual` | 0.800 | 0.800 | 0.573 | 0.156 | 0.070 | 0.933 |
| après — fine-tune **gelé** | 0.900 | 0.800 | 0.550 | 0.123 | 0.067 | 0.933 |
| après — fine-tune **complet** | **1.000** | **0.900** | **0.336** | **0.120** | **0.021** | **1.000** |

Par question, le point sensible `churn_risk` : **0.60 → 0.60 → 0.80** (base → gelé → complet).

### Ce que le fine-tuning montre

- **Le fine-tune complet améliore tout**, proprement : `choice` 0.80→1.00, `urgency` MAE
  0.573→0.336, `ece` 0.156→0.121, `aurc` 0.070→**0.021**, `selective@50` 0.933→1.000. La thèse de
  la doc se vérifie sur nos données : *fine-tuning is where most of the value is*.
- **Geler l'encodeur ne suffit pas.** En entraînant seulement les têtes : +0.10 en `choice` mais
  `noul` inchangé. La spécialisation utile passe par l'**encodeur**.
- **`churn` reste le point faible** (0.60→0.80) : avec **3 exemples positifs** de churn à
  l'entraînement, même un fine-tune complet ne répare pas la négation. La leçon est nette —
  ça se règle avec **plus de données labellisées**, pas avec plus d'époques.
- **Calibration : il faut un vrai set dédié.** Avec 33 tickets, la tranche de calibration fait
  moins de 10 items par type → `laya-train` **n'ajuste pas** les températures (elles restent 1.0,
  avertissement explicite). L'ECE baisse quand même, car la tête devient intrinsèquement moins
  sur-confidente.

### Reproduire le fine-tuning

```bash
# split + fine-tune (encodeur gelé) + éval « avant/après » de Laya
bash tools/finetune.sh

# variante fine-tune complet
FREEZE="" bash tools/finetune.sh

# évaluer le checkpoint avec notre harness, puis comparer à la base
.venv/bin/python -m layabench run --data data/test.jsonl --backend agent \
    --checkpoint checkpoints/tickets-ft-full --device cpu --warmup \
    --json results/after_ft_full_test.json --markdown results/after_ft_full_test.md
.venv/bin/python -m layabench compare results/after_ft_full_test.json \
    --baseline results/before_multilingual_test.json
```

Le checkpoint produit se charge comme n'importe quel autre : `laya.load("checkpoints/tickets-ft-full")`.

---

## 9. Passage à l'échelle : 100 tickets, fine-tune complet **sur GPU**

Suite du 8 : le jeu de données passe à **100 tickets** et l'entraînement (complet) tourne
**sur GPU** — RTX 4070 12 Go, `torch 2.15.0+cu132`.

### Ce qui change

- **100 tickets** : les 33 écrits à la main **+ 67 générés** par `tools/gen_dataset.py`
  (banques de phrases par langue ; labels dérivés des composants assemblés).
  *Limite assumée : ces 67 sont synthétiques et plus répétitifs que les 33 ; le jeu reste un
  ensemble de démonstration, pas un benchmark public.*
- **Split stratifié** (`--strategy stratified`) : **79 train / 21 test** (~20 %, toutes langues).
- `tools/train_laya.py` (API Python `laya.train.finetune`) avec **`calib_frac=0.25`** : la
  tranche de calibration devient assez grande (79 items) pour **ajuster réellement** les
  températures (T ≈ 0.93 / 1.11 / 1.10).
- **Fine-tune complet** (encodeur non gelé), 15 époques, `--micro-batch 16`.

### Résultats — 21 tickets tenus à l'écart (84 décisions)

| métrique | base `multilingual` | fine-tuné (100, GPU) | delta |
|---|---|---|---|
| `choice_accuracy` | 0.7143 | **0.9048** | **+0.1905** |
| `noul_accuracy` | 0.8333 | **0.9524** | **+0.1190** |
| `score_mae` ↓ | 0.8234 | **0.3326** | **-0.4908** |
| `score_within_0.5` | 0.1905 | **0.7619** | **+0.5714** |
| `ece` ↓ | 0.1335 | **0.1001** | -0.0334 |
| `brier` ↓ | 0.1351 | **0.0316** | -0.1035 |
| `aurc` ↓ | 0.0595 | **0.0028** | -0.0567 |
| `selective_accuracy@50` | 0.9688 | **1.000** | +0.0312 |
| `selective_accuracy@80` | 0.8824 | **1.000** | +0.1176 |
| `latency_p50_ms` ↓ | 23.5 | **18.3** | -5.3 |

Par question :

| question | base | fine-tuné |
|---|---|---|
| `churn_risk` (noul) | 0.714 | **1.000** |
| `department` (choice) | 0.714 | **0.905** |
| `refund_requested` (noul) | 0.952 | 0.905 |
| `urgency` (MAE) | 0.823 | **0.333** |

### Ce que ça montre

- **Le passage à l'échelle corrige le point faible** : `churn_risk` passe de **0.714 à 1.000**.
  C'est exactement le signal que le run à 33 tickets (section 8) n'arrivait pas à réparer — la
  conclusion du 8 (« ça se règle avec plus de données ») se vérifie.
- **Amélioration partout** : `choice` +0.19, `urgency` MAE −0.49, `aurc` 0.060→**0.003**,
  `selective@80` 0.88→**1.00**. Seul `refund` recule très légèrement (0.952→0.905) — bruit sur
  21 tickets.
- **La calibration s'ajuste enfin**, parce que `calib_frac=0.25` donne assez d'items par type
  (contrairement aux 33 tickets où les températures restaient bloquées à 1.0).
- **Latence GPU ~18–24 ms/ticket**, cohérente avec les ~33 ms annoncés (contre ~165 ms sur CPU).

### Reproduire

```bash
# 100 tickets : 33 écrits + 67 générés -> dataset -> split stratifié
.venv/bin/python tools/gen_dataset.py
.venv/bin/python tools/build_dataset.py --source data/tickets100.source.jsonl --out data/tickets100.eval.jsonl
.venv/bin/python tools/make_split.py --data data/tickets100.eval.jsonl --strategy stratified \
    --holdout-frac 0.2 --train-out data/train100.jsonl --test-out data/test100.jsonl

# fine-tune COMPLET sur GPU (encodeur non gelé, calib_frac=0.25)
.venv/bin/python tools/train_laya.py --data data/train100.jsonl --eval data/test100.jsonl \
    --out checkpoints/tickets100-ft --base multilingual --device cuda \
    --epochs 15 --micro-batch 16 --grad-accum 1 --calib-frac 0.25

# évaluer « avant » (base) puis « après » (fine-tuné), sur le même test
.venv/bin/python -m layabench run --data data/test100.jsonl --backend agent \
    --checkpoint convaiinnovations/laya --subfolder multilingual --device cuda --warmup \
    --json results/before100_multilingual_test.json
.venv/bin/python -m layabench run --data data/test100.jsonl --backend agent \
    --checkpoint checkpoints/tickets100-ft --device cuda --warmup \
    --json results/after100_ft_test.json
.venv/bin/python -m layabench compare results/after100_ft_test.json \
    --baseline results/before100_multilingual_test.json
```

---

## 10. Étude : généralisation sur formulations inédites, `soft-ce` vs `rlcd`, courbe de données

Objectif : répondre proprement à deux questions qu'un ingénieur se pose vraiment —
**quelle fonction de perte ?** et **combien de données ?** — en s'assurant que le gain est de la
**généralisation**, pas de la mémorisation.

### Protocole

- **333 tickets** = 33 écrits à la main + 300 générés, répartis en **60 templates**
  (`tools/gen_dataset_big.py`). Chaque template = une formulation d'un (langue, département).
- **Split par template** (`make_split.py --strategy template`) : on tient à l'écart **une
  réalisation entière** par (langue, département). Le test utilise donc des **formulations jamais
  vues à l'entraînement** → 258 train / 75 test.
- **3 runs GPU** identiques sauf la variable étudiée : `soft-ce` (300), `rlcd` (300),
  `soft-ce` sur 65 tickets. Même test300 pour tous.
- Évaluation avec **notre harness** (300 décisions) à côté du rapport interne de Laya.

### Résultats (notre harness)

| run | choice_acc | noul_acc | score_mae ↓ | ece ↓ | brier ↓ | aurc ↓ | sel@80 |
|---|---|---|---|---|---|---|---|
| base `multilingual` | 0.653 | 0.753 | 0.672 | 0.222 | 0.237 | 0.149 | 0.750 |
| FT **`soft-ce` (300)** | **0.933** | 1.000 | 0.098 | **0.067** | 0.031 | **0.004** | 0.989 |
| FT `rlcd` (300) | 0.867 | 1.000 | **0.075** | 0.092 | 0.046 | 0.008 | **0.994** |
| FT `soft-ce` (65) | 0.720 | 1.000 | 0.126 | 0.072 | 0.057 | 0.009 | 0.994 |

Par question :

| run | `churn_risk` | `department` | `refund_requested` | `urgency` (MAE) |
|---|---|---|---|---|
| base | 0.600 | 0.653 | 0.907 | 0.672 |
| FT `soft-ce` (300) | 1.000 | **0.933** | 1.000 | 0.098 |
| FT `rlcd` (300) | 1.000 | 0.867 | 1.000 | **0.075** |
| FT `soft-ce` (65) | 1.000 | 0.720 | 1.000 | 0.126 |

### Rapport interne de Laya (mêmes runs)

| run | Accuracy | ECE | Brier top-1 |
|---|---|---|---|
| `soft-ce` (300) | 0.6367 → **0.9800** | 0.2111 → 0.0686 | 0.2441 → 0.0295 |
| `rlcd` (300) | 0.6367 → 0.9667 | 0.2111 → **0.0486** | 0.2441 → 0.0362 |
| `soft-ce` (65) | 0.6367 → 0.9233 | 0.2111 → 0.0623 | 0.2441 → 0.0507 |

### Conclusions

- **Le fine-tuning généralise vraiment.** Sur des formulations **inédites**, `soft-ce` fait passer
  `choice` de 0.653 à **0.933**, `noul` à **1.000**, l'`urgency` MAE de 0.672 à **0.098** et
  l'`aurc` de 0.149 à **0.004**. Ce n'est pas de la mémorisation : le test n'a jamais vu la
  tournure de phrase.
- **`soft-ce` vs `rlcd`** : `soft-ce` gagne sur le **catégoriel** (`department` 0.933 vs 0.867) et
  la **calibration** (ECE 0.067 vs 0.092) ; `rlcd` gagne légèrement sur l'**ordinal**
  (`urgency` MAE 0.075 vs 0.098) et `sel@80`. Cohérent avec la doc Laya (0.790 vs 0.7715 sur
  typed-decisions) → **`soft-ce` par défaut**, `rlcd` si l'ordonnancement fin compte le plus.
- **Courbe de données** : à 65 tickets, `churn`/`refund` sont déjà à 1.000 ; c'est la décision
  **catégorielle** la plus difficile (`department`) qui demande du volume (0.720 → 0.933 de 65 à
  300 tickets). Autrement dit : les flags binaires s'apprennent vite, le choix multi-classe non.
- Latence ~18 ms/ticket (GPU), inchangée par le fine-tuning.

**Limite** : même avec des templates tenus à l'écart, les 300 tickets générés partagent un style ;
les valeurs absolues (0.93–0.98) restent optimistes face à du vrai trafic. Les **comparaisons
relatives** (loss, taille) sont, elles, solides.

### Reproduire

```bash
.venv/bin/python tools/gen_dataset_big.py --target 300
.venv/bin/python tools/build_dataset.py --source data/tickets300.source.jsonl --out data/tickets300.eval.jsonl
.venv/bin/python tools/make_split.py --data data/tickets300.eval.jsonl --strategy template \
    --train-out data/train300.jsonl --test-out data/test300.jsonl
awk 'NR%4==1' data/train300.jsonl > data/train300-small.jsonl     # 65-ticket courbe

for loss in soft-ce rlcd; do
  .venv/bin/python tools/train_laya.py --data data/train300.jsonl --eval data/test300.jsonl \
      --out checkpoints/t300-$loss --base multilingual --device cuda \
      --epochs 12 --micro-batch 16 --grad-accum 1 --calib-frac 0.25 --loss $loss
done
```

---

*Auteur : **CTO 3D/IA chez Atos** · dépôt : [github.com/xuarig007/laya_test](https://github.com/xuarig007/laya_test)*



