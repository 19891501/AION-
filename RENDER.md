# Déploiement Render

## Option A — Blueprint

1. [render.com](https://render.com) → **New** → **Blueprint**
2. Connecte le repo `19891501/AION-`
3. Render lit `render.yaml` → service `aion`
4. Deploy

## Option B — Web Service manuel

- Runtime: Python 3
- Build: `pip install -e . && pip install -r requirements.txt`
- Start: `uvicorn web.app:app --host 0.0.0.0 --port $PORT`
- Health: `/health`

## Endpoints

| Path | Rôle |
|------|------|
| GET /health | Healthcheck |
| GET /status | Verrous S2 + audit |
| GET /preenreg | Pré-enregistrement |
| GET /audit | Corpus TESTABLE ? |
| POST /decide | Behavior Engine |
| POST /veritas | Couche preuve |
| /docs | Swagger UI |

## Test local

```bash
pip install -e ".[dev]" -r requirements.txt
uvicorn web.app:app --reload --port 8000
curl localhost:8000/status
```
