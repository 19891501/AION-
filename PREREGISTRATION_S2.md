# PRÉ-ENREGISTREMENT S2 — Campagne réelle

**Statut : FROZEN**  
**Date de gel : 2026-08-26**  
**Version protocole : 2.0**

Ce document est figé **avant** tout appel API payant.  
Toute modification postérieure change les empreintes et rend la campagne **NON CONFORME**.

---

## 1. Empreintes (verrou)

| Élément | Valeur |
|---------|--------|
| **Corpus (IDs des 20 cas)** | `dccc6774fc0f2ab7` |
| **Pré-enregistrement JSON** | `d2fc38c0d4146d4181f200e36266582cefd8e32030ff37548a0af9de6c87db77` |
| **Protocole (ce fichier)** | gelé à la date ci-dessus |

Commande de vérification :
```bash
aion preenreg
aion preenreg --verifier results/<campagne>.json
```

---

## 2. Hypothèses

**H0 (nulle)**  
Sur le corpus actuel (20 cas, rédigés par l’auteur), en entrée `paraphrase`,  
l’architecture AION n’améliore pas le BAR au-delà de l’étendue de mesure  
par rapport à SCAFFOLD (contrôle décisif) et à RAW.

**H1**  
AION dépasse SCAFFOLD d’un écart de BAR ≥ 0,10 **et**  
dépasse RAW d’un écart de BAR ≥ 0,15,  
avec un taux de faux succès ≤ 0,15,  
sur au moins un modèle réel, en entrée `paraphrase`.

> H0 est le résultat attendu par défaut.  
> Une confirmation de H0 est un résultat publiable.

---

## 3. Population et protocole

| Paramètre | Valeur gelée |
|-----------|--------------|
| Nombre de cas | 20 (corpus actuel) |
| Rédacteur des cas | Auteur du système (limitation connue) |
| Entrée de référence | `paraphrase` |
| Extracteur | `llm` (drapeaux lus par le modèle) |
| Répétitions | 20 |
| Bras | RAW · SCAFFOLD · AION |
| Providers autorisés | `anthropic` · `openai` · `grok` |
| Budget maximal d’appels | 800 par campagne complète |
| Coût estimé maximal | documenté dans le rapport |

**Limitation assumée :**  
Le corpus n’est pas externe. Tout résultat sera donc annoté  
`corpus_externe: false` et ne pourra pas être opposé comme preuve définitive  
de généralisation. Il sert uniquement à obtenir le **premier chiffre réel**.

---

## 4. Métriques (définies avant toute mesure)

| Métrique | Définition | Source code |
|----------|------------|-------------|
| **BAR** | Behavioral Appropriateness Rate = actions correctes / total | `metrics.Compteurs.bar` |
| **FSR** | Taux de faux succès (répondre là où il fallait arbitrer) | `metrics.Compteurs.taux_faux_succes` |
| **Stabilité** | Écart-type du BAR sur 20 répétitions | `Rapport.bar_ecart_type` |
| **Amplitude** | BAR max − BAR min sur 20 répétitions | calculé dans `verifier` |
| **Échecs parse** | Sorties modèle non interprétables | `Rapport.echecs_parse` |
| **Appels** | Nombre d’appels modèle (extraction) | `Rapport.appels_extraction` |

---

## 5. Seuils de conformité (S2)

| Critère | Seuil | Commentaire |
|---------|-------|-------------|
| Écart AION − RAW | ≥ 0,15 | Plus bas que le pré-enregistrement v1 (0,20) car corpus non externe |
| Écart AION − SCAFFOLD | ≥ 0,10 | Contrôle décisif |
| Faux succès AION | ≤ 0,15 | Légèrement relâché (corpus fragile) |
| Écart-type BAR (modèle) | ≤ 0,12 | Stabilité minimale acceptable |
| Amplitude BAR | ≤ 0,30 | |
| Échecs parse | ≤ 30 | |
| Appels max | ≤ 800 | Budget dur |

---

## 6. Règle de décision (automatique)

```
si écart AION-RAW < 0,10          → NO_GO
si écart AION-RAW < 0,15          → SIMPLIFIER
sinon (et FSR ≤ 0,15 + stabilité) → GO
```

- **GO** : l’architecture est gardée et étendue  
- **SIMPLIFIER** : garder VERITAS + ledger, revoir la table de règles  
- **NO_GO** : publier le résultat négatif et arrêter l’architecture actuelle

Un résultat NO_GO est **publié tel quel**.  
Il n’est pas un échec du projet ; c’est un succès méthodologique.

---

## 7. Traitement des échecs et non-conformités

1. Si l’empreinte du pré-enregistrement a changé → campagne **NON CONFORME**
2. Si le corpus a été modifié → campagne **NON CONFORME**
3. Si le nombre de répétitions < 20 → campagne **NON CONFORME**
4. Si le provider n’est pas dans la liste autorisée → campagne **NON CONFORME**
5. Un bras instable (échec des 20 contrôles) ne produit **aucun verdict**

---

## 8. Engagements

1. Aucun seuil de ce document ne sera modifié après avoir vu un résultat.
2. Toute modification change l’empreinte → les campagnes antérieures deviennent non conformes (c’est voulu).
3. Le premier résultat, quel qu’il soit, est publié.
4. Aucun nouveau composant d’architecture avant ce premier chiffre réel.

---

## 9. Commande de lancement (après gel)

```bash
# Vérifier le gel
aion preenreg
aion audit

# Micro-campagne de validation du circuit (5 cas max, 3 reps) — optionnelle
# puis campagne complète :

export ANTHROPIC_API_KEY=...   # ou GROK_API_KEY / OPENAI_API_KEY

aion bench \
  --provider anthropic \
  --entree paraphrase \
  --extracteur llm \
  --reps 20 \
  --budget-appels 800 \
  --cout-appel 0.01 \
  --out results/s2_anthropic_$(date +%Y%m%d).json
```

---

## 10. Statut

```
STATUS: FROZEN
DATE: 2026-08-26
CORPUS_HASH: dccc6774fc0f2ab7
CASES: 20
REPS: 20
ENTREE: paraphrase
EXTRACTEUR: llm
BUDGET_MAX_APPELS: 800
```

Rien ne doit pouvoir modifier silencieusement ces paramètres pendant la campagne.
