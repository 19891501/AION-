# Campagne Anthropic via GitHub Actions

## Prérequis

1. Secret repo : `ANTHROPIC_API_KEY` (déjà créé ✓)
2. Workflow : `.github/workflows/anthropic-burn.yml`

## Lancer (consommer les 29 $)

1. GitHub → repo **AION-**
2. Onglet **Actions**
3. Workflow **Anthropic Burn (AION mesure)**
4. **Run workflow**
   - modele : `claude-3-5-haiku-latest` (volume) ou sonnet (qualité)
   - phase : `all`
5. Attendre la fin → **Artifacts** → `aion-anthropic-results`

## Sécurité

- La clé ne sort pas dans les logs (seulement `len=`)
- Pas de commit de clé
- Artifact = JSON de campagnes seulement

## Après expiration (1er sept)

Révoque / régénère la clé Anthropic et supprime le secret GitHub si besoin.
