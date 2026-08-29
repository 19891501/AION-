# Checklist Semaine 1 — dépôt propre + noyau publiable

Cocher dans l'ordre. Ne rien ajouter au périmètre.

## J1 — dépôt GitHub

- [ ] Créer le dépôt **privé** `aion` sur le nouveau compte GitHub (bascule de compte déjà décidée).
- [ ] `git init && git add . && git commit -m "noyau v0.1.0.dev0 : kernel + banc AION-100"`
- [ ] `git branch -M main && git remote add origin <url> && git push -u origin main`
- [ ] Vérifier que l'onglet **Actions** passe au vert (3 versions de Python).
- [ ] Protéger `main` : PR obligatoire, CI verte requise.

## J2 — vérification locale

- [ ] `pip install -e ".[dev]"`
- [ ] `pytest -q` → 33 tests verts
- [ ] `aion selftest` → PASS
- [ ] `aion bench --provider mock --reps 20` → 3 bras stables
- [ ] `ruff check src tests` → 0 erreur

## J3 — provider réel (préparation S2)

- [ ] `pip install "aion[anthropic]"`
- [ ] `export ANTHROPIC_API_KEY=...` (jamais dans le dépôt, jamais dans la CI)
- [ ] `python -c "from aion.providers import charger; print(charger('anthropic').complete('ping').texte)"`
- [ ] Noter le coût par appel : 18 cas × 20 répétitions × 2 bras = **720 appels** par campagne.

## J4 — arbitrage des doublons

- [ ] Confirmer que le dépôt `noyau` est bien introuvable (déclaré MANQUANT le 22/08).
- [ ] Si introuvable : la colonne « Noyau » du banc `arene` est **retirée**, pas laissée vide.
- [ ] Archiver dans `/archive` les paquets déjà tranchés (aion-arena, wwm, aion-core, AI-COS-Core, synapse-veritas, aion-world).

## J5 — figer avant de mesurer

- [ ] Relire `behavior.py` : **l'ordre des 11 règles est figé** jusqu'au premier chiffre réel.
- [ ] Relire `metrics.py` : les 3 métriques sont figées.
- [ ] Écrire dans `RESULTS.md` la date de gel et la valeur attendue de H0.
- [ ] Tag `v0.1.0.dev0`.

## Ajout 24/08 — corpus externe

- [ ] Envoyer `KIT_REDACTION.md` + `cas_externes_gabarit.json` à **une personne
      extérieure** (45 min de son temps, aucune connaissance du système requise).
- [ ] `aion audit --fichier son_fichier.json` jusqu'à `TESTABLE`.
- [ ] Remplacer le banc interne par son corpus. Publier le résultat tel quel.

## Ajout 24/08 — la campagne réelle est prête à tirer

- [ ] Décider **et écrire dans RESULTS.md, avant de lancer**, le nouveau critère
      de PASS avec un modèle dans la boucle (écart-type maximum toléré ?
      intervalle de confiance ? nombre de répétitions ?).
- [ ] `export ANTHROPIC_API_KEY=...`
- [ ] Répétition à blanc, gratuite : `--provider simule` (même commande).
- [ ] Tir réel :
      `aion bench --provider anthropic --entree paraphrase --extracteur llm \
       --cache .cache_aion --budget-appels 1200 --cout-appel 0.004 --reps 20`
- [ ] Archiver `.cache_aion/` avec le rapport : sans lui, personne ne peut
      rejouer le chiffre publié.

## Ajout 24/08 — pré-enregistrement

- [ ] Relire `preenregistrement.json` ligne par ligne et **accepter les seuils**
      (ou les changer maintenant : après la première campagne, c'est trop tard).
- [ ] `git add preenregistrement.json && git commit -m "gel des criteres"` —
      le commit horodate le gel mieux qu'une date écrite à la main.
- [ ] `aion preenreg --verifier` après chaque campagne. Exit code 1 = non opposable.

## Critère de sortie de S1

Dépôt public ou privé propre + CI verte + `RESULTS.md` qui dit explicitement
qu'il n'y a aucun chiffre réel. **Pas de nouveau composant.**
