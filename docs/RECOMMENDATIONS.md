# 🌟 Recommandations 360° — ereputation2

> Roadmap de durcissement et d'industrialisation pour transformer le projet en plateforme **enterprise-grade**.

---

## 1. 🔒 Sécurité

### 1.1 Authentification & Autorisation (priorité **HAUTE**)
- **Manquant aujourd'hui** : aucune route n'est protégée. Tout `/api/v1/*` est ouvert.
- **Action** :
  - Ajouter `python-jose[cryptography]` et `passlib[bcrypt]` aux requirements.
  - Créer un module `core/security.py` avec :
    - `create_access_token()` / `create_refresh_token()`
    - Dépendance FastAPI `get_current_user()`
  - Modèle `User` (SQLAlchemy) + endpoint `/api/v1/auth/login` & `/refresh`.
  - Décorer toutes les routes plugins avec `Depends(get_current_user)`.

### 1.2 Rate-limiting
- **Action** : `slowapi` (basé sur `limits`) + Redis comme backend.
  ```python
  from slowapi import Limiter
  limiter = Limiter(key_func=lambda r: r.client.host, storage_uri=settings.REDIS_URL)
  app.state.limiter = limiter
  ```
  Limites par défaut suggérées :
  - `/api/v1/auth/login` : 5/min/IP
  - `/api/v1/scrape/*` : 30/min/utilisateur
  - Global : 60/min/IP

### 1.3 Secrets management
- **Aujourd'hui** : `.env` simple. **Suffisant** pour Coolify, mais :
- **Évolution** : pour multi-env (staging/prod), envisager **Doppler**, **Infisical**, ou **Hashicorp Vault** intégrés à Coolify.

### 1.4 Scan vulnérabilités
- **Trivy** en CI :
  ```yaml
  - run: trivy image --severity HIGH,CRITICAL --exit-code 1 ereputation2-backend:${{ github.sha }}
  ```
- **Snyk** ou **Dependabot** pour les deps Python/Node.

### 1.5 Hardening Docker
- Déjà fait : non-root, no-new-privileges, read-only frontend, tmpfs.
- À ajouter : `cap_drop: [ALL]` + `cap_add: [NET_BIND_SERVICE]` sur services qui écoutent.
- Profile **AppArmor**/**Seccomp** custom pour le backend.

### 1.6 WAF / Bot protection
- Coolify expose Traefik. Ajouter **Crowdsec** comme middleware Traefik :
  - Détection brute-force, scan, IP réputation crowd-sourced.
  - Plugin gratuit, déploiement trivial.

---

## 2. 👁️ Observabilité

### 2.1 Logs (priorité **HAUTE**)
- **Aujourd'hui** : Loguru (backend) + Nginx logs.
- **Action** :
  - Backend : passer Loguru en mode **JSON** en prod (`serialize=True`).
  - Centralisation : **Loki** + **Promtail** (stack Grafana, gratuite, légère).
  - Alternative SaaS : Datadog, BetterStack, Grafana Cloud.

### 2.2 Métriques
- Ajouter `prometheus-fastapi-instrumentator` :
  ```python
  from prometheus_fastapi_instrumentator import Instrumentator
  Instrumentator().instrument(app).expose(app)
  ```
- Métriques métier custom :
  - `prospects_scraped_total{source="insee|pappers"}`
  - `outreach_emails_sent_total{channel}`
  - `llm_requests_duration_seconds{model}`

### 2.3 Tracing distribué
- **OpenTelemetry** via `opentelemetry-instrumentation-fastapi` + `opentelemetry-instrumentation-asyncpg`.
- Backend : Tempo, Jaeger, ou Grafana Cloud.

### 2.4 Erreurs
- **Sentry** (DSN déjà prévu dans `.env.example`) :
  - Frontend : `@sentry/react` + replay sessions.
  - Backend : `sentry-sdk[fastapi]`.

### 2.5 Uptime
- **Better Uptime** ou **Uptime Kuma** (self-hosted, déployable sur Coolify).
- Endpoints à surveiller : `/healthz`, `/api/health`, `/api/v1/plugins`.

---

## 3. 🚀 Performance & Scalabilité

### 3.1 Backend
- **Workers Uvicorn** : 2 par défaut dans le `CMD` du Dockerfile. Ajuster selon RAM (`workers = 2 × CPU + 1`).
- **Gunicorn + UvicornWorker** pour gestion fine du cycle de vie.
- Cache Redis pour les réponses INSEE/Pappers (TTL 24h sur résultats stables).

### 3.2 Frontend
- **Code splitting** : déjà natif Vite, mais auditer avec `rollup-plugin-visualizer`.
- **Lazy load** des routes : `React.lazy(() => import('./pages/Pipeline'))`.
- **Image optimization** : utiliser des formats AVIF/WebP via `vite-plugin-image-optimizer`.
- **Préchargement** des routes critiques : `<link rel="prefetch">`.

### 3.3 Base de données
- **Index** sur les colonnes filtrées : `siret`, `email`, `score`, `created_at`.
- **Connection pooling** : asyncpg gère nativement, mais en cas de pics, ajouter **PgBouncer**.
- **Read replicas** : prévu dans `docker-compose.prod.yml` mais non utilisé. À activer dès >100k prospects.

### 3.4 LLM
- **Ollama** : précharger le modèle au démarrage (`OLLAMA_KEEP_ALIVE=24h`).
- **Cache sémantique** : embeddings + Redis pour éviter les calls LLM redondants (gain typique : 30-50%).
- **Fallback OpenAI** : circuit-breaker si Ollama OOM.

### 3.5 Scaling horizontal
- Le backend est *stateless* (state dans Postgres + Redis), donc scalable.
- Coolify ne fait pas de auto-scaling natif, mais :
  - **Coolify Pro** ou **K3s + Helm** pour cluster.
  - Préparer le déploiement Kubernetes : manifests prêts, juste à templatiser.

---

## 4. 🧪 Qualité & Tests

### 4.1 Tests backend (priorité **HAUTE**)
- Le dossier `tests/` existe mais semble vide. À structurer :
  ```
  tests/
  ├── unit/          # services, repositories, plugins
  ├── integration/   # API endpoints avec DB+Redis
  └── e2e/           # workflows complets
  ```
- Outils : `pytest`, `pytest-asyncio`, `httpx.AsyncClient`, `testcontainers-python`.
- Cible : **80% coverage** minimum sur `core/`, `services/`, `plugins/`.

### 4.2 Tests frontend
- **Vitest** pour unit tests composants (`@testing-library/react`).
- **Playwright** pour E2E sur les 3 parcours clés :
  1. Login → Dashboard
  2. Import CSV → Score → Pipeline
  3. Outreach campagne → Tracking

### 4.3 Lint & Format
- **Pre-commit hooks** :
  ```yaml
  # .pre-commit-config.yaml
  repos:
    - repo: https://github.com/astral-sh/ruff-pre-commit
      rev: v0.4.0
      hooks: [{id: ruff, args: [--fix]}, {id: ruff-format}]
    - repo: https://github.com/pre-commit/mirrors-eslint
      rev: v8.56.0
      hooks: [{id: eslint, files: \.[jt]sx?$, types: [file]}]
  ```
- **Type-check strict** : déjà activé dans `tsconfig.json`. Ajouter `mypy --strict` côté Python.

### 4.4 CI/CD GitHub Actions
Exemple minimal — voir [`docs/CI_TEMPLATE.yml`](./CI_TEMPLATE.yml) :
```yaml
name: CI
on: [push, pull_request]
jobs:
  backend:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.11'}
      - run: pip install -r requirements.txt ruff mypy
      - run: ruff check .
      - run: pytest --cov=core --cov=plugins --cov-fail-under=70
  frontend:
    runs-on: ubuntu-24.04
    defaults: {run: {working-directory: frontend}}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: {node-version: '20', cache: 'npm', cache-dependency-path: frontend/package-lock.json}
      - run: npm ci
      - run: npm run lint
      - run: npm run build
  docker:
    needs: [backend, frontend]
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/build-push-action@v5
        with:
          context: ./frontend
          load: true
          tags: frontend:test
      - run: docker run --rm aquasec/trivy image --severity HIGH,CRITICAL --exit-code 1 frontend:test
```

---

## 5. 📊 Données & RGPD

### 5.1 Migrations
- **Manquant** : Alembic.
- **Action** :
  ```bash
  pip install alembic
  alembic init migrations
  # Configurer alembic/env.py avec settings.DATABASE_URL
  alembic revision --autogenerate -m "initial"
  ```
- Lancer les migrations au boot : `alembic upgrade head` dans le `CMD` du backend (avant uvicorn).

### 5.2 Backups
- **Coolify** offre des backups Postgres natifs : à activer.
- Cible : S3 (AWS, Backblaze B2, Wasabi) ou stockage Coolify.
- Tester un *restore* trimestriel (un backup non-testé = pas de backup).

### 5.3 RGPD
- **Plugin `compliance-guard`** existe — vérifier qu'il implémente :
  - Registre des traitements (`/api/v1/gdpr/processing-register`)
  - Export RGPD (`/api/v1/gdpr/export?email=`)
  - Effacement RGPD (`/api/v1/gdpr/erase?email=`)
  - Consentement explicite tracé (table `consent_log`)
- **CGU & Politique de confidentialité** : pages publiques sur le frontend (manquantes).
- Note : le scraping B2B n'exige pas de consentement préalable mais nécessite *information* + *opt-out facile* (CNIL guidelines 2022).

### 5.4 Anonymisation
- En staging/dev, *jamais* de données réelles. Script `scripts/anonymize-db.py` à créer (Faker + UPDATE).

---

## 6. 🎨 UX / Frontend

### 6.1 Design system
- Tailwind est utilisé — bon choix. Ajouter **shadcn/ui** ou **Radix UI** pour composants accessibles.
- Tokens design : couleurs Epok/Laserandco (gold accent #D4AF37 + dark) à formaliser dans `tailwind.config.js`.

### 6.2 Accessibilité
- Audit **Lighthouse** ≥ 90 sur Accessibility.
- ARIA roles, keyboard nav, contrastes WCAG AA minimum.

### 6.3 i18n
- Si rayonnement européen prévu : **react-i18next**.

### 6.4 PWA
- Vite + `vite-plugin-pwa` → app installable, offline-first sur les listes consultables.

### 6.5 Mobile
- Le projet ne contient **pas d'app Android**. Si pertinent pour le commercial terrain :
  - Option 1 : PWA installable (rapide, suffisant pour 80% des cas).
  - Option 2 : App Android Kotlin natif (Android Studio) qui consomme la même API REST. Stack recommandée : **Jetpack Compose + Retrofit + Hilt**.

---

## 7. 🤖 IA & LLM

### 7.1 Confidentialité
- **Ollama local** : excellent choix B2B. Llama 3.1 8B = bon ratio qualité/RAM.
- Pour des cas plus exigeants : **Mistral 7B Instruct** ou **Qwen 2.5 7B**.

### 7.2 RAG (Retrieval-Augmented Generation)
- Pour le plugin `pain-point-engine` : indexer les data INSEE/Pappers + sites scrapés dans **Qdrant** ou **Weaviate**.
- Embeddings : `nomic-embed-text` via Ollama (gratuit, performant).

### 7.3 Function calling
- FastAPI tools exposés au LLM via le pattern OpenAI tools/Anthropic tools.
- Cas d'usage : "Trouve-moi 10 cabinets dentaires à Roubaix sans site web" → LLM appelle `scraper-insee.search()` puis `audit-digital.batch_audit()`.

### 7.4 Coûts
- OpenAI : prévoir un budget mensuel + alertes (`openai.api_key` rotated tous les 90 jours).
- Cache embeddings + responses → divise les coûts par 3-5x typiquement.

---

## 8. 🏢 Architecture long-terme

### 8.1 Découplage Backend
- Le `main.py` charge dynamiquement les routes des plugins → fragile en prod.
- **Évolution** : déclaratif via `manifest.yaml` de chaque plugin, validation Pydantic au boot, échec rapide si incohérence.

### 8.2 Event Bus
- Redis pub/sub aujourd'hui → suffisant pour 99% des cas.
- Si besoin de durabilité (replay, dead-letter queue) : **Redis Streams** (déjà inclus) ou **NATS JetStream**.

### 8.3 Workers asynchrones
- Pour les jobs lourds (scraping batch, envois mass-mail) : **Celery** + Redis broker.
- Plus moderne : **Arq** (asyncio-native, plus léger que Celery).

### 8.4 API Gateway
- Pour multi-tenant ou ouverture API publique : **Kong** ou **Traefik Plugin RateLimit** + auth Coolify.

### 8.5 Multi-tenant
- Si Epok revend la plateforme à plusieurs clients : isolation par schéma Postgres (`SET search_path TO tenant_xyz`) + middleware FastAPI.

---

## 9. 📦 DevEx (Developer Experience)

### 9.1 Makefile
```makefile
.PHONY: install dev build test lint deploy clean

install:
	pip install -r requirements.txt
	cd frontend && npm install

dev:
	docker compose -f docker-compose.yml up

test:
	pytest --cov && cd frontend && npm test

lint:
	ruff check . && cd frontend && npm run lint

build:
	./scripts/build-local.sh all

clean:
	docker compose down -v
	rm -rf frontend/node_modules frontend/dist .pytest_cache
```

### 9.2 Devcontainer
- `.devcontainer/devcontainer.json` pour onboarding 1-clic VSCode.

### 9.3 Documentation
- **MkDocs Material** pour la doc dev (architecture, plugins, runbooks).
- Hébergée sur GitHub Pages ou un service Coolify dédié.

---

## 10. 🎯 Roadmap proposée (3 sprints)

### Sprint 1 — Stabilité (2 semaines)
- ✅ Patch Dockerfile (ce livrable)
- 🔲 CI GitHub Actions
- 🔲 Auth JWT + rate-limit
- 🔲 Migrations Alembic
- 🔲 Backups Postgres Coolify

### Sprint 2 — Observabilité (2 semaines)
- 🔲 Sentry frontend + backend
- 🔲 Prometheus + Grafana (déployés via Coolify)
- 🔲 Loki + logs JSON
- 🔲 Uptime Kuma

### Sprint 3 — Qualité (2 semaines)
- 🔲 80% coverage tests backend
- 🔲 Playwright E2E sur 3 parcours clés
- 🔲 Pre-commit hooks
- 🔲 Trivy + Dependabot
- 🔲 Documentation MkDocs

---

## 📎 Ressources
- Coolify : https://coolify.io/docs
- FastAPI best practices : https://github.com/zhanymkanov/fastapi-best-practices
- 12-factor app : https://12factor.net
- OWASP API Security Top 10 : https://owasp.org/API-Security/
- CNIL prospection B2B : https://www.cnil.fr/fr/la-prospection-commerciale
