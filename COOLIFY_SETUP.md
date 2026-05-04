# 🚀 Guide d'Installation sur Coolify

Ce guide vous accompagne pas à pas pour déployer **B2B Prospector** sur votre VPS via **Coolify**.

---

## 📋 Prérequis

1. **Un VPS** (Hetzner, DigitalOcean, OVH, etc.) avec Docker installé
2. **Coolify** déjà installé sur le VPS ([Documentation Coolify](https://coolify.io/docs))
3. **Un nom de domaine** pointant vers votre VPS (optionnel mais recommandé)
4. **Clés API** (optionnelles selon les fonctionnalités souhaitées) :
   - API INSEE (gratuit) ou Pappers/BODACC
   - OpenAI (pour reformulation LLM)
   - Autres services selon plugins activés

---

## 🎯 Méthode 1 : Import Direct du Docker Compose (Recommandé)

### Étape 1 : Préparer le Repository

1. **Pusher votre code sur GitHub/GitLab** :
   ```bash
   cd /workspace
   git init
   git add .
   git commit -m "Initial commit - B2B Prospector ready for Coolify"
   git remote add origin https://github.com/VOTRE_USER/b2b-prospector.git
   git push -u origin main
   ```

2. **Vérifier que le fichier `docker-compose.coolify.yml` est présent** à la racine.

### Étape 2 : Configurer dans Coolify

1. **Connectez-vous à Coolify** (http://votre-vps-ip:8000)

2. **Créer un nouveau projet** :
   - Cliquez sur **"New Project"**
   - Nom : `B2B Prospector`
   - Description : `Copilote commercial B2B intelligent`

3. **Ajouter une nouvelle ressource** :
   - Cliquez sur **"New Resource"** → **"Docker Compose"**
   - Source : **Git Repository**
   - URL : `https://github.com/VOTRE_USER/b2b-prospector.git`
   - Branche : `main`
   - Fichier Docker Compose : `docker-compose.coolify.yml`

4. **Configurer les Variables d'Environnement** :
   
   Dans l'interface Coolify, ajoutez ces variables sensibles (Secrets) :

   | Variable | Valeur Recommandée | Description |
   |----------|---------------------|-------------|
   | `POSTGRES_USER` | `prospector` | Utilisateur DB |
   | `POSTGRES_PASSWORD` | `Générez_un_mdp_complexe_32_chars` | Mot de passe DB |
   | `POSTGRES_DB` | `prospector_db` | Nom de la DB |
   | `REDIS_PASSWORD` | `Générez_un_mdp_complexe_32_chars` | Mot de passe Redis |
   | `SECRET_KEY` | `Générez_une_clé_secrète_64_chars` | Clé de chiffrement JWT |
   | `INSEE_API_KEY` | *(Optionnel)* | Clé API INSEE |
   | `PAPPERS_API_KEY` | *(Optionnel)* | Clé API Pappers |
   | `OPENAI_API_KEY` | *(Optionnel)* | Clé OpenAI pour LLM |

   > 💡 **Astuce** : Générez des mots de passe forts avec :
   > ```bash
   > openssl rand -base64 32
   > ```

5. **Configurer le Domaine** (Optionnel) :
   - Allez dans l'onglet **"Domains"** de la ressource
   - Ajoutez : `prospector.votre-domaine.com`
   - Coolify gérera automatiquement le certificat SSL (Let's Encrypt)

6. **Déployer** :
   - Cliquez sur **"Deploy"**
   - Attendez que les conteneurs démarrent (2-5 minutes)
   - Vérifiez les logs pour confirmer le démarrage

---

## 🎯 Méthode 2 : Déploiement Manuel via SSH (Alternative)

Si vous préférez ne pas utiliser Git :

### Étape 1 : Transférer les fichiers

```bash
# Sur votre machine locale
scp -r /workspace/* user@votre-vps:/home/user/b2b-prospector/
```

### Étape 2 : Créer le fichier .env

```bash
cd /home/user/b2b-prospector

cat > .env << EOF
POSTGRES_USER=prospector
POSTGRES_PASSWORD=$(openssl rand -base64 32)
POSTGRES_DB=prospector_db
REDIS_PASSWORD=$(openssl rand -base64 32)
SECRET_KEY=$(openssl rand -base64 48)
ENVIRONMENT=production
LOG_LEVEL=INFO
INSEE_API_KEY=
PAPPERS_API_KEY=
OPENAI_API_KEY=
EOF

chmod 600 .env
```

### Étape 3 : Lancer avec Docker Compose

```bash
docker compose -f docker-compose.coolify.yml --env-file .env up -d --build
```

### Étape 4 : Vérifier le statut

```bash
docker compose -f docker-compose.coolify.yml ps
docker compose -f docker-compose.coolify.yml logs -f api
```

---

## 🔧 Configuration Post-Déploiement

### 1. Initialiser la Base de Données

Une fois les conteneurs démarrés, exécutez les migrations :

```bash
# Se connecter au conteneur API
docker exec -it b2b-prospector-api bash

# Lancer les migrations (si Alembic configuré)
alembic upgrade head

# Ou initialiser la DB manuellement
python -c "from app.core.database import init_db; init_db()"

exit
```

### 2. Tester l'API

Accédez à l'URL fournie par Coolify (ou http://votre-ip:8000) :

- **Swagger UI** : `https://prospector.votre-domaine.com/docs`
- **Health Check** : `https://prospector.votre-domaine.com/api/v1/health`

Test rapide avec curl :

```bash
curl -X GET https://prospector.votre-domaine.com/api/v1/health
```

### 3. Activer les Plugins

Par défaut, tous les plugins sont activés. Pour personnaliser :

Dans Coolify → Variables d'environnement :
```
ENABLE_PLUGINS=scraper-insee,audit-digital,pain-point-engine,pipeline-kanban
```

Ou pour TOUS les plugins :
```
ENABLE_PLUGINS=all
```

---

## 📊 Monitoring & Maintenance

### Logs en Temps Réel

```bash
# Via Coolify UI (recommandé)
# Ou en CLI :
docker compose -f docker-compose.coolify.yml logs -f api worker
```

### Backup Automatique

Ajoutez ce cron job pour sauvegarder PostgreSQL quotidiennement :

```bash
crontab -e

# Ajouter cette ligne (backup à 3h du matin)
0 3 * * * docker exec b2b-prospector-db pg_dump -U prospector prospector_db > /backups/prospector_$(date +\%Y\%m\%d).sql
```

### Mise à Jour

```bash
# Tirer les nouvelles modifications
git pull origin main

# Rebuild et redémarrer
docker compose -f docker-compose.coolify.yml up -d --build
```

---

## 🛠️ Troubleshooting

### Problème : Conteneur API ne démarre pas

**Solution** :
```bash
docker compose -f docker-compose.coolify.yml logs api
# Cherchez l'erreur, souvent :
# - DATABASE_URL incorrect
# - SECRET_KEY manquante
# - Port déjà utilisé
```

### Problème : Connection à PostgreSQL échoue

**Solution** :
```bash
# Vérifier que DB est healthy
docker compose -f docker-compose.coolify.yml ps db

# Tester la connection
docker exec -it b2b-prospector-db psql -U prospector -d prospector_db -c "SELECT 1;"
```

### Problème : Migration échoue

**Solution** :
```bash
# Reset DB (ATTENTION: efface toutes les données!)
docker volume rm b2b-prospector_pgdata
docker compose -f docker-compose.coolify.yml up -d db
# Puis relancer les migrations
```

---

## 🎉 Prochaines Étapes

Une fois déployé :

1. **Créer votre premier prospect** via Swagger UI
2. **Lancer un audit digital** automatique
3. **Générer des angles commerciaux**
4. **Configurer vos séquences d'outreach**

📖 Consultez la documentation complète : `http://votre-url/docs`

---

## 📞 Support

- Documentation technique : `/workspace/README.md`
- Analyse stratégique : `/workspace/ANALYSIS_COMPLETE.md`
- Issues GitHub : [Votre Repo]

**Bon déploiement ! 🚀**
