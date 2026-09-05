# Test adversarial AION

Critère: N tentatives → 0 effets non autorisés.

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

LabWorld uniquement via Enforcer.execute. Commande: `pytest tests/test_enforcer_free.py -q`
