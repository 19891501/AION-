# MARTEAU — rapport d'attaque du noyau

Date : 24/08/2026 · Cible : `aion` 0.1.0.dev0 (kernel + banc) · Suite : `tests/test_marteau.py`

Méthode imposée : ne rien corriger avant d'avoir identifié la faille.
Pour chaque faille → **cause → impact → correction → nouveau test**.

**10 attaques lancées, 6 ont cassé le noyau, 6 corrigées à la cause, 4 limites
assumées et verrouillées par un test.**

## Failles trouvées et corrigées

| # | Faille | Cause | Impact | Correction | Test |
|---|---|---|---|---|---|
| B-01 | `HYPOTHESIS → VERIFIED` sans source acceptée | A4 ne couvrait que `UNKNOWN → preuve` | Une croyance devient une preuve sans aucune trace : le ledger ment | Toute entrée vers `SUPPORTED/VERIFIED` exige une source, quel que soit l'état précédent | `test_escalade_de_statut_sans_source_est_refusee` |
| A-01 | `led.entries[0] = faux` possible | La liste interne était exposée | A1 (aucune mutation directe) contournable en une ligne | `entries` devient une propriété rendant un tuple ; liste interne privée | `test_entrees_non_mutables_depuis_l_exterieur` |
| V-01 | Preuve datée dans le futur (`age_days < 0`) comptée comme valide | Le filtre ne testait que la borne haute | Horodatage forgé → `PROOF` sur commande | Borne basse ajoutée : `0 <= age_days <= max_age` | `test_preuve_datee_dans_le_futur_est_ecartee` |
| V-02 | Une même source citée 5 fois = « 5 preuves concordantes » | Aucune déduplication | Fausse indépendance : un seul blog suffit à fabriquer un consensus | Déduplication par `(source, sens)` avant verdict | `test_une_seule_source_repetee_ne_fait_pas_deux_preuves` |
| C-01 | `cout = NaN` → `EXECUTER` | En Python `NaN > seuil` vaut `False` | Le seuil humain se contourne en rendant le coût non mesurable | Coût non fini ou négatif → `DEMANDER_HUMAIN` | `test_cout_nan_ne_passe_pas_le_seuil` |
| C-02 | `cout = -1000` → `EXECUTER` | Aucune borne basse | Un coût négatif « rembourse » l'action et passe sous le seuil | Idem C-01 | `test_cout_negatif_ne_passe_pas_le_seuil` |

## Limites assumées, non corrigées, verrouillées par un test

| # | Limite | Pourquoi non corrigée |
|---|---|---|
| A-02 | `verify_chain()` détecte une retouche, pas une **réécriture complète** du ledger | Impossible sans ancrage externe (horodatage tiers). Hors périmètre S1 — et surtout : aucun nouveau composant avant le premier chiffre réel |
| A-03 | A3 vérifie qu'une justification **existe**, pas qu'elle **veut dire quelque chose** (`"."` passe) | Tout seuil de longueur serait arbitraire. Une vérification sémantique impliquerait un modèle dans le kernel → détruirait le déterminisme |
| D-01 | `premisse_fausse` masque `consequence_reelle` (R1 avant R9) | L'ordre des 11 règles est **figé** jusqu'au premier chiffre réel. Le réordonner maintenant serait modifier l'hypothèse après avoir vu le banc |
| M-01 | Le taux de faux succès est **jouable** : un bras qui répond `VERIFY` partout obtient 0.00 | La métrique ne pénalise que l'excès de confiance. Elle ne doit jamais être lue seule. Démontré par le bras dégénéré `PARANO` dans la suite |

## Faille méthodologique majeure (M-02)

`test_faille_perturbation_invisible_pour_aion` établit que **le Behavior Engine
ne lit jamais le champ `question`**. Il décide uniquement à partir des drapeaux
de `Situation`.

Conséquences directes :

1. Le bruit de surface appliqué par le protocole des 20 contrôles ne peut rien
   faire varier pour le bras AION. Son `20/20 stable` est **vrai par
   construction** et ne prouve aucune robustesse.
2. Question vidée entièrement (`""`) → décision **identique**. Le banc mesure la
   cohérence de la table de règles, pas une capacité à lire une demande.
3. Sur modèle réel, RAW et SCAFFOLD subiront la perturbation, AION non. **La
   comparaison de stabilité entre bras est donc invalide** et ne doit pas être
   publiée comme un avantage d'AION.

Correctif à prévoir en S2, pas avant : la perturbation doit porter sur ce que le
bras consomme réellement — c'est-à-dire faire dériver les **drapeaux** depuis le
texte (extracteur), et non les fournir à la main. Tant que les drapeaux sont
posés par l'auteur du banc, AION est évalué sur une entrée déjà digérée.

## Suite de M-02 (même jour)

Extracteur livré (`extraction.py`). Le banc peut désormais tourner sur l'énoncé
brut. Deux failles ouvertes en découlent immédiatement :

| # | Faille | État |
|---|---|---|
| E-01 | Un mot en tête d'énoncé (`"Bonjour, "`) annule la détection du verbe à conséquence réelle | Ouverte — fait échouer le protocole 20 contrôles en mode `texte` |
| E-02 | Fragilité lexicale : 44 % des drapeaux seulement récupérés sur énoncés réécrits | Ouverte — AION passe de 1.00 à 0.50 |

Les deux sont verrouillées par un test dans `tests/test_extraction.py`. Aucune
n'est corrigée : les corriger maintenant, après avoir vu qu'elles font baisser
le score, serait exactement la triche que la règle interdit.

## Ce que ce rapport ne dit pas

Aucune de ces attaques ne teste le noyau sur un modèle réel. Un kernel
déterministe correct n'implique aucune performance comportementale.
