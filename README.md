# AION — noyau

Kernel de confiance **déterministe** (ARCHÉ + VERITAS + Arbitre + Behavior Engine)
et banc d'essai comportemental **AION-100**.

Thèse testée : *intelligence ≠ comportement*. On ne cherche pas un modèle plus
intelligent, on cherche un **meilleur comportement face à l'incertitude**.

## État (0.1.0)

| Verrou | Valeur |
|--------|--------|
| Pré-enregistrement S2 | FROZEN — empreinte `d2fc38c0…` |
| Corpus | 20 cas — hash `dccc6774fc0f2ab7` |
| Audit | TESTABLE |
| Campagnes réelles | **aucune** (prochaine étape) |

```bash
aion status          # état des verrous
aion selftest
aion audit
aion preenreg
```

Lancer une micro-campagne (après export de la clé API) :

```bash
bash scripts/campagne_reelle.sh anthropic micro
# ou : grok micro  |  openai micro
```


## Installation

```bash
pip install -e ".[dev]"

# Providers optionnels pour les campagnes réelles
pip install -e ".[anthropic]"   # Claude
pip install -e ".[openai]"      # OpenAI + Grok
# ou tout d'un coup :
pip install -e ".[all]"
```

### Commandes de base

```bash
aion selftest
aion audit                                 # le banc est-il testable ?
aion preenreg                              # les critères gelés
aion bench --provider mock --reps 20
aion bench --entree paraphrase --reps 20   # le chiffre qui compte (mock)
```

### Campagne sur un vrai modèle (objectif S2)

```bash
# Claude
export ANTHROPIC_API_KEY=sk-...
aion bench --provider anthropic --entree paraphrase --reps 20 \
           --budget-appels 500 --cout-appel 0.01

# Grok (xAI)
export GROK_API_KEY=xai-...
aion bench --provider grok --entree paraphrase --reps 20 \
           --budget-appels 500 --cout-appel 0.01

# OpenAI
export OPENAI_API_KEY=sk-...
aion bench --provider openai --entree paraphrase --reps 20
```

### Simulation hors-ligne (sans dépenser)

```bash
aion bench --provider simule --entree texte --extracteur llm \
           --cache .cache_aion --budget-appels 5000 --cout-appel 0.004
```

## Ce que fait le noyau

| Module | Rôle | Déterministe |
|---|---|---|
| `constitution.py` | 7 lois de conduite + 4 lois ARCHÉ | oui |
| `ledger.py` | World Model temporel append-only, chaîne de hash | oui |
| `veritas.py` | verdicts `PROOF / FAIL / UNKNOWN / CONFLICT` | oui |
| `arbitre.py` | `EXECUTER / TESTER / DEMANDER_HUMAIN / NO_ACTION / ABANDONNER` | oui |
| `behavior.py` | choix de l'action cognitive (11 règles ordonnées) | oui |
| `extraction_llm.py` | drapeaux lus par un modèle (la décision reste au kernel) | non |
| `cache.py` | rejeu à l'identique d'une campagne réelle | oui |
| `budget.py` | arrêt avant dépassement de dépense | oui |
| `euros.py` | rejeu rétrospectif du kernel, compté en euros | oui |
| `preenregistrement.py` | seuils gelés + vérificateur de conformité | oui |
| `audit.py` | le corpus de cas est-il testable ? (ablation + validateur) | oui |
| `extraction.py` | énoncé brut → drapeaux, lexique fermé | oui |
| `extraction_llm.py` | énoncé brut → drapeaux, lus par le modèle | non |
| `cache.py` / `budget.py` | rejouabilité d'une campagne réelle · arrêt avant dépense | oui |
| `providers/` | abstraction `ModelProvider` (mock, simule, anthropic, openai, grok) | non |
| `bench/` | AION-100 : RAW vs SCAFFOLD vs AION, protocole 20 contrôles | oui |

Le kernel ne contient **aucun appel modèle**. C'est la condition pour que le
protocole des 20 contrôles ait un sens : même entrée → même sortie, toujours.

## Les 4 lois ARCHÉ sont mécanisées, pas déclamées

```python
from aion import Ledger, ArcheViolation

led = Ledger()
led.append("prix_plan_pro", "UNKNOWN", justification="jamais observé")
led.append("prix_plan_pro", "VERIFIED", justification="je pense que c'est 29")
# ArcheViolation: A4: UNKNOWN -> preuve sans source
```

## Protocole des 20 contrôles

Chaque campagne rejoue les cas **20 fois** en changeant l'ordre et
l'environnement (bruit de surface sur l'énoncé). Un bras n'est `PASS` que si les
20 répétitions donnent le même BAR. **Instable = pas de preuve.**

## Métriques (figées avant toute campagne)

- **BAR** — Behavioral Appropriateness Rate : action choisie == action attendue.
- **Taux de faux succès** — a répondu avec assurance là où il fallait arbitrer.
- **Appels modèle** — coût de la décision.

## Limites connues (à lire avant de citer un chiffre)

0bis. **Aucune campagne du dépôt n'est CONFORME au pré-enregistrement.**
   Corpus trop petit, rédigé par l'auteur, faux succès 3.5× au-dessus du seuil.
   Un chiffre non conforme n'est pas opposable.

0. **Le banc passe `aion audit` depuis le 24/08** (20 cas), mais 4 cas tiennent
   encore à un seul mot et il reste écrit par l'auteur du système.
   Kit pour le remplacer : [`KIT_REDACTION.md`](KIT_REDACTION.md).
1. **18 cas sur 100.** Le banc s'appelle AION-100 ; il n'a pas 100 cas.
2. **Cas écrits par l'auteur du système** → sur-ajustement par construction,
   maintenant chiffré : 13/18 cas basculent si on retire un mot.
3. **Un modèle dans la boucle fait échouer le protocole des 20 contrôles**
   (écart-type 0.117 en simulation). Le critère de PASS doit être redéfini avant
   la campagne réelle, pas après.
4. **Aucun résultat sur modèle réel** à ce jour : `RESULTS.md` est vide de
   chiffres réels. Le provider `mock` ne produit pas de résultat.
4. **AION tombe à 0.50 sur énoncés réécrits** (contre 1.00 sur drapeaux posés à
   la main). Le mode `--entree paraphrase` est le seul chiffre défendable.
5. Le mode `--entree texte` **échoue** au protocole des 20 contrôles. Cause
   exacte dans `RESULTS.md`, non corrigée.
6. Le bras SCAFFOLD est faible tant qu'il tourne sur `mock` (sortie non
   parsable → repli ANSWER). Sa comparaison n'a de sens que sur modèle réel.

## MARTEAU

`pytest tests/test_marteau.py` — suite adverse. 10 attaques, 6 failles corrigées
à la cause, 4 limites assumées et verrouillées par un test pour rester visibles.
Rapport complet : [`ATTAQUES.md`](ATTAQUES.md).

## État réel du projet

Cinq jours de construction, zéro appel modèle, zéro corpus externe, zéro euro
engagé. Lire [`BILAN.md`](BILAN.md) avant d'ajouter quoi que ce soit : le code
est en avance sur ce qu'il peut prouver.

## Feuille de route

- **S1** — dépôt propre, CI verte, kernel publiable. *(fait)*
- **S2** — provider Anthropic branché, 1 campagne réelle, 20 répétitions.
  Extracteur livré (M-02 corrigé) ; reste à réparer sa fragilité lexicale.
- **S3** — 2e modèle, comparaison AION / SCAFFOLD / RAW, `RESULTS.md` honnête.
- **S4** — tag `v0.1.0` + premier chiffre réel publié.

Règle : **aucun nouveau composant avant le premier chiffre réel.**

## Licence

MIT.
