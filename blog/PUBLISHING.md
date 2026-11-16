# Publier l'article sur Medium

Tout est prêt dans `blog/` : l'article (`medium-laya-fr.md`) et deux visuels
(`assets/cover.png`, `assets/results.png`).

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
| `assets/cover.png` (1500×750) | **image de couverture** : au moment de publier, « Add a featured image » |
| `assets/results.png` | à insérer **dans** l'article, à la place du tableau Markdown de l'étape 4 |

Astuce : glisse-dépose le PNG directement dans l'éditeur Medium.

## 3. Métadonnées Medium

- **Title** (≤ ~60 caractères) :
  `Laya, du zero-shot à la production : affiner un moteur de décision open source`
- **Subtitle** (la ligne en gras/italique juste après le titre, dans l'article) :
  `Trier des tickets support en 5 langues, en un seul forward pass. De 33 à 300 exemples, du CPU au GPU — avec les chiffres.`
- **Tags** (5 max) : `Machine Learning`, `NLP`, `Large Language Models`, `Python`, `Hugging Face`
- **SEO description** (facultatif) :
  `Benchmark et fine-tuning de Laya, un moteur de décision non-autorégressif, sur un cas d'usage de triage de tickets support multilingue. Résultats mesurés, du zero-shot à la production.`

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

## 6. (Optionnel) Version anglaise

Medium a une audience majoritairement anglophone ; une traduction EN élargit nettement la portée.
Le même Markdown + les mêmes images suffisent (titres, tags et sous-titre à traduire).
