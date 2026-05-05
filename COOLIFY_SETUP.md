--- COOLIFY_DEPLOYMENT.md (原始)


+++ COOLIFY_DEPLOYMENT.md (修改后)
# 🚀 Guide de Déploiement Coolify - B2B Prospector

## ✅ Problème Résolu

L'erreur `PermissionError: [Errno 13] Permission denied: '/app/logs/prospector.log'` a été corrigée.

### Modifications Apportées

1. **Dockerfile** : Création des dossiers `/app/logs` et `/app/data` avec les bons permissions avant le passage en `non-root user`
2. **docker-compose.yml** : Ajout d'une commande personnalisée qui assure les permissions au démarrage
3. **Volumes locaux** : Création des dossiers `logs/` et `data/` à la racine avec permissions ouvertes

---

## 📋 Instructions pour Coolify

### Option 1: Docker Compose (Recommandé)

Dans Coolify, sélectionnez **"Docker Compose"** comme source et collez ce contenu :

```yaml
version: '3.8'

services:
  app:
    image: votre-registry/b2b-prospector:latest
    # OU build from git:
    # build:
    #   context: .
    #   dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - REDIS_HOST=redis
      - DATABASE_URL=sqlite:///./data/prospector.db
      - SECRET_KEY=votre-cle-secrete-generer-aleatoirement
    volumes:
      - prospector-/app/data
      - prospector-logs:/app/logs
    depends_on:
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  redis:
    image: redis:7-alpine
    volumes:
      - redis-/data
    command: redis-server --appendonly yes
    restart: unless-stopped

volumes:
  prospector-
  prospector-logs:
  redis-
```

### Option 2: Git Repository

1. **Push your code to GitHub/GitLab**
   ```bash
   cd /workspace
   git init
   git add .
   git commit -m "Initial commit - B2B Prospector ready for Coolify"
   git branch -M main
   git remote add origin https://github.com/votre-user/b2b-prospector.git
   git push -u origin main
   ```

2. **Dans Coolify** :
   - Click "New Resource" → "Git Repository"
   - Connectez votre repository GitHub/GitLab
   - Sélectionnez la branche `main`
   - Build Pack: **Nixpacks** ou **Dockerfile**
   - Root Directory: `/` (laisser vide)
   - Publish Directory: laisser vide
   - Build Command: laisser vide (utilize Dockerfile)
   - Start Command: laisser vide (utilize CMD in Dockerfile)

3. **Variables d'environnement à configurer dans Coolify** :
   ```
   ENVIRONMENT=production
   DEBUG=false
   SECRET_KEY=<generer-une-cle-aleatoire>
   REDIS_HOST=redis
   DATABASE_URL=sqlite:///./data/prospector.db
   ```

4. **Persistent Volumes** (IMPORTANT) :
   Dans l'onglet "Storage" de Coolify, ajoutez :
   - `/app/data` → Volume: `prospector-data`
   - `/app/logs` → Volume: `prospector-logs`

---

## 🔍 Vérification Post-Déploiement

Après le déploiement, vérifiez que l'application fonctionne :

### 1. Health Check
```bash
curl https://votre-domaine.coolify.app/health
```

Réponse attendue :
```json
{
  "status": "healthy",
  "service": "B2B Prospector",
  "version": "1.0.0",
  "environment": "production"
}
```

### 2. API Documentation
Accédez à : `https://votre-domaine.coolify.app/docs`

### 3. Test Endpoint
```bash
curl -X GET https://votre-domaine.coolify.app/api/v1/prospects/search?q=google
```

---

## 🛠️ Commands Utiles

### Voir les logs dans Coolify
- Onglet "Logs" dans le dashboard Coolify
- OU en SSH : `docker logs -f <container-id>`

### Redémarrer le service
- Bouton "Restart" dans Coolify
- OU en SSH : `docker restart <container-id>`

### Accéder au container en shell
```bash
docker exec -it <container-id> bash
```

### Vérifier les permissions
```bash
docker exec <container-id> ls -la /app/logs
docker exec <container-id> ls -la /app/data
```

---

## 🐛 Troubleshooting

### Erreur: Logs non écrits
```bash
# Vérifier permissions
docker exec <container-id> ls -la /app/

# Devrait afficher :
# drwxr-xr-x appuser appuser  4096 ... logs
# drwxr-xr-x appuser appuser  4096 ... data
```

### Erreur: Database non persistante
Vérifiez que les volumes sont bien configurés dans Coolify :
- `/app/data` doit être mounté sur un volume persistent

### Erreur: Redis non connecté
Vérifiez la variable d'environnement `REDIS_HOST=redis`

---

## 📊 Next Steps After Deployment

1. **Configurer un nom de domaine** dans Coolify
2. **Activer HTTPS/SSL** (automatique avec Let's Encrypt)
3. **Sauvegarder les volumes** régulièrement
4. **Configurer les alerts** de monitoring
5. **Tester tous les endpoints** via `/docs`

---

## 🎯 Checklist de Validation

- [ ] Application démarre sans erreur de permission
- [ ] Logs s'écrivent dans `/app/logs/prospector.log`
- [ ] Database SQLite persistante dans `/app/data/`
- [ ] Health check retourne `healthy`
- [ ] API `/docs` accessible
- [ ] Redis connecté et fonctionnel
- [ ] HTTPS activé
- [ ] Variables d'environnement de production configurées

---

**Support** : Si vous rencontrez d'autres problèmes, consultez les logs dans Coolify et partagez l'erreur complète.
