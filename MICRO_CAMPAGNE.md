# Micro-campagne S2 — validation du circuit

**Statut : prêt**  
**But : vérifier le circuit de bout en bout avant d’engager le budget de la campagne complète.**

Cette micro-campagne **n’est pas opposable** au pré-enregistrement S2  
(reps < 20, sous-échantillon de cas). Elle sert uniquement à prouver que :

1. le provider réel répond
2. l’extracteur LLM parse
3. le budget coupe correctement
4. le rapport JSON s’écrit avec l’empreinte du pré-enregistrement
5. rien ne plante

---

## Prérequis

```bash
# Une seule clé suffit
export ANTHROPIC_API_KEY=sk-...
# ou
export GROK_API_KEY=xai-...
# ou
export OPENAI_API_KEY=sk-...

pip install -e ".[anthropic]"   # ou .[openai] / .[all]
aion preenreg                   # vérifier le gel
aion audit                      # doit rester TESTABLE
```

---

## Lancement

```bash
# Claude
aion bench \
  --provider anthropic \
  --micro \
  --entree paraphrase \
  --extracteur llm \
  --budget-appels 40 \
  --cout-appel 0.01 \
  --out results/micro_anthropic.json

# Grok
aion bench \
  --provider grok \
  --micro \
  --entree paraphrase \
  --extracteur llm \
  --budget-appels 40 \
  --cout-appel 0.01 \
  --out results/micro_grok.json
```

Paramètres effectifs de `--micro` :
- **5 cas** (sous-échantillon aléatoire selon la graine)
- **3 répétitions**
- Marqué `micro_campagne: true` dans le JSON
- Avertissement explicite : non opposable

---

## Ce qu’on vérifie après

1. Exit code 0 (ou 2 si budget dépassé — acceptable en micro)
2. Fichier JSON créé dans `results/`
3. Champ `preenregistrement_empreinte` présent et égal à :
   `d2fc38c0d4146d4181f200e36266582cefd8e32030ff37548a0af9de6c87db77`
4. Champ `micro_campagne: true`
5. Au moins un bras a des `appels_extraction > 0` (preuve que le modèle a été appelé)
6. Pas d’exception Python

Si tout ça est vert → le circuit est validé → on peut lancer la campagne complète (20 cas × 20 reps).

---

## Coût estimé

| Provider | Appels max | Coût estimé |
|----------|------------|-------------|
| 5 cas × 3 reps × 3 bras × ~1 appel extraction | ≤ 40 | ~0,20–0,50 € |

Le garde-fou `--budget-appels 40` coupe avant dépassement.

---

## Après la micro-campagne

- Si le circuit casse → corriger, **sans** toucher au pré-enregistrement
- Si le circuit passe → lancer la campagne S2 complète (documentée dans `PREREGISTRATION_S2.md`)
