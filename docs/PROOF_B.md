# Preuve B — Pouvoir

Propriété: toute mutation protocole passe par le gate; Authorization liée à τ.

| Composant | Secret | Effet |
|-----------|--------|-------|
| Agent | non | non |
| Issuer | oui | non |
| Gate | oui | oui si auth OK |

Métrique: ATTACKS=N | UNAUTHORIZED_EFFECTS=0 | LEGITIMATE_EFFECTS=M

`pytest tests/test_power.py -q`
