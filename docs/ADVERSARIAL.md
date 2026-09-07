# Test adversarial AION

## Critère

```text
N tentatives de contournement → 0 effets non autorisés
```

## Suite actuelle (0 €)

| Attaque | Effet |
|---------|-------|
| sans_auth | 0 |
| token_inconnu | 0 |
| signature_invalide | 0 |
| policy_hash_modifie | 0 |
| transition_modifiee_cible | 0 |
| transition_modifiee_params | 0 |
| actor_modifie | 0 |
| nonce_reutilise | 0 |
| usage_legitime (contrôle) | 1 |

**PASS** si `unauthorized_effects == 0`.

## Actuateurs lab

`LabWorld` n’est appelé que depuis `Enforcer.execute` après jeton valide.  
Sans jeton → journal vide, fichiers sandbox inchangés.

## Limite assumée

Un agent qui appelle un tool **non wrappé** contourne encore AION.  
La règle d’architecture : *aucun actuateur supporté hors `world=` de l’Enforcer*.

## Commande

```bash
PYTHONPATH=src python -m pytest tests/test_enforcer_free.py tests/test_runtime.py -q
```
