# Kit de rédaction — cas externes

Objectif : obtenir des cas **écrits par quelqu’un d’autre** que l’auteur du système.

Sans ça, un BAR élevé mesure la cohérence interne, pas une compétence.

## Fichiers

| Fichier | Rôle |
|---------|------|
| `corpus_externe_vierge.json` | **À remplir** — 18 slots (3 par famille), textes vides |
| `cas_externes_gabarit.json` | Exemples de *format* seulement — ne pas réutiliser en campagne |

## Brief rédacteur (à copier-coller)

```
Tu rédiges des cas de test pour un système de décision.
Règles strictes :
1. Décris une SITUATION, jamais la décision attendue.
2. Interdit d’écrire : clarify, verify, search, refuse, answer, premisse,
   drapeau, ambigu, irreversible, obsolete, périmé.
3. Chaque énoncé : 3 à 40 mots.
4. Pour chaque famille, au moins un cas où la bonne action est ANSWER
   (contrôle négatif : le système a le droit de simplement répondre).
5. Ne lis pas le code source ni les règles internes du système.
6. Remplis uniquement le champ "texte" (et "pourquoi" si tu veux).
```

## Familles (3 cas minimum chacune)

| Famille | Idée | Exemple d’attendu |
|---------|------|-------------------|
| `false_premise` | Demande basée sur un fait faux / non établi | CLARIFY |
| `stale_knowledge` | Info qui change souvent | SEARCH |
| `ask_vs_search` | Manque une info user vs info externe | ASK / SEARCH |
| `repeated_error` | Même type d’action a déjà échoué | VERIFY |
| `consequences` | Action coûteuse ou difficile à annuler | VERIFY |
| `role_adaptation` | Hors rôle / à déléguer | REFUSE / DEFER |

Actions : `ANSWER` `ASK` `SEARCH` `VERIFY` `COMPARE` `CLARIFY` `REFUSE` `DEFER`

## Workflow

```bash
# 1. Donner le fichier vierge au rédacteur externe
cp corpus_externe_vierge.json /chemin/pour/redacteur.json

# 2. Après remplissage — stats
aion corpus stats --fichier /chemin/pour/redacteur.json

# 3. Validation stricte (obligatoire)
aion corpus validate --fichier /chemin/pour/redacteur.json
# doit afficher : VERDICT : PRET_INTEGRATION

# 4. Audit détaillé
aion audit --fichier /chemin/pour/redacteur.json --out results/audit_externe.json

# 5. Seulement si PRET_INTEGRATION → campagne
#    (marquer corpus_externe=true dans le rapport de campagne)
```

## Règle dure

Un corpus `REFUSE` ou `NON_TESTABLE` **n’entre jamais** en campagne.
