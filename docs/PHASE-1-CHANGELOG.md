# 📦 Phase 1 — Changelog

> Patch de stabilisation : transforme le déploiement vide en application B2B
> fonctionnelle de bout en bout.

## ✨ Nouveautés

### 🗄️ Base de données
- **Migrations Alembic complètes** : 0001_initial_schema.py
- 7 tables créées : `users`, `pipeline_stages`, `prospects`, `contacts`, `plugin_states`, `audit_logs`, `scrape_cache`
- Extension `pg_trgm` activée (recherche fuzzy)
- Index optimisés sur SIREN, SIRET, ville, étape

### 🌱 Seed initial
- Création automatique de l'admin (depuis `ADMIN_EMAIL` / `ADMIN_PASSWORD`)
- 6 étapes de pipeline par défaut : Nouveau → Contacté → RDV pris → En négociation → Gagné / Perdu
- 13 plugins enregistrés (4 core + 5 scrapers + 4 futurs)
- 10 prospects de démo en Hauts-de-France (Roubaix, Lille, Tourcoing, Wattrelos)

### 🔌 Plugins backend
- **Loader corrigé** : les routes core sont chargées au boot via `core/plugin_loader.py`
- Plugin `prospects` : CRUD complet + ajout par SIRET + import CSV/XLSX + ré-enrichissement
- Plugin `pipeline` : Kanban + drag-n-drop + gestion des étapes
- Plugin `dashboard` : KPI agrégés + répartition par étape
- Plugin `system` : `/health`, `/info`, gestion des plugins

### 🌐 Scrapers (5 sources, sans clé API)
- **INSEE** via `recherche-entreprises.api.gouv.fr` (API publique)
- **BODACC** via `bodacc-datadila.opendatasoft.com` (API publique)
- **Pappers** via scraping HTTP respectueux (délai 2s)
- **Pages Jaunes** via scraping HTTP (délai 3s)
- **Google Maps** via Playwright headless avec anti-détection
- **Aggregator** : orchestre les 5 sources en parallèle, fusionne les données, gère le cache 24h

### 🎨 Frontend
- Toutes les pages corrigées :
  - **Dashboard** : KPI réels + graphique recharts
  - **Pipeline** : Kanban drag-n-drop avec @dnd-kit/core
  - **Prospects** : table avec recherche, pagination, modale d'ajout (SIRET ou manuel), import CSV
  - **Plugins** : liste avec toggle actif/inactif (plus de spinner infini)
  - **Settings** : état système réel (DB, Redis, plugins, uptime)
- Client API axios avec gestion d'erreur centralisée
- Toasts (Sonner) : succès/erreurs/info
- Composants UI : EmptyState, Skeleton, Spinner, ErrorBoundary
- React Query pour cache + invalidation intelligente

### 🐳 Infrastructure
- `docker-compose.coolify.yml` avec service `migrate` (init container)
- Migrations + seed exécutés automatiquement au déploiement
- Healthchecks sur tous les services
- Dockerfile backend avec Playwright Chromium pré-installé

## 🐛 Corrections

| Problème initial                                        | Correction                                                                |
|---------------------------------------------------------|---------------------------------------------------------------------------|
| Dashboard tous KPI à 0                                  | Plugin dashboard chargé + agrégats SQL réels                              |
| « Erreur lors de l'ajout du prospect »                  | Routes `/prospects` + `POST /by-siret` actives + scraper INSEE            |
| Page Plugins en chargement infini                       | Plugin `system` charge `/api/v1/plugins` depuis la table `plugin_states`  |
| Settings « État système : Inconnu »                     | Endpoint `/api/v1/system/info` retourne uptime, DB, Redis, plugins        |
| Pipeline 4 colonnes vides                                | Seed crée 6 étapes + 10 prospects répartis                                |
| Aucune route plugin chargée                             | `core/plugin_loader.py` lit `plugin_states` et charge les routers actifs  |

## 📈 Endpoints API

```
GET    /api/v1/system/health
GET    /api/v1/system/info
GET    /api/v1/plugins
POST   /api/v1/plugins/{name}/toggle

GET    /api/v1/prospects                    Liste paginée
POST   /api/v1/prospects                    Création manuelle
POST   /api/v1/prospects/by-siret           Création + enrichissement multi-sources
POST   /api/v1/prospects/import             Import CSV/XLSX
GET    /api/v1/prospects/{id}
PATCH  /api/v1/prospects/{id}
PATCH  /api/v1/prospects/{id}/stage         Drag-n-drop Kanban
DELETE /api/v1/prospects/{id}
POST   /api/v1/prospects/{id}/enrich        Ré-enrichissement

GET    /api/v1/pipeline/board               Kanban complet
GET    /api/v1/pipeline/stages
POST   /api/v1/pipeline/stages
PATCH  /api/v1/pipeline/stages/{id}
DELETE /api/v1/pipeline/stages/{id}

GET    /api/v1/dashboard/stats              KPIs + distribution
```

## 🔜 Phase 2 (à venir)

- Authentification JWT complète (login/refresh)
- CRUD complet sur contacts (UI)
- Vue détail prospect (drawer)
- Gestion des étapes via UI (drag pour réordonner)
- Filtres avancés sur la liste prospects
- API officielle Pappers/INSEE en option
