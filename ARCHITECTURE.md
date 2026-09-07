# AION — architecture unifiée

> La preuve décide, pas l'intention.  
> Mesurer avant d'amplifier.

## Carte des composants (issus des archives)

| Couche | Modules | Origine |
|--------|---------|---------|
| **Noyau** | constitution, ledger, veritas, arbitre, behavior | aion-noyau-s1, noyau, synapse-veritas |
| **Preuve** | veritas, audit, preenregistrement, marteau | aion-noyau-audit, boite-a-outils-rigueur |
| **Extraction** | extraction, extraction_llm | aion-noyau-extraction |
| **Banc** | bench/cases, arms, metrics, runner | aion-100, aion-test-complet |
| **Providers** | mock, simule, local, ollama, anthropic, openai, grok | aion-noyau-s1 |
| **Économie** | euros, budget, cache | aion-euros, aion-bilan |
| **Surface** | cli, web API + UI | aion-x-final, platform |
| **Futur (gelé)** | CRDT, fédération, atlas, agora | linear-crdt, federation, atlas — *après* preuve S2 |

## Flux de décision

```
Demande
  → Extraction (drapeaux)
  → Behavior Engine (R0–R10)
  → Veritas (PROOF/FAIL/CONFLICT/UNKNOWN)
  → Arbitre (EXECUTER/TESTER/DEMANDER_HUMAIN/NO_ACTION/ABANDONNER)
  → Action autorisée ou refus
```

## Verrou scientifique S2

- Pré-enregistrement gelé (`preenregistrement.json`)
- Empreinte SHA-256 dans chaque rapport
- Corpus 20 cas, entrée `paraphrase`, extracteur `llm`
- Seuils : Δ(AION−RAW) ≥ 0.15, FSR ≤ 0.15
- **Aucun** nouveau composant d'architecture avant un chiffre réel

## Ce qui n'est PAS dans v0.1

Multi-agent, GUI lourde, fédération CRDT, marketplace, D2C/B2B engines —  
présentés dans les archives comme **vision**, pas comme code de production tant que S2 n'a pas parlé.

## API & UI

- Production : https://aion-3.onrender.com/
- Docs : /docs
- Health : /health
