# Appliquer ça à ton projet — 15 minutes

Aucune de ces étapes ne suppose que ton projet ressemble à celui d'origine.

## Minute 0-3 — installer et voir tourner

```bash
cd code/aion && pip install -e ".[dev]"
aion audit                  # exemple fourni : verdict + alertes
pytest tests/test_marteau.py -q
```

## Minute 3-8 — auditer TON banc de test

Exporte tes cas de test au format attendu — un fichier, cinq champs :

```json
{"cas": [
  {"id": "t-01",
   "famille": "<le type de situation que ce cas teste>",
   "texte": "<la demande, écrite comme un utilisateur l'écrirait>",
   "attendu": "<ANSWER|ASK|SEARCH|VERIFY|COMPARE|CLARIFY|DEFER|REFUSE>",
   "pourquoi": "<une ligne>"}
]}
```

```bash
aion audit --fichier tes-cas.json
```

Ce que tu vas probablement découvrir, dans l'ordre de fréquence :

1. Une famille sans contrôle négatif — ton banc récompense la sur-prudence.
2. Des cas qui tiennent à un seul mot — tu mesures un lexique.
3. Un énoncé qui contient sa propre réponse.

Si ton système n'a pas de « familles », mets-en une seule : les contrôles
d'ablation et de fuite fonctionnent quand même.

## Minute 8-12 — geler tes seuils avant de mesurer

Copie `code/aion/preenregistrement.json`, remplace les seuils par les tiens,
puis :

```bash
aion preenreg               # affiche les critères + l'empreinte
```

Commite le fichier. Le commit horodate le gel mieux qu'une date écrite à la
main. Après ta première campagne, tout changement de seuil devient détectable.

**Le seul moment où tu peux honnêtement choisir tes seuils, c'est maintenant.**

## Minute 12-15 — écrire ta première attaque

Ouvre `code/aion/tests/test_marteau.py` et copie le patron. Une attaque utile
répond à : *quelle entrée ferait passer mon système à côté de son propre garde-fou ?*

Trois pistes qui ont fonctionné ici, transposables presque partout :

- **Valeurs non finies.** `NaN`, `inf`, négatifs, zéro. En Python, toute
  comparaison avec `NaN` est fausse : un seuil se contourne sans effraction.
- **Escalade d'état.** Un objet peut-il passer d'« hypothèse » à « vérifié »
  sans que rien ne le justifie ?
- **Bruit de surface.** Ajoute « Bonjour, » devant l'entrée. Si le résultat
  change, ton système lit la forme et pas le fond.

Quand une attaque réussit et que tu décides de ne pas corriger : garde le test,
nomme-le `test_faille_*`, écris dans sa docstring pourquoi tu ne corriges pas.

## Et ensuite

`METHODE.md` contient les sept étapes complètes, dont les deux qui coûtent le
plus cher à sauter : séparer ce qu'on donne au système de ce qu'il doit trouver
(étape 4), et chercher l'antériorité des **combinaisons** et pas seulement des
composants (étape 6).
