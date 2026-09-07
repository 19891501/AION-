# Déploiement Render

## Prérequis

1. Compte sur [render.com](https://render.com)
2. Repo GitHub connecté (idéalement avec le code **complet**)

## Option A — Blueprint (recommandé)

1. Dashboard Render → **New** → **Blueprint**
2. Connecte le repo `19891501/AION-`
3. Render lit `render.yaml` et crée le service `aion`
4. Deploy

## Option B — Web Service manuel

1. **New** → **Web Service**
2. Repo : `https://github.com/19891501/AION-`
3. Runtime : **Python 3**
4. Build : `pip install -e . && pip install -r requirements.txt`
5. Start : `uvicorn web.app:app --host 0.0.0.0 --port $PORT`
6. Health check : `/health`

## Endpoints

| Méthode | Path | Rôle |
|---------|------|------|
| GET | `/` | Info service |
| GET | `/health` | Healthcheck Render |
| GET | `/status` | Verrous S2 + audit |
| GET | `/preenreg` | Pré-enregistrement gelé |
| GET | `/audit` | Corpus TESTABLE ? |
| POST | `/decide` | Behavior Engine |
| POST | `/veritas` | Couche preuve |

Docs interactives : `https://<service>.onrender.com/docs`

## Test local

```bash
pip install -e ".[dev]" -r requirements.txt
uvicorn web.app:app --reload --port 8000
curl http://127.0.0.1:8000/status
```
