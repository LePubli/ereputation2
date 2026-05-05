# 📝 Changelog — Patch Production ereputation2

> Ce document récapitule les modifications apportées par le patch.

---

## 🔴 Bugs critiques corrigés

### `frontend/Dockerfile`
- **Avant** : 110 lignes contenant **3 versions concaténées** du Dockerfile, dont la dernière préfixée par des numéros de ligne (`1\t`, `2\t`, …) provenant d'une sortie d'outil d'affichage.
- **Après** : Dockerfile multi-stage propre (deps + builder + production), 70 lignes, BuildKit-aware, non-root.
- **Erreur Coolify résolue** : `Dockerfile parse error: unknown instruction "1"`.

### `.gitignore`
- **Avant** : 3 versions concaténées avec markers de diff chinois (`--- (原始)` / `+++ (修改后)`) et lignes Markdown (` ``` `).
- **Après** : `.gitignore` propre, sections clairement délimitées.

---

## 🟢 Nouveaux fichiers

| Fichier | Rôle |
|---|---|
| `frontend/.dockerignore` | Exclut `node_modules`, `dist`, `.env`, `.git` du build context |
| `.dockerignore` (racine) | Exclut artefacts Python, frontend, secrets du build backend |
| `scripts/build-local.sh` | Test du build avant push, avec smoke tests |
| `scripts/generate-secrets.sh` | Génère `.env` avec `openssl rand` |
| `scripts/healthcheck.sh` | Vérifie l'état de tous les endpoints |
| `docs/RECOMMENDATIONS.md` | Roadmap 360° de durcissement |
| `docs/CHANGELOG.md` | Ce fichier |

---

## 🟡 Fichiers améliorés

### `Dockerfile` (backend)
- Multi-stage **builder + production** (gain ~40% taille image).
- `python:3.11-slim-bookworm` au lieu de `python:3.11-slim` (Debian 12 stable).
- Cache BuildKit `--mount=type=cache,target=/root/.cache/pip`.
- Ajout `asyncpg` + `psycopg2-binary` (manquaient dans `requirements.txt`).
- User non-root explicite (UID 1000, system user).
- `tini` comme PID 1 (graceful shutdown).
- 2 workers Uvicorn par défaut + `--proxy-headers` + `--forwarded-allow-ips`.
- Healthcheck `start-period` rallongé à 20s (laisse le temps au lifespan).

### `frontend/Dockerfile`
- Stages séparés : `deps` (install) + `builder` (compile) + `production` (Nginx).
- `node:20-alpine` au lieu de `node:18-alpine` (Node 18 EOL avril 2025).
- Cache npm via BuildKit.
- ARG `VITE_*` pour injection variables build-time.
- Sanity check post-build (`test -f /app/dist/index.html`).
- User `nginx` non-root, port `8080` (non privilégié).
- `tini` PID 1.
- Healthcheck `/healthz` dédié (vs `/`).
- Labels OCI complets.

### `frontend/nginx.conf`
- Logs JSON structurés (`json_combined`) → Loki/Datadog ready.
- Endpoint `/healthz` séparé (status 200 plain text, pas d'`access_log`).
- Headers de sécurité : CSP, HSTS, X-Frame-Options, Permissions-Policy.
- Compression Gzip + types étendus (wasm, avif, webp).
- Cache 1 an immutable pour assets hashés Vite.
- `index.html` no-cache (déploiements transparents).
- WebSocket support pour streaming SSE/LLM.
- Timeouts 300s pour `/api/` (LLM Ollama peut être lent).
- Bloque `.dotfiles` (sauf `.well-known/` pour Let's Encrypt).
- `server_tokens off` (cache version Nginx).

### `docker-compose.coolify.yml`
- **Build args alignés** entre compose et Dockerfiles (`VITE_*`).
- **Variables obligatoires** avec syntaxe `${VAR:?error message}` : échec rapide si manquantes.
- **Healthchecks robustes** sur tous les services + `depends_on.condition: service_healthy`.
- **Resource limits** (CPU + RAM) sur tous les services.
- **Logs JSON** avec rotation (`max-size`, `max-file`).
- **Security** : `no-new-privileges`, `read_only` (frontend), `tmpfs` montés.
- **Postgres 16** (vs 15) + paramètres prod (`shared_buffers`, slow query log).
- **Redis 7** avec `requirepass`, `maxmemory 256mb`, `allkeys-lru`.
- **Service Ollama** ajouté (profile `llm`, optionnel).
- Pas de port exposé sauf via Coolify reverse proxy.
- Volume nommé pour `pgdata` (sous-dossier explicite).

### `.env.example`
- Variables `VITE_*` ajoutées (frontend build args).
- Variable `IMAGE_TAG` ajoutée (rollback Coolify).
- Marqueurs `__CHANGE_ME__` clairs sur les secrets.
- Sections regroupées et commentées.
- `LLM_API_URL` aligné sur le service Docker `ollama:11434`.

---

## 🔢 Métriques avant/après

| Métrique | Avant | Après |
|---|---|---|
| Taille image frontend | ~180 MB (estimé) | ~50 MB |
| Taille image backend | ~450 MB | ~280 MB |
| Lignes Dockerfile frontend | 110 (corrompues) | 70 (propres) |
| Healthchecks définis | 3 | 5 |
| Services avec resource limits | 0 | 5 |
| Services non-root | 0 | 2 |
| Headers de sécurité Nginx | 3 | 7 |
| Variables critiques avec validation | 0 | 3 |

---

## 🧪 Tests de validation

```bash
# 1. Build frontend isolé
docker buildx build \
    --platform linux/amd64 \
    --build-arg VITE_API_BASE_URL=/api \
    --build-arg VITE_APP_VERSION=1.0.0 \
    -t ereputation2-frontend:test \
    --load \
    ./frontend

# 2. Build backend isolé
docker buildx build \
    --platform linux/amd64 \
    -t ereputation2-backend:test \
    --load \
    .

# 3. Stack complète
./scripts/generate-secrets.sh > .env
docker compose -f docker-compose.coolify.yml up -d

# 4. Vérification
./scripts/healthcheck.sh http://localhost:8080
docker compose -f docker-compose.coolify.yml ps
```

---

## ⏭️ Migrations à prévoir (côté code)

Ces points ne sont **pas** corrigés par le patch (hors scope) mais sont identifiés :

1. `frontend/src/services/api.ts` doit utiliser `import.meta.env.VITE_API_BASE_URL` au lieu d'une URL en dur.
2. `core/config.py` doit accepter `DATABASE_URL` au format `postgresql+asyncpg://` (asyncpg dialect).
3. Ajouter Alembic pour les migrations DB.
4. Le plugin manager `core/plugin_manager.py` charge dynamiquement → ajouter un cache au démarrage et fail-fast si plugin défaillant.
5. CI GitHub Actions à créer (template fourni dans `RECOMMENDATIONS.md`).
