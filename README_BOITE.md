# Boîte à outils — tester honnêtement son propre système

Quatre outils qui marchent, testés, exécutables en cinq minutes. Ils servent à
répondre à des questions qu'on ne se pose en général qu'après avoir perdu six
mois.

| Outil | Question à laquelle il répond | Commande |
|---|---|---|
| **Audit de corpus** | Mon banc de test peut-il seulement porter un résultat ? | `aion audit --fichier cas.json` |
| **Pré-enregistrement** | Mes seuils sont-ils gelés, et puis-je le prouver ? | `aion preenreg --verifier rapport.json` |
| **Suite MARTEAU** | Que se passe-t-il quand j'attaque mon propre code ? | `pytest tests/test_marteau.py` |
| **Le Doute** | Comment faire écrire des cas de test par quelqu'un d'autre ? | ouvrir `outils/le-doute.html` |

Le tout en Python pur, sans dépendance, MIT.

## Démarrage

```bash
cd code/aion
pip install -e ".[dev]"
pytest -q          # 78 tests
aion audit         # sur le corpus d'exemple
```

## 1. Audit de corpus — l'outil le plus utile des quatre

Il répond avant toute mesure : **est-ce que mon banc de test mesure quelque
chose ?** Deux contrôles font l'essentiel du travail.

**Ablation mot à mot.** Il retire chaque mot de l'énoncé, un par un, et regarde
si la décision bascule. Un cas qui tient à un seul mot ne teste pas une
compétence, il teste la présence de ce mot.

**Contrôle négatif obligatoire.** Chaque famille de cas doit contenir au moins
un exemple où le comportement naïf est le bon. Sans ça, le banc récompense un
système qui refuse tout.

Il refuse aussi les énoncés qui contiennent leur propre réponse, les doublons,
et les longueurs aberrantes. Format d'entrée :

```json
{"cas": [{"id": "x-01", "famille": "consequences",
          "texte": "Passe la commande chez le fournisseur habituel",
          "attendu": "VERIFY", "pourquoi": "commande irréversible"}]}
```

Sortie : `TESTABLE` ou `NON TESTABLE`, avec la liste des problèmes et le code de
sortie qui va avec (utilisable en CI).

## 2. Pré-enregistrement — rendre la triche visible

Un fichier JSON contient hypothèse, seuils et règle de décision. L'outil calcule
son empreinte SHA-256 et l'inscrit dans chaque rapport de campagne.

Modifier un seuil après avoir vu un résultat change l'empreinte et rend toutes
les campagnes antérieures **non conformes**. On ne s'empêche pas de tricher —
on rend la triche visible dans un diff.

`aion preenreg --verifier` rend aussi la décision go / simplifier / no-go, en
marquant explicitement **non opposable** toute décision issue d'une campagne qui
ne remplit pas ses propres conditions.

## 3. MARTEAU — attaquer son propre code

Un patron de suite adverse, avec une règle qui change tout : **les failles qu'on
décide de ne pas corriger sont verrouillées par un test**, nommé `test_faille_*`,
pour rester visibles au lieu de s'effacer dans le silence.

## 4. Le Doute — faire écrire les cas par quelqu'un d'autre

Un jeu de dix minutes, jouable au téléphone, qui produit un fichier de cas au
format de l'audit. Les règles de validité sont devenues des règles du jeu :
deux pièges et une carte honnête par manche, mots interdits refusés en direct.
Aucune compétence technique requise — c'est le but.

## Ce que ces outils ont trouvé, sur le projet qui les a produits

Preuve qu'ils trouvent des choses réelles, pas des principes :

- **6 failles dans le kernel**, dont une qui laissait une croyance devenir une
  preuve, et une qui contournait le seuil d'approbation humaine en rendant le
  coût non mesurable (`NaN > seuil` vaut `False`).
- **13 cas de test sur 18 tenaient à un seul mot.** Le banc mesurait un lexique.
- **Score passé de 1.00 à 0.50** dès que le système a dû lire l'énoncé au lieu
  de recevoir des indices posés à la main.
- **Campagne déclarée non conforme** par le pré-enregistrement, alors que le
  chiffre brut était flatteur.

Chaque constat est reproductible avec les commandes ci-dessus.

## Le reste du code

`code/aion` contient aussi un kernel déterministe : journal append-only avec
chaîne de hash, vérification rendant `PROOF / FAIL / UNKNOWN / CONFLICT`, arbitre
de décision, moteur de sélection d'action. **Il n'a rien de nouveau** — c'est de
l'event sourcing et de la prédiction sélective, tous deux largement publiés
(voir `METHODE.md` §6). C'est une implémentation propre et testée, pas une
contribution. Prends-la si elle t'épargne du temps.

MIT.
