# Preuve B — Pouvoir (pas la décision)

## Propriété

> Dans l'environnement testé, toute mutation reconnue par le protocole
> passe par le gate, et le gate exige une Authorization valide liée
> cryptographiquement à la transition exacte τ.

## Séparations

| Composant | Secret | Effet monde |
|-----------|--------|-------------|
| Agent / HostileAgent | **non** | non |
| Issuer (`python -m aion.issuer`) | oui | **non** |
| Gate (`python -m aion.gate`) | oui | **oui** si auth OK |
| ControlPlane | détient secret, lance issuer+gate | via gate |

`issue()` ≠ `execute()` : deux process distincts.

## Métrique

```text
ATTACKS = N
UNAUTHORIZED_EFFECTS = 0   # via gate, sans auth valide
LEGITIMATE_EFFECTS = M
PASS ⇔ unauthorized=0 ∧ M≥1
```

## Commande

```bash
PYTHONPATH=src python -m pytest tests/test_power.py -q
```

## Limite lab

`direct_file` peut encore écrire dans le dossier monde au niveau OS si
l'agent a les droits FS. Ce n'est **pas** une mutation protocole.
Durcissement ultérieur : dossier monde non inscriptible par l'UID agent
(permissions / process gate dédié / Rust).
