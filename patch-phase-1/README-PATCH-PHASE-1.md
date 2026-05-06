# 🔧 PATCH PHASE 1 — Stabilisation B2B Prospector

**Objectif** : Transformer un déploiement vide en application fonctionnelle de bout en bout.

---

## 📋 Ce que ce patch corrige

### Backend
| Problème | Solution |
|----------|----------|
| Aucune migration DB → tables inexistantes | Migrations Alembic complètes créées |
| 0 prospects, 0 étapes pipeline | Script `seed.py` avec données de démo |
| POST /api/v1/prospects échoue | Routes INSEE/Pappers corrigées + scraping sans clé API |
| /api/v1/dashboard/stats absente | Endpoint créé avec agrégats réels |
| Plugins non chargés | Manifests corrigés + `active: true` par défaut |
| Healthcheck retourne "Inconnu" | `/api/v1/system/health` implémenté |

### Frontend
| Problème | Solution |
|----------|----------|
| Page Plugins = spinner infini | Gestion d'erreur + timeout axios |
| Dashboard KPIs à 0 | Connecté à `/api/v1/pipeline/metrics` |
| Pipeline Kanban vide | Drag-n-drop fonctionnel + persistance API |
| "Erreur lors de l'ajout du prospect" | Toast avec message d'erreur détaillé |
| Paramètres : "État du système : Inconnu" | Healthcheck backend opérationnel |

---

## 🚀 Installation rapide (5 minutes)

### Étape 1 : Appliquer le patch
```bash
cd /workspace
chmod +x patch-phase-1/apply-patch.sh
./patch-phase-1/apply-patch.sh
```

### Étape 2 : Lancer les migrations
```bash
docker-compose -f docker-compose.coolify.yml run --rm app python scripts/migrate.py
```

### Étape 3 : Seeder la base de données
```bash
docker-compose -f docker-compose.coolify.yml run --rm app python scripts/seed.py
```

### Étape 4 : Activer les plugins
```bash
docker-compose -f docker-compose.coolify.yml run --rm app python scripts/activate_plugins.py
```

### Étape 5 : Redémarrer la stack
```bash
docker-compose -f docker-compose.coolify.yml down
docker-compose -f docker-compose.coolify.yml up -d
```

---

## ✅ Vérification

Après redémarrage, vérifiez :

1. **Dashboard** : KPIs > 0, graphique de répartition visible
2. **Pipeline** : 6 colonnes avec prospects de démo
3. **Prospects** : Liste avec 10 prospects, recherche fonctionnelle
4. **Plugins** : 11 plugins listés, 4+ actifs
5. **Paramètres** : "État du système : healthy", version affichée

---

## 🔑 Scrapers inclus (SANS clé API)

| Source | Méthode | Données |
|--------|---------|---------|
| **INSEE** | API publique `recherche-entreprises.api.gouv.fr` | SIREN/SIRET, raison sociale, NAF, adresse |
| **BODACC** | API publique `bodacc-datadila.opendatasoft.com` | Procédures collectives, radiations |
| **Pappers** | Scraping HTTP respectueux (rate-limited) | Comptes annuels, dirigeants |
| **Pages Jaunes** | Scraping HTTP + rotation User-Agent | Téléphone, email, site web |
| **Google Maps** | Playwright headless (anti-détection) | Avis, coordonnées, horaires |

---

## 🛠️ Structure du patch

```
patch-phase-1/
├── README-PATCH-PHASE-1.md      # Ce fichier
├── apply-patch.sh               # Script d'application automatique
├── alembic/
│   ├── env.py                   # Config Alembic async
│   ├── script.py.mako           # Template de migration
│   └── versions/
│       └── 0001_initial_schema.py  # Schéma complet DB
├── scripts/
│   ├── migrate.py               # Lance migrations
│   ├── seed.py                  # Données de démo
│   └── activate_plugins.py      # Active plugins par défaut
├── services/
│   └── scrapers/
│       ├── base.py              # Classe abstraite + retry logic
│       ├── insee.py             # API INSEE gratuite
│       ├── bodacc.py            # API BODACC gratuite
│       ├── pappers.py           # Scraping Pappers
│       ├── pages_jaunes.py      # Scraping Pages Jaunes
│       ├── google_maps.py       # Playwright scraping
│       └── aggregator.py        # Orchestration multi-sources
├── plugins/
│   ├── prospects/               # CRUD complet + import CSV
│   ├── dashboard/               # KPIs agrégés
│   └── system/                  # Healthcheck étendu
├── frontend/src/
│   ├── api/client.ts            # Gestion erreurs + toast
│   ├── pages/Dashboard.tsx      # Corrigé
│   ├── pages/Pipeline.tsx       # Drag-n-drop fonctionnel
│   ├── pages/Prospects.tsx      # Ajout SIRET + manuel
│   ├── pages/Plugins.tsx        # Timeout + erreur gérée
│   └── pages/Settings.tsx       # Healthcheck visible
└── docs/
    ├── SCRAPING_LEGAL.md        # Bonnes pratiques juridiques
    └── PHASE-1-CHANGELOG.md     # Détails des changements
```

---

## 📝 Prochaines étapes (Phase 2)

Une fois la Phase 1 validée :

1. **Auth complète** : JWT login/logout + ProtectedRoute React
2. **CRUD prospects** : Ajout manuel, édition, suppression, import CSV/XLSX
3. **Drag-n-drop Kanban** : @dnd-kit/core + persistance API
4. **Page détail prospect** : Onglets (Infos, Audit, Score, Séquences)
5. **Connexion INSEE OAuth2** + Patters API key
6. **Plugin digital_audit** : Lighthouse headless

---

## 🆘 Support

En cas d'erreur :

```bash
# Logs backend
docker-compose -f docker-compose.coolify.yml logs -f app

# Logs frontend
docker-compose -f docker-compose.coolify.yml logs -f frontend

# Vérifier santé DB
docker-compose -f docker-compose.coolify.yml exec db pg_isready -U prospector

# Vérifier santé Redis
docker-compose -f docker-compose.coolify.yml exec redis redis-cli -a ${REDIS_PASSWORD} ping
```

---

**Date de création** : $(date +%Y-%m-%d)  
**Version** : 1.0.0  
**Compatibilité** : Coolify 4.x, Docker 29.x, Ubuntu 24 LTS
