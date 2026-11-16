# Publier l'article sur Medium

Tout est prêt dans `blog/` :

| article | visuels |
|---|---|
| `medium-laya-fr.md` (français) | `assets/cover-fr.png`, `assets/results-fr.png` |
| `medium-laya-en.md` (English) | `assets/cover-en.png`, `assets/results-en.png` |

Régénérer les 4 visuels : `python tools/make_medium_assets.py`

## 1. Choisir la méthode de publication

**A. Import par URL (recommandé — Medium convertit le Markdown tout seul)**
1. Mettre `medium-laya-fr.md` dans un **gist GitHub public** (ou un dépôt) et copier son URL « raw ».
2. Aller sur **https://medium.com/p/import**, coller l'URL raw, valider.
3. Medium crée un brouillon avec titres, gras, listes et blocs de code déjà formatés.
4. Relire, ajouter les images (voir §2), les tags (§3), publier.

**B. Copier-coller direct**
Medium convertit le Markdown collé (titres, gras, listes, `code`). **Les tableaux ne passent pas** :
c'est pour ça que le tableau clé est fourni en **image** (`assets/results.png`) — colle l'image à la
place du tableau Markdown (garde le tableau Markdown pour la version GitHub/raw).

## 2. Images

| image | usage |
|---|---|
| `assets/cover-fr.png` / `cover-en.png` (1500×750) | **image de couverture** : au moment de publier, « Add a featured image » |
| `assets/results-fr.png` / `results-en.png` | à insérer **dans** l'article, à la place du tableau Markdown de l'étape 4 |

Astuce : glisse-dépose le PNG directement dans l'éditeur Medium.

## 3. Métadonnées Medium

- **Title** (≤ ~60 caractères) :
  `Laya, du zero-shot à la production : affiner un moteur de décision open source`
- **Subtitle** (la ligne en gras/italique juste après le titre, dans l'article) :
  `Trier des tickets support en 5 langues, en un seul forward pass. De 33 à 300 exemples, du CPU au GPU — avec les chiffres.`
- **Tags** (5 max) : `Machine Learning`, `NLP`, `Large Language Models`, `Python`, `Hugging Face`
- **SEO description** (facultatif) :
  `Benchmark et fine-tuning de Laya, un moteur de décision non-autorégressif, sur un cas d'usage de triage de tickets support multilingue. Résultats mesurés, du zero-shot à la production.`

### Version anglaise (`medium-laya-en.md`)

- **Title** : `Laya, from zero-shot to production: fine-tuning an open-source decision engine`
- **Subtitle** : `Routing support tickets in 5 languages in a single forward pass. From 33 to 300 examples, CPU then GPU — with the numbers, including the ones that hurt.`
- **Tags** : `Machine Learning`, `NLP`, `Large Language Models`, `Python`, `Hugging Face`
- **SEO description** : `Benchmarking and fine-tuning Laya, a non-autoregressive decision engine, on multilingual support-ticket routing — measured results, from zero-shot to production.`

## 4. Checklist avant de publier

- [ ] Retirer le bloc `<!-- ... -->` de notes en fin d'article.
- [ ] Remplacer le tableau Markdown de l'étape 4 par l'image `results.png` (si méthode B).
- [ ] Vérifier que les blocs de code sont bien en `bash`.
- [ ] Mettre `cover.png` en image de couverture.
- [ ] Relecture : les chiffres (0.933 / 1.000 / 0.098 / 0.067 / 0.004) sont cohérents dans tout l'article.
- [ ] Ajouter un **canonical link** (Paramètres de l'article → *Advanced*) si le même texte est publié ailleurs (dev.to, blog perso) — évite le contenu dupliqué.
- [ ] Créditer Laya (Convai Innovations) et lier la doc HF, comme dans la section *Ressources*.

## 5. Après publication

- Partager dans les *Discussions* du dépôt Laya (le projet référence les retours de la communauté).
- Reposter sur **dev.to** (même Markdown, mais là les tableaux passent) avec canonical → Medium.
- Répondre aux commentaires : c'est ce qui fait vivre un article technique.

## 6. Les deux langues

Les deux versions sont prêtes :

| | titre | couverture |
|---|---|---|
| EN (`medium-laya-en.md`) | *Laya, from zero-shot to production: fine-tuning an open-source decision engine* | `cover-en.png` |
| FR (`medium-laya-fr.md`) | *Laya, du zero-shot à la production : affiner un moteur de décision open source* | `cover-fr.png` |

Medium a une audience majoritairement anglophone : publier **l'anglais** d'abord donne plus de portée.
La version FR peut suivre sur le même compte, ou sur dev.to / blog perso avec un **canonical**
croisé vers Medium (et inversement) pour éviter le contenu dupliqué.

---

## 7. Profil Medium — bio et liens

**Bio de profil** (Medium → *Settings* → *Profile* → champ **Bio**, 160 caractères max) :

> CTO 3D/IA chez Atos · benchmarks, fine-tuning et mise en production de modèles de décision

Version anglaise :

> CTO 3D/IA at Atos · benchmarking, fine-tuning and shipping decision models

**Liens du profil** (*Settings* → *Profile* → comptes sociaux) :
- **GitHub** : https://github.com/xuarig007/laya_test

**Mention en fin d'article** : déjà rédigée dans les deux articles —
`À propos — CTO 3D/IA chez Atos …` et `About the author — CTO 3D/IA at Atos …`. Tu peux y ajouter ton
prénom/nom en début de ligne si tu veux signer.

> À savoir : Medium n'expose pas de champ « employeur » ; la **bio** et les **liens du profil** sont les
> deux endroits où le rôle apparaît. La mention dans l'article est le troisième (et le plus visible pour
> un lecteur qui arrive par le lien).

---

## 8. Dépannage : « Import failed — the server stopped responding »

Deux causes fréquentes, toutes deux corrigées ici :

1. **l'URL d'import est incomplète** (l'URL `refs/heads/...` se coupe facilement) ;
2. **Medium n'arrive pas à récupérer les images** : elles étaient référencées en chemins *relatifs*
   (`assets/results-en.png`), illisibles depuis l'extérieur. Elles sont maintenant en **URL absolues**
   (`https://raw.githubusercontent.com/.../assets/...png`) → Medium les télécharge pendant l'import.

Les notes internes (bloc HTML `<!-- ... -->` en fin d'article) ont aussi été retirées : elles
n'apportent rien au lecteur et peuvent perturber l'importeur.

### URL d'import exacte (à copier en entier, sans coupure)

Les tableaux sont **déjà des images** dans les articles (voir § 9) : on importe donc directement
l'article, sans variante intermédiaire :

```
EN : https://raw.githubusercontent.com/xuarig007/laya_test/main/blog/medium-laya-en.md
FR : https://raw.githubusercontent.com/xuarig007/laya_test/main/blog/medium-laya-fr.md
```

> **Cache CDN de GitHub.** `raw.githubusercontent.com` sert les fichiers avec
> `cache-control: max-age=300` : après un `git push`, l'URL raw peut renvoyer **l'ancienne version
> pendant ~5 minutes** (un paramètre `?v=2` ne contourne pas ce cache). Si l'import lit une version
> périmée, **attendre 5 minutes** et réessayer. Pour vérifier ce qui est réellement servi :
> `curl -s <url> | grep png`. L'API GitHub renvoie, elle, toujours la version à jour
> (`curl -H 'Accept: application/vnd.github.raw' https://api.github.com/repos/xuarig007/laya_test/contents/blog/medium-laya-en.md`).

> **Tableaux.** Medium n'affiche pas les tableaux Markdown : à l'import ils apparaissent en texte
> « | a | b | ». Garder le tableau-image `results-en.png` pour la comparaison clé, et supprimer (ou
> transformer en liste) les petits tableaux restants dans l'éditeur.

### Si l'import échoue encore (l'importeur de Medium est capricieux)

1. **Réessayer** — l'erreur « server stopped responding » est souvent transitoire (« Try again »).
2. **Passer par un gist** (la méthode la plus fiable) : créer un gist public sur
   [gist.github.com](https://gist.github.com) avec le contenu de `medium-laya-en.md`, puis importer
   l'URL **raw** du gist (`https://gist.githubusercontent.com/<user>/<id>/raw/...`).
3. **Coller directement dans l'éditeur Medium** : Medium convertit le Markdown au collage (titres,
   gras, listes, blocs de code). Les tableaux ne passent pas → insérer l'image `results-en.png` à la
   place. C'est la méthode la plus rapide si l'import refuse.
4. **Publier d'abord ailleurs** (dev.to, blog perso) puis importer l'**URL de la page publiée** :
   l'importeur Medium est d'abord conçu pour une page HTML publiée, pas pour un fichier brut.

### Rappel des métadonnées (reprises de la section 3)

- lecture estimée : ~9 min
- couverture : `assets/cover-en.png` (EN) / `assets/cover-fr.png` (FR)
- tags (5 max) : `Machine Learning`, `NLP`, `Large Language Models`, `Python`, `Hugging Face`

---

## 9. Les tableaux sont des images (dans les articles eux-mêmes)

Medium **n'affiche pas les tableaux Markdown** : ils s'aplatissent en texte illisible
(`runchoicecnoulbefore (base)0.8000.800…`).

Dans `blog/medium-laya-en.md` et `blog/medium-laya-fr.md`, **chaque tableau a été remplacé par une
image** :

```markdown
![Titre de la section](https://raw.githubusercontent.com/xuarig007/laya_test/main/blog/assets/table-<langue>-<slug>.png)
```

Les liens sont en **URL absolues** : Medium les télécharge à l'import, et GitHub les affiche aussi.
Onze images au total (5 tableaux par langue + le comparatif `results-*.png`).

`tools/make_table_images.py` fait la conversion :

1. détecte chaque tableau Markdown et la section au-dessus (qui devient le titre de l'image) ;
2. le rend en `blog/assets/table-<langue>-<slug>.png` — titre inclus, **gras conservé**, balisage
   (`` ` `` / `**`) nettoyé, texte long replié automatiquement ;
3. **réécrit l'article** en remplaçant le bloc tableau par le lien de l'image ;
4. supprime un tableau si une image (déjà présente juste au-dessus) le montre — pas de doublon.

Le script est **idempotent** : relancé sur un article déjà converti, il ne fait rien.

```bash
.venv/bin/python tools/make_table_images.py     # après avoir (re)mis un tableau dans un article
```

**Pour modifier un tableau** : remplacer la ligne `![...](...)` par le tableau Markdown voulu, puis
relancer le script (le nom d'image est dérivé du titre de section, donc stable). Les mêmes tableaux
restent par ailleurs en Markdown dans le `README.md` (§ 4, 8, 9, 10) et dans `results/*.json`.




