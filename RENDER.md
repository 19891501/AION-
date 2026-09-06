# Déploiement Render

Pas d'API Render depuis ici : tu cliques Blueprint, GitHub pousse le yaml.

## 1. Runtime AION (API + MCP)

Repo : `19891501/AION-`

1. [render.com](https://dashboard.render.com) → **New** → **Blueprint**
2. Connecte `19891501/AION-`
3. Service `aion` — start : `uvicorn web.boot:app`
4. Custom domain (option) : `api.sios.app`

Health : `/health` · MCP : `POST /mcp` · Docs : `/docs`

Si le service `aion-3` existe déjà : **Manual Deploy** → latest `main`.
Change le start command en `uvicorn web.boot:app --host 0.0.0.0 --port $PORT`.

## 2. SIOS — sios.app (site produit)

Repo : `19891501/sios` · Blueprint `render.yaml` · static.

Custom domain : `sios.app`

DNS chez le registrar :
```
CNAME  www  sios.onrender.com
```
Apex : CNAME flattening / ALIAS vers `sios.onrender.com`
(ou les A de Render indiqués dans le dashboard).

## 3. VELYX — velyx.org (lab)

Repo : `19891501/velyx` · static.

Custom domain : `velyx.org`

## Test MCP une fois AION live

```bash
curl https://aion-3.onrender.com/mcp
curl -X POST https://aion-3.onrender.com/mcp \
  -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"aion_propose","arguments":{"intent":"virement 10000","action":"transfer","target":"iban-X","amount":10000}}}'
```
Attendu : `effect: 0`.
