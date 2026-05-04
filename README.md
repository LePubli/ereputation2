# 🚀 B2B Prospector

**Copilote commercial B2B intelligent, modulaire et production-ready**

Une application de prospection B2B qui collecte des données publiques vérifiées, audite la présence digitale, et génère des angles commerciaux basés sur des faits (0% hallucination).

## ✨ Fonctionnalités

### Core Features
- **Collecte de données légales** via API INSEE/Pappers (SIRET, raison sociale, NAF, effectifs)
- **Audit digital complet** : CMS, analytics, pixels, SEO, performance, conformité RGPD
- **Génération d'angles commerciaux** basée sur un moteur de règles déterministe
- **Pipeline Kanban** pour le suivi des prospects avec métriques et alertes
- **Architecture plugin** pour une extensibilité maximale

### 🆕 Plugins Avancés (Nouveautés!)
- **📧 Outreach Multi-Channel** : Séquences automatisées Email, LinkedIn, WhatsApp avec personnalisation IA
- **🧠 Semantic Analyzer** : Analyse NLP du contenu web pour détecter douleurs et valeurs
- **🎯 Predictive Scorer** : Scoring prédictif de propension à l'achat (HOT/WARM/COLD)
- **🎙️ Voice Assistant** : Transcription et analyse d'appels avec détection d'objections
- **📊 A/B Testing** : Optimisation scientifique des campagnes (sujets, templates, canaux)
- **⚙️ Automation Engine** : Workflows automatisés et triggers événementiels
- **🛡️ Compliance Guard** : Gestion RGPD, consentement et désinscription automatique

### Principes Architecturaux
- ✅ **Core + Plugins** : Architecture modulaire avec plugins activables/désactivables
- ✅ **Zero Hallucination** : Toute donnée est traçable à une source publique vérifiée
- ✅ **100% Open-Source** : Aucune dépendance payante
- ✅ **Production-Ready** : Docker, tests, logs structurés, monitoring
- ✅ **RGPD Compliant** : Données B2B uniquement, traçabilité, droit à l'oubli

## 🏗️ Architecture

```
/workspace
├── core/                    # Core minimaliste
│   ├── config.py           # Configuration et settings
│   ├── event_bus.py        # Redis Pub/Sub pour communication
│   └── plugin_manager.py   # Découverte et chargement des plugins
├── plugins/                 # Plugins fonctionnels
│   ├── scraper-insee/      # Récupération données légales
│   ├── audit-digital/      # Audit présence digitale
│   ├── pain-point-engine/  # Génération angles commerciaux
│   ├── pipeline-kanban/    # Gestion visuelle des prospects
│   ├── semantic-analyzer/  # Analyse NLP contenu web 🆕
│   ├── predictive-scorer/  # Scoring prédictif 🆕
│   ├── outreach-multichannel/ # Séquences auto Email/LinkedIn/WhatsApp 🆕
│   ├── voice-assistant/    # Transcription & analyse appels 🆕
│   ├── ab-testing/         # Optimisation campagnes 🆕
│   ├── automation-engine/  # Workflows automatisés 🆕
│   └── compliance-guard/   # Conformité RGPD 🆕
├── api/                     # Routes API
├── models/                  # Modèles de données
├── services/                # Services métier
├── utils/                   # Utilitaires
├── tests/                   # Tests unitaires et d'intégration
├── main.py                  # Point d'entrée FastAPI
├── requirements.txt         # Dépendances Python
├── Dockerfile              # Containerisation
└── docker-compose.yml      # Orchestration
```

## 🚀 Démarrage Rapide

### Option 1 : Docker (Recommandé)

```bash
# Cloner le projet
git clone <repository-url>
cd b2b-prospector

# Lancer avec Docker Compose
docker-compose up -d

# Vérifier que l'application tourne
curl http://localhost:8000/health
```

### Option 2 : Développement Local

```bash
# Installer les dépendances
pip install -r requirements.txt

# Copier le fichier d'environnement
cp .env.example .env

# Lancer l'application
python main.py

# Ou avec auto-reload pour le développement
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📡 API Endpoints

### Santé & Information
- `GET /` - Page d'accueil avec informations
- `GET /health` - Health check
- `GET /ready` - Readiness check
- `GET /api/v1/endpoints` - Liste tous les endpoints
- `GET /api/v1/plugins` - Liste les plugins

### Plugin: Scraper INSEE
- `POST /api/v1/prospects` - Créer un prospect par SIRET
- `GET /api/v1/prospects/{siren}` - Récupérer infos légales
- `GET /api/v1/prospects/search?q={query}` - Recherche entreprise

### Plugin: Audit Digital
- `POST /api/v1/audit/digital/{prospect_id}` - Lancer un audit
- `GET /api/v1/audit/digital/{prospect_id}` - Récupérer résultats
- `GET /api/v1/audit/digital/{prospect_id}/score` - Score de maturité

### Plugin: Pain Point Engine
- `POST /api/v1/angles/generate` - Générer angles commerciaux
- `GET /api/v1/angles/{prospect_id}` - Liste des angles
- `POST /api/v1/angles/{angle_id}/format` - Reformuler avec LLM

### Plugin: Pipeline Kanban
- `GET /api/v1/pipeline` - Vue Kanban complète
- `PATCH /api/v1/pipeline/{prospect_id}/stage` - Changer étape
- `GET /api/v1/pipeline/metrics` - Métriques du pipeline
- `POST /api/v1/pipeline/{prospect_id}/interactions` - Ajouter interaction
- `GET /api/v1/pipeline/alerts` - Alertes prospects

### 🆕 Plugin: Semantic Analyzer
- `POST /api/v1/semantic/analyze` - Analyser le contenu d'un site web
- `GET /api/v1/semantic/pain-points/categories` - Catégories de douleurs détectables

### 🆕 Plugin: Predictive Scorer
- `POST /api/v1/score/calculate` - Calculer le score prédictif d'un prospect
- `GET /api/v1/score/{prospect_id}` - Récupérer le score et ses composantes
- `GET /api/v1/score/breakdown` - Détail du scoring par dimension

### 🆕 Plugin: Outreach Multi-Channel
- `POST /api/v1/outreach/sequences` - Créer une séquence multi-canal
- `POST /api/v1/outreach/email/generate` - Générer un email personnalisé
- `POST /api/v1/outreach/email/send` - Envoyer un email
- `POST /api/v1/outreach/linkedin/send` - Envoyer un message LinkedIn
- `POST /api/v1/outreach/whatsapp/send` - Envoyer un message WhatsApp
- `GET /api/v1/outreach/stats` - Statistiques des campagnes

### 🆕 Plugin: Voice Assistant
- `POST /api/v1/voice/transcribe` - Transcrire un fichier audio
- `POST /api/v1/voice/analyze` - Analyser une transcription d'appel
- `POST /api/v1/voice/upload-and-analyze` - Workflow complet upload + analyse
- `POST /api/v1/voice/batch-analyze` - Analyser plusieurs appels en batch

### 🆕 Plugin: A/B Testing
- `POST /api/v1/ab-testing/tests` - Créer un test A/B
- `GET /api/v1/ab-testing/tests` - Lister tous les tests
- `POST /api/v1/ab-testing/tests/{id}/start` - Démarrer un test
- `POST /api/v1/ab-testing/events` - Enregistrer un événement de conversion
- `GET /api/v1/ab-testing/tests/{id}/winner` - Récupérer le gagnant
- `GET /api/v1/ab-testing/sample-size-calculator` - Calculateur de taille d'échantillon

### 🆕 Plugin: Automation Engine
- `POST /api/v1/automation/workflows` - Créer un workflow automatisé
- `GET /api/v1/automation/triggers` - Liste des triggers disponibles
- `POST /api/v1/automation/execute` - Exécuter un workflow manuellement

### 🆕 Plugin: Compliance Guard
- `POST /api/v1/compliance/check` - Vérifier la conformité RGPD
- `POST /api/v1/compliance/opt-out` - Gérer une demande de désinscription
- `GET /api/v1/compliance/audit-log` - Consulter le journal d'audit

## 🔌 Système de Plugins

### Activer/Désactiver un Plugin

```bash
# Via API
curl -X POST http://localhost:8000/api/v1/plugins/audit-digital/enable
curl -X POST http://localhost:8000/api/v1/plugins/audit-digital/disable
```

### Créer un Nouveau Plugin

1. Créer un dossier dans `/plugins/`
2. Ajouter un `manifest.yaml` :
```yaml
name: mon-plugin
version: 1.0.0
description: Description du plugin
dependencies: []
events_published: []
events_subscribed: []
endpoints: []
```

3. Implémenter `main.py` avec les handlers

## 📊 Score de Maturité Digitale

L'audit digital calcule un score (0-100) basé sur 5 dimensions :

| Dimension | Poids | Critères |
|-----------|-------|----------|
| Présence | 30% | Site actif, réseaux sociaux, meta tags |
| Modernité | 25% | CMS récent, HTTPS, performance |
| Tracking | 20% | Google Analytics, Meta Pixel, GTM |
| Conformité | 15% | RGPD, cookies, mentions légales |
| Engagement | 10% | Newsletter, chat, prise de RDV |

## 🔒 RGPD & Conformité

- ✅ Données B2B uniquement (personnes morales)
- ✅ Sources publiques vérifiées (INSEE, open data)
- ✅ Traçabilité complète des données
- ✅ Droit à l'oubli implémentable
- ✅ Pas de scraping agressif (rate limiting)

## 🧪 Tests

```bash
# Lancer les tests
pytest

# Avec couverture de code
pytest --cov=. --cov-report=html

# Tests spécifiques
pytest tests/test_scraper_insee.py
pytest tests/test_audit_digital.py
```

## 📝 License

MIT License - Voir [LICENSE](LICENSE) pour plus de détails.

## 🤝 Contribution

Les contributions sont les bienvenues ! Veuillez lire [CONTRIBUTING.md](CONTRIBUTING.md) pour plus de détails.

---

**Développé avec ❤️ pour les équipes commerciales B2B**
