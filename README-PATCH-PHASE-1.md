# 📦 PATCH PHASE 1 — B2B Prospector

> Patch de stabilisation transformant un déploiement vide
> en application B2B fonctionnelle de bout en bout.
> Version : **1.1.0** — Repo : `LePubli/ereputation2`
> Production : `https://prospect.le-publicitaire.fr`

---

## 🎯 Objectif

Corriger les 6 dysfonctionnements bloquants identifiés sur la production :

| Symptôme observé                                       | Origine                                          | ✅ Corrigé par                              |
|--------------------------------------------------------|--------------------------------------------------|---------------------------------------------|
| Dashboard tous les KPI à 0                              | Plugin dashboard non chargé                      | `core/plugin_loader.py` + plugin actif      |
| « Erreur lors de l'ajout du prospect »                  | Routes prospects manquantes                     | Plugin prospects + scrapers INSEE/BODACC… |
| Page Plugins en chargement infini                       | Endpoint `/plugins` absent                       | Plugin system + table `plugin_states`      |
| « État du système : Inconnu »                           | Endpoint `/system/info` absent                   | `plugins/system/routes.py`                  |
| Pipeline Kanban : 4 colonnes vides                      | Aucune étape + aucun prospect en BDD            | Migrations + seed                            |
| Aucune route plugin disponible (4 routes seulement)     | Loader plugin défaillant                        | Migrations Alembic + chargement explicite  |

---

## 📋 Prérequis

| Outil          | Version mini | Utilité                                |
|----------------|--------------|----------------------------------------|
| Docker         | 24.0+        | Conteneurisation                        |
| Docker Compose | 2.20+        | Orchestration                          |
| Coolify        | 4.x          | Déploiement (production)                |
| Python         | 3.11+        | Backend (dev local seulement)          |
| Node.js        | 20+          | Frontend (dev local seulement)         |
| Git            | 2.40+        | Clonage du repo                        |

**Côté serveur** : Ubuntu 22.04 / 24.04 LTS — au moins **2 vCPU + 4 Go RAM** + 20 Go SSD.

---

## 📁 Contenu du patch

```
patch-phase-1/
├── README-PATCH-PHASE-1.md          ← (ce fichier)
├── apply-patch.sh                   ← Script d'application
├── .env.example                     ← Variables mises à jour
├── alembic.ini, alembic/            ← Migrations BDD
├── core/                            ← Config + DB + sécurité + loader plugin
├── models/                          ← SQLAlchemy + Pydantic
├── plugins/                         ← prospects, pipeline, dashboard, system
├── services/scrapers/               ← INSEE, BODACC, Pappers, PJ, Google Maps
├── scripts/                         ← seed, migrate.sh, activate_plugins
├── frontend/                        ← React/TS complet
├── docker-compose.coolify.yml       ← Compose pour Coolify
├── Dockerfile                       ← Backend Python + Playwright
├── requirements.txt
├── main.py
└── docs/
    ├── SCRAPING_LEGAL.md
    └── PHASE-1-CHANGELOG.md
```

---

## 🚀 Installation étape par étape

### Étape 1 — Cloner le repo cible

```bash
git clone https://github.com/LePubli/ereputation2.git
cd ereputation2
git checkout -b patch-phase-1
```

### Étape 2 — Récupérer le patch

```bash
# Décompresser l'archive du patch dans le repo
unzip /chemin/vers/patch-phase-1.zip
# Doit créer : ./patch-phase-1/
```

### Étape 3 — Appliquer le patch

```bash
bash patch-phase-1/apply-patch.sh
```

Ce script :
- Sauvegarde `.env` existant en `.env.backup.YYYYMMDD_HHMMSS`
- Copie tous les fichiers du patch dans le repo
- Met le `scripts/migrate.sh` exécutable
- Affiche un récapitulatif des étapes suivantes

### Étape 4 — Configurer `.env`

Si premier déploiement :

```bash
cp .env.example .env
nano .env
```

**Variables critiques à renseigner** :

```bash
# Sécurité — Générer avec `openssl rand -base64 48`
SECRET_KEY=...
POSTGRES_PASSWORD=...
REDIS_PASSWORD=...
ADMIN_PASSWORD=...

# CORS — Domaine de production
CORS_ORIGINS=https://prospect.le-publicitaire.fr,http://localhost:3000

# SMTP PlanetHoster
SMTP_HOST=mail.le-publicitaire.fr
SMTP_PORT=587
SMTP_USER=noreply@le-publicitaire.fr
SMTP_PASSWORD=...

# Admin par défaut (créé au premier seed)
ADMIN_EMAIL=admin@le-publicitaire.fr
```

### Étape 5 — Build & test local

```bash
# Lance toute la stack
docker compose -f docker-compose.coolify.yml up --build

# Dans un autre terminal, observe les logs
docker compose -f docker-compose.coolify.yml logs -f migrate backend
```

**Logs attendus à la première exécution** :

```
✓ Connexion DB
✓ Migrations Alembic appliquées (revision 0001)
✓ Admin créé : admin@le-publicitaire.fr
✓ 6 étapes pipeline en base
✓ 13 plugins enregistrés
✓ 10 prospects de démo insérés
✅ Seed terminé
…
✓ Plugin system chargé (4 routes)
✓ Plugin prospects chargé (8 routes)
✓ Plugin pipeline chargé (5 routes)
✓ Plugin dashboard chargé (1 routes)
📦 Plugins actifs : system, prospects, pipeline, dashboard
```

### Étape 6 — Vérifier les routes

```bash
curl http://localhost:8080/api/v1/system/info | jq
curl http://localhost:8080/api/v1/dashboard/stats | jq
curl http://localhost:8080/api/v1/prospects?page=1 | jq
curl http://localhost:8080/api/v1/pipeline/board | jq
curl http://localhost:8080/api/v1/plugins | jq
```

Ouvrir ensuite : **http://localhost:8080**

---

## ⚙️ Configuration `.env` détaillée

| Variable                       | Défaut                          | Description                                    |
|--------------------------------|---------------------------------|------------------------------------------------|
| `APP_ENV`                      | `production`                    | Environnement (production / development)        |
| `DEBUG`                        | `false`                         | Active SQL echo + reload                       |
| `LOG_LEVEL`                    | `INFO`                          | Niveau de log loguru                           |
| `SECRET_KEY`                   | —                               | Clé JWT (32+ chars). À générer.               |
| `POSTGRES_*`                   | —                               | Config Postgres                                |
| `REDIS_PASSWORD`               | —                               | Mot de passe Redis                             |
| `ADMIN_EMAIL`                  | `admin@le-publicitaire.fr`      | Compte admin créé au seed                      |
| `ADMIN_PASSWORD`               | —                               | Mot de passe initial                           |
| `SCRAPER_TIMEOUT`              | `30`                            | Timeout HTTP (secondes)                        |
| `SCRAPER_CACHE_TTL_HOURS`      | `24`                            | TTL du cache `scrape_cache`                    |
| `PLAYWRIGHT_HEADLESS`          | `true`                          | Mode headless pour Google Maps                 |
| `SMTP_HOST`                    | `mail.le-publicitaire.fr`       | SMTP PlanetHoster                              |

---

## 🐛 Debug

### Backend ne démarre pas

```bash
docker compose logs backend
# ou
docker compose -f docker-compose.coolify.yml logs --tail=100 backend
```

**Erreurs fréquentes** :

| Erreur                                        | Solution                                                  |
|-----------------------------------------------|-----------------------------------------------------------|
| `relation "users" does not exist`             | Le service `migrate` n'a pas tourné. Relancer manuellement. |
| `connection refused on db:5432`               | Postgres pas prêt. Vérifier le healthcheck.               |
| `ModuleNotFoundError: core.config`            | PYTHONPATH manquant. Vérifier que le code est en `/app`. |

### Forcer une migration manuelle

```bash
docker compose exec backend bash scripts/migrate.sh
```

### Vérifier les routes chargées

```bash
docker compose exec backend curl http://localhost:8000/openapi.json | jq '.paths | keys'
```

Doit retourner **18+ routes** (vs 4 avant patch).

### Frontend affiche une page blanche

```bash
docker compose logs frontend
docker compose exec frontend ls /usr/share/nginx/html
```

Vérifier que `index.html` et `assets/` existent.

### Reset complet base + cache

```bash
docker compose -f docker-compose.coolify.yml down -v
docker compose -f docker-compose.coolify.yml up --build
```

⚠️ Supprime aussi les données. Réservé au dev.

---

## 🚢 Déploiement sur Coolify

### Configuration côté Coolify

1. **Source** : Git → repo GitHub `LePubli/ereputation2`, branche `patch-phase-1` (ou main après merge)
2. **Build** : Docker Compose
3. **Compose file** : `docker-compose.coolify.yml`
4. **Environment** : copier le contenu de `.env` (toutes les valeurs)
5. **Domaine** : `prospect.le-publicitaire.fr` → service `frontend` port 8080
6. **Persistance** : volumes `postgres_data` et `redis_data` activés
7. **Build args** : `VITE_API_URL=/api/v1`

### Première fois (avec seed)

Le service `migrate` se charge des migrations + seed automatiquement au premier déploiement.

Vérifier les logs Coolify : doit afficher `✅ Seed terminé`.

### Déploiements suivants

Le service `migrate` est idempotent : il ne re-seed pas si la BDD contient déjà les données. Aucune action manuelle requise.

### Rollback en cas de pépin

```bash
# Sur le serveur Coolify
docker compose -f docker-compose.coolify.yml down
git checkout <commit-d-avant-patch>
# Redéployer depuis Coolify
```

⚠️ Avant rollback : `pg_dump` la base !

---

## 📊 Exemples d'utilisation

### Ajouter un prospect via SIRET (avec scraping)

**Via UI** : Page Prospects → bouton « Ajouter un prospect » → onglet « Par SIREN/SIRET » → entrer `552120222` (Renault) → Créer.

**Via API** :

```bash
curl -X POST https://prospect.le-publicitaire.fr/api/v1/prospects/by-siret \
  -H "Content-Type: application/json" \
  -d '{"identifier": "552120222"}'
```

**Réponse type** :

```json
{
  "id": "...",
  "company_name": "RENAULT",
  "siren": "552120222",
  "naf_code": "29.10Z",
  "naf_label": "Construction de véhicules automobiles",
  "city": "BOULOGNE-BILLANCOURT",
  "sources_used": ["insee", "bodacc", "pappers"],
  "enrichment": {...},
  "contacts": [{"first_name": "Luca", "last_name": "...", "role": "Directeur Général"}]
}
```

### Importer un CSV

Format attendu (séparateur `,` ou `;`) :

```csv
company_name,siren,city,postal_code,phone,email,website
Boulangerie Test,123456789,Lille,59000,0320000001,test@example.fr,https://example.fr
...
```

**Via UI** : Page Prospects → « Importer CSV » → drag-n-drop le fichier.

**Via API** :

```bash
curl -X POST https://prospect.le-publicitaire.fr/api/v1/prospects/import \
  -F "file=@prospects.csv"
```

### Drag-n-drop dans le Kanban

UI uniquement. Glisser une carte d'une colonne à l'autre déclenche `PATCH /api/v1/prospects/{id}/stage` automatiquement.

### Récupérer les KPI

```bash
curl https://prospect.le-publicitaire.fr/api/v1/dashboard/stats | jq
```

```json
{
  "kpi": {
    "total_prospects": 11,
    "conversion_rate": 9.09,
    "estimated_revenue": 152500.0,
    "active_plugins": 9
  },
  "distribution": [
    {"stage_name": "Nouveau", "color": "#3b82f6", "count": 2},
    {"stage_name": "Contacté", "color": "#eab308", "count": 2},
    ...
  ]
}
```

---

## 🛠️ Développement local (sans Docker)

### Backend

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# Lance Postgres + Redis avec Docker
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=prospector -e POSTGRES_DB=prospector --name pg postgres:16-alpine
docker run -d -p 6379:6379 --name redis redis:7-alpine

# Variables d'env (sans Docker, host=localhost)
export DATABASE_URL=postgresql+asyncpg://postgres:prospector@localhost:5432/prospector
export REDIS_URL=redis://localhost:6379/0

bash scripts/migrate.sh
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev    # http://localhost:3000 (proxy /api → :8000)
```

---

## 📚 Documentation API

Une fois déployé, la doc Swagger interactive est disponible sur :

- **Swagger UI** : `https://prospect.le-publicitaire.fr/docs`
- **ReDoc** : `https://prospect.le-publicitaire.fr/redoc`
- **OpenAPI JSON** : `https://prospect.le-publicitaire.fr/openapi.json`

---

## ⚖️ Avertissement légal sur le scraping

Voir **[docs/SCRAPING_LEGAL.md](docs/SCRAPING_LEGAL.md)** pour le détail.

**Points clés** :
- INSEE & BODACC : 100 % légal (API publiques data.gouv.fr)
- Pappers, Pages Jaunes : zone grise — délais polite + cache 24h
- Google Maps : à utiliser avec parcimonie (Playwright headless)
- À grand volume (>100 req/jour) → migrer vers les API officielles

---

## 🔜 Roadmap Phase 2 (à venir)

- 🔐 Authentification JWT complète (login + refresh + middleware)
- 👥 CRUD complet sur contacts (UI)
- 📋 Vue détail prospect (drawer latéral)
- 🎨 Réordonnancement des étapes par drag (UI)
- 🔍 Filtres avancés sur la liste prospects (NAF, ville, score…)
- 📧 Module emailing (séquences, templates)
- 🤖 Phase 3 : automation engine + scoring prédictif
- 📱 Phase 5 : application Android Studio Kotlin

---

## 📝 Licence & support

- **Licence** : propriétaire — © Le Publicitaire
- **Mainteneur** : Epok
- **Issues** : repo GitHub `LePubli/ereputation2` → Issues
- **Contact** : `admin@le-publicitaire.fr`
