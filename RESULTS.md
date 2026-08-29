# RESULTS

> Règle du projet : **tout résultat négatif est publié**. Un résultat absent est
> signalé comme absent, jamais comblé par une estimation.

## Modèles réels testés

| Date | Modèle | Bras | Répétitions | BAR | Faux succès | Stable | Rapport |
|---|---|---|---|---|---|---|---|
| — | *aucun* | — | — | — | — | — | — |

**État au 29/08/2026 : aucun chiffre sur modèle de frontier. Des micro-campagnes locales ont validé le circuit (section ci-dessous). Le tableau des modèles réels reste vide jusqu'à Ollama ou une clé API.**

## Micro-campagnes locales (2026-08-29) — non opposables

> Provider `local` / `simule` : **aucun modèle de frontier**.  
> 5 cas × 3 reps. Sert uniquement à valider le circuit de bout en bout.  
> Ne pas citer comme preuve d'efficacité de l'architecture.

### Provider `local` (distilgpt2 + extracteur lexical bruité)

| Bras | BAR moy | Écart-type | Parse KO | Appels |
|------|---------|------------|----------|--------|
| RAW | 0.200 | 0.163 | 0 | 15 |
| SCAFFOLD | 0.200 | 0.163 | 0 | 15 |
| AION | 0.467 | 0.094 | 0 | 15 |

- Écart AION−RAW : +0.267  
- Empreinte pré-enregistrement : `d2fc38c0…` (présente)  
- Rapport : `results/micro_local/`

### Provider `simule`

| Bras | BAR moy | Parse KO | Appels |
|------|---------|----------|--------|
| RAW | 0.200 | 0 | 15 |
| SCAFFOLD | 0.200 | 0 | 15 |
| AION | 0.467 | 1 | 15 |

Circuit validé : budget, cache, JSON, markdown, empreinte.

### Campagne locale élargie — 20 cas × 5 reps (`local`)

| Bras | BAR moy | Écart-type | Min | Max |
|------|---------|------------|-----|-----|
| RAW | 0.300 | 0.000 | 0.30 | 0.30 |
| SCAFFOLD | 0.300 | 0.000 | 0.30 | 0.30 |
| AION | 0.300 | 0.089 | 0.20 | 0.45 |

- Écart AION−RAW : **0.000**  
- Signal : sur le corpus complet en paraphrase + extracteur bruité, l'avantage micro (5 cas) **disparaît**.  
- C'est cohérent avec les alertes d'audit (fragilité lexicale, corpus auteur).  
- Rapport : `results/local_20cas_5reps/`

  
**Tableau des modèles réels ci-dessus reste vide.**


## Campagne de reproductibilité (provider = mock)

Ces chiffres ne sont **pas** un résultat. Ils vérifient une seule chose : le banc
est déterministe et rejouable.

| Bras | BAR | Faux succès | Appels modèle | 20/20 stable |
|---|---|---|---|---|
| RAW | 0.28 | 0.50 | 18 | oui |
| SCAFFOLD | 0.28 | 0.50 | 18 | oui |
| AION | 1.00 | 0.00 | 0 | oui |

### Pourquoi le 1.00 d'AION ne prouve rien

Les 18 cas ont été écrits par l'auteur des 11 règles du Behavior Engine. AION
obtient 1.00 **par construction** : le banc et le système partagent la même
théorie. C'est une tautologie mesurée, pas une compétence mesurée.

Ce chiffre ne deviendra informatif que si les deux conditions suivantes sont
réunies :

1. les cas sont rédigés par une personne extérieure (jalon 60 jours) ;
2. les bras tournent sur un modèle réel, où RAW et SCAFFOLD peuvent gagner.

### Résultat déjà acquis (négatif, publié)

Le bras SCAFFOLD sur `mock` est **indiscernable de RAW** (0.28 / 0.28). Le
scaffolding par prompt n'apporte rien tant que la sortie du modèle n'est pas
parsable. Si cet écart reste nul sur modèle réel, l'hypothèse H1 (« l'architecture
apporte plus que le prompt ») devra être défendue autrement — ou abandonnée.

## Correctif M-02 et premier chiffre non tautologique (24/08)

Le Behavior Engine reçoit désormais des drapeaux **dérivés de l'énoncé** par
`extraction.py`, au lieu de drapeaux posés à la main. Trois modes d'entrée :

| Entrée | Ce que ça mesure | AION — BAR | Faux succès | Drapeaux exacts | 20/20 |
|---|---|---|---|---|---|
| `drapeaux` | la table de règles seule | 1.00 | 0.00 | 1.00 | PASS |
| `texte` | + lecture de l'énoncé canonique | 0.94 | 0.06 | 0.94 | **FAIL** |
| `paraphrase` | + énoncé réécrit | **0.50** | 0.39 | 0.44 | PASS |

RAW et SCAFFOLD restent à 0.28 dans les trois modes (ils ne consomment pas les
drapeaux).

### Résultat principal : 1.00 → 0.50

Sur des énoncés réécrits, AION perd **la moitié de son avantage apparent**. Le
1.00 du mode `drapeaux` mesurait la cohérence entre une table de règles et un
banc écrits par la même personne. Le chiffre défendable est **0.50**, et il ne
bat RAW (0.28) que d'un facteur inférieur à 2 — sur un banc de 18 cas, ce n'est
pas un écart publiable.

### Échec du protocole des 20 contrôles en mode `texte` (FAIL, cause exacte)

BAR observé sur 20 répétitions : `0.9444` ×11, `1.0` ×6, `0.8889` ×3.
**Instable = pas de preuve.**

Cause exacte : l'extracteur ne reconnaît un verbe à conséquence réelle qu'en
**tête** d'énoncé. Le bruit de politesse injecté par le protocole
(`"Bonjour, "`) décale le verbe et annule le drapeau `consequence_reelle` sur
`cq-01`. Non corrigé : le correctif appartient à S2, avec re-gel des cas.
Verrouillé par `test_faille_bruit_de_politesse_casse_la_detection_du_verbe`.

### Mode d'échec observé

Quand un drapeau manque, la décision retombe sur `ANSWER` (règle R10). L'échec
est donc **silencieux** : le système répond avec assurance au lieu d'arbitrer.
C'est exactement le comportement que le projet prétend éliminer — le taux de
faux succès passe de 0.00 à 0.39 entre `drapeaux` et `paraphrase`.

## Le protocole des 20 contrôles est incompatible avec un modèle réel (24/08)

Campagne sur `SimuleProvider` — un modèle **factice non déterministe** (8 % de
drapeaux inversés, 2 % de sorties non parsables). Aucun chiffre ci-dessous n'est
un résultat ; c'est la mécanique qui est mesurée.

| Bras | BAR moyen | écart-type | min | max | 20/20 |
|---|---|---|---|---|---|
| RAW | 0.278 | 0.000 | 0.28 | 0.28 | PASS |
| SCAFFOLD | 0.278 | 0.000 | 0.28 | 0.28 | PASS |
| AION | 0.633 | **0.117** | 0.39 | 0.83 | **FAIL** |

### Ce que ça impose

1. **Un BAR seul ne veut plus rien dire.** L'écart entre la meilleure et la pire
   répétition est de **0.44** — plus large que l'écart entre AION et RAW. Toute
   publication devra donner moyenne ± écart-type, jamais un chiffre unique.
2. **Le critère `PASS = 20/20 identiques` devient inatteignable** dès qu'un
   modèle est dans la boucle. Il n'est **pas** modifié ici : le redéfinir après
   avoir vu qu'il échoue serait de la triche. La décision doit être prise et
   écrite **avant** la première campagne réelle (jalon S2).
3. Les sorties non parsables sont **comptées** (`parse KO`), jamais repliées
   silencieusement sur des drapeaux vides qui donneraient une bonne note.

### Rejouabilité ≠ robustesse

Avec `--cache`, deux modèles différents rendent des BAR **identiques** en rejeu
(975 hits / 1080 lectures dans la campagne ci-dessus). Le cache rend une campagne
réelle auditable par un tiers — il ne rend pas le système stable. La campagne
reste `FAIL`. Les deux notions ne doivent jamais être confondues dans un rapport.

## AION-€ — mécanique livrée, aucune donnée réelle (24/08)

Rejeu rétrospectif du kernel sur des décisions passées dont l'issue est connue.
Aucun appel modèle, aucune dépense. Critères gelés à part dans
[`preenregistrement-euros.json`](preenregistrement-euros.json) pour ne pas
toucher l'empreinte du pré-enregistrement principal.

**Ratio de prudence = (perte évitée − perte subie − gain manqué) / friction.**

Le gain manqué n'était pas dans la première version du calcul. Sans lui, le
gabarit donnait un ratio de **35** : un kernel qui bloque presque tout paraît
infiniment rentable tant qu'on ne compte pas ce que l'hésitation fait perdre.
Avec le coût d'opportunité, le même jeu tombe à **17** — et la table de
sensibilité montre l'essentiel :

| Rattrapage supposé | 2 € | 4 € | 8 € | 16 € | 32 € |
|---|---|---|---|---|---|
| 0.3 | −6.0 | −3.0 | −1.5 | −0.75 | −0.38 |
| 0.5 | 14.0 | 7.0 | 3.5 | 1.75 | 0.88 |
| 0.7 | 34.0 | 17.0 | 8.5 | 4.25 | 2.12 |
| 1.0 | 64.0 | 32.0 | 16.0 | 8.0 | 4.0 |

**Le signe du résultat dépend d'une hypothèse invérifiable** — la part des pertes
qu'une vérification aurait vraiment évitée. À 0.3, l'architecture détruit de la
valeur. Aucun ratio ne sera donc publié sans cette table.

Chiffres calculés sur 6 décisions **fictives** du gabarit : mécanique vérifiée,
résultat inexistant. Le pré-enregistrement exige 30 décisions réelles.

## Pré-enregistrement gelé le 24/08

Les seuils, l'hypothèse et la règle de décision sont figés dans
[`preenregistrement.json`](preenregistrement.json), empreinte
`41d0341f3ea5…`. Chaque campagne écrit cette empreinte dans son rapport :
modifier un seuil après coup rend toutes les campagnes antérieures **NON
CONFORMES**, visiblement, dans un diff.

Règle de décision, sans interprétation possible :

| Écart AION − RAW | Décision |
|---|---|
| ≥ 0.20 | **GO** — l'architecture est gardée |
| 0.10 – 0.20 | **SIMPLIFIER** — garder VERITAS et le ledger, jeter la table de règles |
| < 0.10 | **NO_GO** — publier le résultat négatif et arrêter |

### La campagne actuelle est NON CONFORME

`aion preenreg --verifier` sur la meilleure campagne du dépôt :

| Critère | État |
|---|---|
| écart AION − RAW `+0.200` | OK |
| écart AION − SCAFFOLD `+0.200` | OK |
| stabilité (écart-type `0.000`) | OK |
| **faux succès `0.350`** (max 0.10) | **NON** |
| **taille du corpus** 20 cas (min 30) | **NON** |
| **corpus externe** | **NON** — rédigé par l'auteur |

La décision calculée serait `GO`, et elle est explicitement marquée **non
opposable**. Le taux de faux succès à 0.35 est le point noir : sur énoncés
réécrits, AION répond avec assurance dans plus d'un tiers des cas où il devrait
arbitrer.

## Campagnes du 24/08 — banc a 20 cas, TESTABLE

Banc corrige (3 bloquants levés : fuite lexicale sur `as-03`, contrôle négatif
ajouté à `repeated_error`, 3e cas pour `role_adaptation`). `aion audit` rend
désormais `TESTABLE`, avec 4 alertes de fragilité maintenues.

### Extracteur lexical (déterministe, 0 appel modèle)

| Entrée | AION (BAR moy) | écart-type | min–max | Drapeaux | 20/20 |
|---|---|---|---|---|---|
| `drapeaux` | 1.000 | 0.000 | 1.00–1.00 | 1.00 | PASS |
| `texte` | 0.848 | 0.040 | 0.80–0.90 | 0.85 | **FAIL** |
| `paraphrase` | **0.500** | 0.000 | 0.50–0.50 | 0.45 | PASS |

RAW et SCAFFOLD : 0.300 partout.

### Extracteur modèle (`SimuleProvider` — modèle factice bruité, **pas un résultat**)

| Entrée | AION (BAR moy) | écart-type | min–max | Drapeaux | 20/20 | Parse KO |
|---|---|---|---|---|---|---|
| `texte` | 0.613 | 0.103 | 0.45–0.80 | 0.50 | **FAIL** | 10 |
| `paraphrase` | 0.375 | 0.081 | 0.25–0.50 | 0.35 | **FAIL** | 10 |

### Trois constats

1. **Un modèle non déterministe ne peut pas passer le protocole des 20 contrôles.**
   Écart-type 0.10 sur le BAR, min 0.45 / max 0.80 pour la même campagne. Ce n'est
   pas un défaut du simulateur : c'est la propriété que le protocole est censé
   détecter. Toute campagne réelle échouera au 20/20 — le critère devra devenir un
   intervalle, décidé **avant** la première campagne réelle, pas après.
2. **Le cache donne la rejouabilité, pas la robustesse.** Deux modèles de graines
   différentes rejoués sur le même cache produisent des BAR identiques, alors que
   la campagne reste instable. Ne jamais présenter un rejeu comme une preuve de
   stabilité.
3. **Les sorties illisibles ne sont pas masquées.** 10 échecs de parsing sur la
   campagne AION ; l'extracteur rend alors une `Situation` vide plutôt que de
   retomber en douce sur le lexical. Un repli silencieux ferait passer la
   défaillance du modèle pour un succès de l'architecture.

## Audit du banc : NON TESTABLE (24/08)

`aion audit` mesure si un corpus de cas peut porter un résultat, avant de mesurer
quoi que ce soit. Verdict sur le banc interne :

| Constat | Détail |
|---|---|
| **NON TESTABLE le 24/08 matin — corrigé depuis** | 3 bloquants |
| `role_adaptation` | 2 cas, minimum 3 |
| `repeated_error` | aucun contrôle négatif — un bras qui ne répond jamais y fait un sans-faute |
| `as-03` | la réponse attendue fuit dans l'énoncé (« **Compare** ces deux approches » → `COMPARE`) |
| **13 cas sur 18** | tiennent à **un seul mot** : retirer `prix`, `stock`, `Envoie` ou `Supprime` change la décision |

### Conséquence sur les chiffres déjà publiés

Le 0.50 en mode `paraphrase` reste le meilleur chiffre disponible, mais il est
mesuré sur un banc que son propre validateur refuse. **Aucun chiffre de ce dépôt
ne doit être cité tant que `aion audit` ne rend pas `TESTABLE`.**

L'ablation mot à mot explique aussi la chute 1.00 → 0.50 : quand la décision tient
à un mot, il suffit de le paraphraser pour la faire disparaître.

### Faux positif connu du validateur (V-FP1)

« compare » est à la fois un verbe français banal et le nom d'une action. La règle
de fuite est lexicale, elle ne peut pas trancher. Conservée telle quelle : une
règle qui se tait quand elle doute ne sert à rien.

## Ce que le protocole des 20 contrôles ne prouve pas (24/08)

Attaque MARTEAU `M-02` : le Behavior Engine ne lit jamais l'énoncé, uniquement
les drapeaux de `Situation`. Le bruit appliqué par le protocole ne peut donc
rien faire varier pour AION — sa stabilité 20/20 est vraie **par construction**.

→ La colonne « stable » ne doit **pas** être présentée comme un avantage d'AION
sur RAW/SCAFFOLD. Détail et correctif prévu : `ATTAQUES.md`.

## Journal des campagnes

Chaque campagne écrit un JSON horodaté dans `results/` (ordre des cas, graine,
BAR par répétition, échecs détaillés, environnement Python). Ne jamais publier un
chiffre sans le JSON correspondant.


## Corpus assistant (18 cas) — 2026-08-29

> Rédigé dans la conversation de construction. **Pas un corpus indépendant.**  
> Fichier : `corpus_assistant_18.json` — hash `7e2e24c1b6a178b2`  
> `corpus_externe` doit rester **false**.

### Validation

- `aion corpus validate` → PRET_INTEGRATION (structure)
- `aion audit` → TESTABLE
- Origine : assistant, pas un tiers

### Campagne locale 18 cas × 3 reps (`local`, paraphrase, llm)

| Bras | BAR moy |
|------|---------|
| RAW | 0.333 |
| SCAFFOLD | 0.333 |
| AION | 0.315 |

Écart AION−RAW : **−0.018** (AION n'améliore pas).  
Rapport : `results/assistant_18/`

