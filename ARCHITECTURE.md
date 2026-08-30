# AION — architecture unifiée

> La preuve décide, pas l'intention.
> Mesurer avant d'amplifier.

## Carte des composants (archives fusionnées)

| Couche | Modules | Origine |
|--------|---------|--------|
| Noyau | constitution, ledger, veritas, arbitre, behavior | aion-noyau-s1, noyau, synapse-veritas |
| Preuve | veritas, audit, preenregistrement, marteau | aion-noyau-audit, boite-a-outils-rigueur |
| Extraction | extraction, extraction_llm | aion-noyau-extraction |
| Banc | cases, arms, metrics, runner | aion-100 |
| Providers | mock, simule, local, ollama, anthropic, openai, grok | aion-noyau |
| Économie | euros, budget, cache | aion-euros |
| Surface | cli, web API + UI | aion-x-final |
| Futur (gelé) | CRDT, fédération, atlas | *après* preuve S2 |

## Flux

Demande → Extraction → Behavior (R0–R10) → Veritas → Arbitre → action

## Verrou S2

Pré-enregistrement gelé. Aucun nouveau composant d'architecture avant un chiffre réel sur modèle frontier.

## Production

https://aion-3.onrender.com/
