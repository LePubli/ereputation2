# 🎯 ereputation2 — Copilote Commercial B2B (Epok)

> **Patch de production** — Correction du Dockerfile frontend corrompu, durcissement de la stack et préparation au déploiement Coolify.

[![Coolify](https://img.shields.io/badge/Coolify-ready-6366f1)](https://coolify.io)
[![Docker](https://img.shields.io/badge/Docker-29.x-2496ed)](https://www.docker.com/)
[![Ubuntu](https://img.shields.io/badge/Ubuntu-24.04%20LTS-E95420)](https://ubuntu.com/)

---

## 📋 Sommaire

1. [Description du projet](#-description-du-projet)
2. [Diagnostic de l'erreur Coolify](#-diagnostic-de-lerreur-coolify)
3. [Architecture cible](#-architecture-cible)
4. [Arborescence](#-arborescence)
5. [Prérequis](#-prérequis)
6. [Installation pas à pas](#-installation-pas-à-pas)
7. [Configuration `.env`](#-configuration-env)
8. [Lancement local](#-lancement-local)
9. [Déploiement Coolify](#-déploiement-coolify)
10. [Debug & troubleshooting](#-debug--troubleshooting)
11. [Checklist Production](#-checklist-production)
12. [Recommandations 360°](#-recommandations-360)

---

## 📦 Description du projet

**ereputation2** (alias *B2B Prospector* / *Copilote Commercial B2B*) est une plateforme modulaire de prospection B2B intelligente combinant :

- **Frontend** : React 18 + Vite 5 + TypeScript + Tailwind, servi par Nginx Alpine
- **Backend** : FastAPI (Python 3.11) avec architecture plugin (11 plugins métier)
- **Datastores** : PostgreSQL 16 + Redis 7 (Event Bus)
- **LLM** : Ollama local (confidentialité B2B) — fallback OpenAI
- **APIs externes** : INSEE, Pappers
- **Déploiement** : Coolify sur Ubuntu 24 LTS, Docker 29.4 + BuildKit + Buildx

---

## 🚨 Diagnostic de l'erreur Coolify

### Symptôme
Lors du build Coolify : `Dockerfile parse error : unknown instruction "1"` autour des lignes 125-127.

### Cause racine identifiée

Le fichier `frontend/Dockerfile` du dépôt original contient **trois versions du même Dockerfile concaténées**, dont la dernière est précédée de **numéros de ligne** (`1\t`, `2\t`, …) provenant d'une sortie d'outil d'affichage (type `cat -n`, `view`, ou rendu Markdown numéroté). Docker interprète ces chiffres comme des instructions invalides.

**Preuve** (extrait du fichier original) :
```dockerfile
35	CMD ["nginx", "-g", "daemon off;"]
36	
37	        # Frontend Dockerfile - Production Ready   ← début 2e Dockerfile
38	        FROM node:18-alpine AS builder
...
73	     1	# Frontend Dockerfile - Production Ready   ← début 3e Dockerfile + numéros
74	     2	FROM node:18-alpine AS builder
75	     3	
```

Le même problème touche le `.gitignore` (markers de diff `--- (原始)` / `+++ (修改后)` en chinois, soit "*original*" / "*modifié*").

### Origine probable
Copier-coller depuis une UI affichant des diffs numérotés — *ChatGPT*, *Cursor*, ou un agent qui a produit des outputs avec préfixes de lignes. Les fichiers ont ensuite été commités tels quels.

### Correctifs appliqués
| Fichier | Action |
|---|---|
| `frontend/Dockerfile` | Réécrit, multi-stage propre, BuildKit, non-root, `tini` PID 1 |
| `frontend/nginx.conf` | Headers sécurité, CSP, logs JSON, healthz dédié, port 8080 |
| `frontend/.dockerignore` | **Créé** — exclut `node_modules`, `dist`, `.env` |
| `.dockerignore` (racine) | **Créé** — exclut artefacts Python, frontend, secrets |
| `Dockerfile` (backend) | Multi-stage, image slim, non-root user, `tini`, asyncpg |
| `.gitignore` | Réécrit propre |
| `docker-compose.coolify.yml` | Build args alignés, healthchecks, ressources, secrets, security_opt |
| `.env.example` | Variables `VITE_*` ajoutées, structure clarifiée |
| `scripts/` | Build local, génération de secrets, healthcheck stack |

---

## 🏗️ Architecture cible

```
                ┌────────────────────────────────────────┐
                │         Coolify (Traefik/Caddy)        │
                │     HTTPS · Let's Encrypt · Routing    │
                └──────────────┬─────────────────────────┘
                               │
                ┌──────────────▼──────────────┐
                │   frontend (Nginx :8080)    │
                │   - SPA React/Vite          │
                │   - Reverse-proxy /api/ →   │
                └──────────────┬──────────────┘
                               │ /api/*
                ┌──────────────▼──────────────┐
                │      app (FastAPI :8000)    │
                │   - Plugin manager          │
                │   - Event Bus listener      │
                └──┬─────────────┬─────────┬──┘
                   │             │         │
            ┌──────▼──┐    ┌─────▼────┐  ┌─▼──────────┐
            │ Postgres│    │  Redis   │  │   Ollama   │
            │ (pgdata)│    │ (events) │  │  (LLM 8B)  │
            └─────────┘    └──────────┘  └────────────┘
```

**Réseau interne** : `prospector` (bridge), aucun port hors `frontend:8080` exposé à Coolify.

---

## 📁 Arborescence

```
ereputation2/
├── .dockerignore                    ← NOUVEAU
├── .env.example                     ← MIS À JOUR
├── .gitignore                       ← CORRIGÉ
├── Dockerfile                       ← BACKEND multi-stage
├── docker-compose.coolify.yml       ← CORRIGÉ
├── docker-compose.yml               ← (dev local, inchangé)
├── docker-compose.prod.yml          ← (HA + monitoring, inchangé)
├── main.py
├── requirements.txt
├── pyproject.toml
│
├── frontend/
│   ├── .dockerignore                ← NOUVEAU
│   ├── Dockerfile                   ← CORRIGÉ (3 stages)
│   ├── nginx.conf                   ← AMÉLIORÉ
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── src/
│       ├── App.tsx
│       ├── main.tsx
│       ├── components/
│       ├── pages/
│       ├── services/
│       ├── store/
│       └── types/
│
├── core/                            (config, event_bus, plugin_manager)
├── plugins/                         (11 plugins métier)
├── models/
├── services/
├── repositories/
├── utils/
│
└── scripts/                         ← NOUVEAU
    ├── build-local.sh
    ├── generate-secrets.sh
    └── healthcheck.sh
```

---

## ✅ Prérequis

### Serveur Coolify (production)
- Ubuntu 24.04 LTS · 4 vCPU · 8 GB RAM (16 GB si Ollama actif)
- Docker 29.x avec BuildKit (par défaut) et plugin Buildx
- Coolify ≥ 4.0
- Domaine pointé sur le serveur (ex. `prospect.le-publicitaire.fr`)

### Poste de développement
- Docker Desktop / Docker Engine ≥ 24
- Node.js ≥ 20 (pour dev frontend hors Docker)
- Python ≥ 3.11 (pour dev backend hors Docker)
- `make`, `openssl`, `git`

---

## 🛠️ Installation pas à pas

```bash
# 1. Cloner le projet
git clone https://github.com/epok/ereputation2.git
cd ereputation2

# 2. Appliquer les patchs (fichiers de ce livrable)
#    → Remplacer frontend/Dockerfile, frontend/nginx.conf, Dockerfile, .gitignore,
#      docker-compose.coolify.yml, .env.example
#    → Ajouter frontend/.dockerignore, .dockerignore, scripts/

# 3. Générer les secrets
chmod +x scripts/*.sh
./scripts/generate-secrets.sh > .env

# 4. Vérifier le .env (CORS_ORIGINS, domaine, clés API)
nano .env

# 5. Build local pour valider avant push
./scripts/build-local.sh all
```

---

## 🔐 Configuration `.env`

Voir [`.env.example`](./.env.example). Variables **obligatoires** pour démarrer :

| Variable | Description | Génération |
|---|---|---|
| `SECRET_KEY` | Signature JWT | `openssl rand -base64 48` |
| `POSTGRES_PASSWORD` | Mot de passe DB | `openssl rand -base64 32` |
| `REDIS_PASSWORD` | Mot de passe Redis | `openssl rand -base64 32` |
| `CORS_ORIGINS` | URL frontend autorisée | `https://prospect.le-publicitaire.fr` |

Variables **optionnelles** (selon plugins activés) : `INSEE_API_KEY`, `INSEE_API_SECRET`, `PAPPERS_API_KEY`, `OPENAI_API_KEY`, `SENTRY_DSN`, `SMTP_*`.

---

## 🚀 Lancement local

### Stack complète Docker
```bash
# Démarrage
docker compose -f docker-compose.coolify.yml up -d

# Vérifier l'état
docker compose -f docker-compose.coolify.yml ps
docker compose -f docker-compose.coolify.yml logs -f app

# Healthcheck stack complète
./scripts/healthcheck.sh http://localhost:8080
```

### Avec LLM local (Ollama)
```bash
docker compose -f docker-compose.coolify.yml --profile llm up -d
docker exec -it ereputation2-ollama-1 ollama pull llama3.1:8b
```

### Mode dev (frontend hot-reload, backend uvicorn --reload)
```bash
# Backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (autre terminal)
cd frontend && npm install && npm run dev
# → http://localhost:3000  (proxy Vite vers :8001)
```

---

## ☁️ Déploiement Coolify

### Étape 1 — Préparer Coolify
1. **New Resource → Docker Compose**
2. **Source** : votre dépôt Git (privé ou public)
3. **Branch** : `main`
4. **Build Pack** : `Docker Compose`
5. **Compose File** : `docker-compose.coolify.yml`

### Étape 2 — Configurer les variables
Dans Coolify > **Environment Variables**, copier-coller depuis `.env.example` toutes les variables, en remplaçant les valeurs `__CHANGE_ME__`. Cocher *Build-time* pour les `VITE_*`.

### Étape 3 — Configurer le domaine
Sur le service `frontend` :
- **Domain** : `prospect.le-publicitaire.fr`
- **Port** : `8080`
- **HTTPS** : automatique (Let's Encrypt via Coolify)

### Étape 4 — Premier déploiement
Cliquer **Deploy**. Suivre les logs jusqu'au `✔ healthy` sur les 3 services principaux.

### Étape 5 — Validation
```bash
./scripts/healthcheck.sh https://prospect.le-publicitaire.fr
```

---

## 🐛 Debug & Troubleshooting

| Symptôme | Cause probable | Solution |
|---|---|---|
| `unknown instruction "1"` au build | Fichier corrompu (numéros de ligne collés) | Remplacer par les Dockerfile de ce patch |
| `npm ci` échoue : `EUSAGE` | `package-lock.json` désynchronisé | `cd frontend && rm -rf node_modules package-lock.json && npm install` puis recommit |
| Frontend → backend : `502 Bad Gateway` | Service `app` pas encore `healthy` | Vérifier `depends_on.condition: service_healthy` |
| `PermissionError /app/logs/...` | Volumes Coolify avec permissions root | Les permissions sont fixées dans le Dockerfile (USER appuser après chown) |
| `Connection refused` Redis | `REDIS_PASSWORD` manquant ou différent | Aligner les valeurs `.env` ↔ Coolify |
| CORS bloqué | Frontend sur autre origine | Ajuster `CORS_ORIGINS` dans `.env` |
| Build OOM | Image Vite trop lourde | Augmenter RAM Coolify ou limiter via `node --max-old-space-size=2048` |
| TLS handshake error | DNS pas encore propagé | Attendre puis Force Renew dans Coolify |

### Logs utiles
```bash
# Coolify : depuis l'UI ou via SSH
docker compose -f docker-compose.coolify.yml logs -f --tail=100 app
docker compose -f docker-compose.coolify.yml logs -f --tail=100 frontend
docker compose -f docker-compose.coolify.yml logs -f --tail=100 db
```

---

## 🛡️ Checklist Production

| | Item | État |
|---|---|---|
| ☑ | Secrets injectés via env runtime (pas de hardcode) | ✅ |
| ☑ | `.dockerignore` à la racine ET dans `frontend/` | ✅ |
| ☑ | Healthchecks sur tous les services | ✅ |
| ☑ | Logs JSON + rotation (10MB × 5-10 fichiers) | ✅ |
| ☑ | Non-root user dans frontend ET backend | ✅ |
| ☑ | Images multi-stage + Alpine/slim | ✅ |
| ☑ | `tini` PID 1 (graceful shutdown) | ✅ |
| ☑ | Limites CPU/RAM (`deploy.resources.limits`) | ✅ |
| ☑ | `security_opt: no-new-privileges` | ✅ |
| ☑ | Frontend `read_only` + `tmpfs` | ✅ |
| ☑ | Headers sécurité (CSP, HSTS, X-Frame-Options) | ✅ |
| ☑ | Compression Gzip activée | ✅ |
| ☑ | Cache long pour assets immutables (Vite hash) | ✅ |
| ☑ | Healthcheck `/healthz` dédié (vs `/`) | ✅ |
| ☑ | Variables `${VAR:?}` qui échouent fast si manquantes | ✅ |
| ☑ | Postgres 16 + paramètres prod (slow query log) | ✅ |
| ☑ | Redis avec auth + maxmemory + LRU | ✅ |
| ☑ | Cache mounts BuildKit (`--mount=type=cache`) | ✅ |
| ⏳ | Tests CI/CD (GitHub Actions / GitLab CI) | À ajouter |
| ⏳ | Backups automatiques DB | À configurer dans Coolify |
| ⏳ | Monitoring Sentry/Prometheus | DSN à fournir |
| ⏳ | Scan vuln Trivy/Snyk | À intégrer en CI |

---

## 🌟 Recommandations 360°

Voir [`docs/RECOMMENDATIONS.md`](./docs/RECOMMENDATIONS.md) pour le plan d'amélioration complet (sécurité, observabilité, scalabilité, RGPD, CI/CD, qualité code).

### Top 10 priorités
1. **CI/CD GitHub Actions** : lint + tests + scan Trivy + push image
2. **Pre-commit hooks** : `ruff`, `black`, `eslint`, `tsc --noEmit`
3. **Backups Postgres** : Coolify backups quotidiens vers S3/B2
4. **Sentry** : observabilité erreurs frontend + backend
5. **Authentification** : JWT + refresh token + rate limit `slowapi`
6. **Tests** : pytest + Vitest + Playwright (E2E sur les 3 parcours clés)
7. **DB migrations** : Alembic (manquant dans le projet)
8. **API versioning** : `/api/v1` strict + dépréciation contrôlée
9. **Conformité RGPD** : registre traitements, export/effacement RGPD
10. **Documentation API** : OpenAPI déjà présent via FastAPI, exposer Redoc public

---

## 📜 Licence
Propriétaire — Epok / Le Publicitaire. Tous droits réservés.

## 👤 Contact
- **Client** : Epok (laserandco.fr)
- **Domaine** : `prospect.le-publicitaire.fr`
- **Support technique** : voir issues GitHub
