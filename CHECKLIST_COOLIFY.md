# 🎯 Checklist de Déploiement Coolify

Utilisez cette checklist pour garantir un déploiement réussi sur votre VPS.

---

## ✅ PRÉ-INSTALLATION

### Infrastructure
- [ ] VPS avec minimum 4GB RAM, 2 CPU, 40GB SSD
- [ ] Docker installé et fonctionnel (`docker --version`)
- [ ] Coolify installé et accessible (http://votre-ip:8000)
- [ ] Nom de domaine configuré (DNS pointant vers le VPS)
- [ ] Firewall ouvert : ports 22 (SSH), 80/443 (HTTP/HTTPS)

### Code & Repository
- [ ] Code pushé sur GitHub/GitLab
- [ ] Fichier `docker-compose.coolify.yml` présent à la racine
- [ ] Fichier `.env.example` présent pour référence
- [ ] README.md à jour avec les instructions

### Clés API (Optionnel mais recommandé)
- [ ] Compte INSEE API créé (gratuit)
- [ ] Compte Pappers API créé (freemium)
- [ ] Ollama installé localement OU clé OpenAI générée

---

## 🚀 INSTALLATION DANS COOLIFY

### Étape 1 : Création du Projet
- [ ] Connecté à l'interface Coolify
- [ ] Nouveau projet créé : "B2B Prospector"
- [ ] Resource Docker Compose ajoutée
- [ ] Repository Git connecté
- [ ] Branche `main` sélectionnée
- [ ] Fichier `docker-compose.coolify.yml` spécifié

### Étape 2 : Variables d'Environnement
- [ ] `POSTGRES_USER` défini (ex: `prospector`)
- [ ] `POSTGRES_PASSWORD` généré (32+ caractères)
- [ ] `POSTGRES_DB` défini (ex: `prospector_db`)
- [ ] `REDIS_PASSWORD` généré (32+ caractères)
- [ ] `SECRET_KEY` généré (64+ caractères)
- [ ] `ENVIRONMENT` = `production`
- [ ] `LOG_LEVEL` = `INFO`
- [ ] `ENABLE_PLUGINS` = `all` (ou liste personnalisée)

### Étape 3 : Clés API Optionnelles
- [ ] `INSEE_API_KEY` renseignée (si disponible)
- [ ] `PAPPERS_API_KEY` renseignée (si disponible)
- [ ] `OPENAI_API_KEY` ou `OLLAMA_BASE_URL` configuré

### Étape 4 : Domaine & SSL
- [ ] Domaine ajouté (ex: `prospector.votre-domaine.com`)
- [ ] Certificat SSL généré automatiquement (Let's Encrypt)
- [ ] HTTPS forcé activé

### Étape 5 : Déploiement Initial
- [ ] Bouton "Deploy" cliqué
- [ ] Build en cours surveillé (logs visibles)
- [ ] Tous les conteneurs démarrés sans erreur
- [ ] Health checks passants (vert dans Coolify)

---

## 🔧 POST-INSTALLATION

### Tests de Fonctionnalité
- [ ] Swagger UI accessible : `https://prospector.votre-domaine.com/docs`
- [ ] Health check OK : `GET /api/v1/health` retourne 200
- [ ] Base de données connectée (pas d'erreur de connection)
- [ ] Redis connecté (event bus fonctionnel)
- [ ] Plugins chargés (vérifier logs API)

### Tests des Endpoints Principaux
- [ ] `POST /api/v1/prospects` - Création prospect par SIRET fonctionne
- [ ] `GET /api/v1/prospects/{siren}` - Récupération infos légales OK
- [ ] `POST /api/v1/audit/digital/{id}` - Lancement audit digital OK
- [ ] `GET /api/v1/pipeline` - Vue Kanban affichée
- [ ] `POST /api/v1/angles/generate` - Génération angles fonctionne

### Sécurité
- [ ] Mots de passe forts générés pour tous les secrets
- [ ] `.env` non commité dans Git (dans .gitignore)
- [ ] Firewall VPS configuré (seuls ports nécessaires ouverts)
- [ ] HTTPS actif sur toutes les routes
- [ ] Rate limiting activé (60 req/min par défaut)

### Monitoring
- [ ] Logs accessibles via Coolify UI
- [ ] Alertes configurées (email/webhook en cas d'erreur)
- [ ] Métriques de base surveillées (CPU, RAM, Disk)
- [ ] Backup database planifié (cron job ou Coolify feature)

---

## 📊 VALIDATION MÉTIER

### Scénario Test Complet
1. [ ] Créer un prospect avec un SIRET réel (ex: 775684019 pour Google France)
2. [ ] Vérifier que les données légales sont récupérées
3. [ ] Lancer un audit digital sur le prospect
4. [ ] Attendre la fin de l'audit (score 0-100 généré)
5. [ ] Générer des angles commerciaux
6. [ ] Vérifier que les angles sont basés sur des faits vérifiés
7. [ ] Changer le stage du prospect dans le Kanban
8. [ ] Créer une séquence d'outreach email
9. [ ] Vérifier que le template est personnalisé

### Performance
- [ ] Temps de réponse API < 500ms (hors appels externes)
- [ ] Audit digital complet < 30 secondes
- [ ] Génération angles < 5 secondes
- [ ] Pas de memory leaks après 100 requêtes

---

## 🛠️ MAINTENANCE RÉCURRENTE

### Quotidien
- [ ] Vérifier les logs d'erreurs (Coolify UI)
- [ ] Surveiller l'espace disque (`df -h`)
- [ ] Vérifier les backups effectués

### Hebdomadaire
- [ ] Mettre à jour les dépendances sécurité
- [ ] Review des métriques de performance
- [ ] Nettoyer les vieux logs (> 7 jours)

### Mensuel
- [ ] Backup complet testé (restore sur environnement test)
- [ ] Audit de sécurité (fail2ban, SSH keys, etc.)
- [ ] Review des coûts infrastructure

---

## 🆘 TROUBLESHOOTING RAPIDE

### Problèmes Courants

| Symptôme | Solution |
|----------|----------|
| Conteneur API redémarre en boucle | Vérifier logs : `DATABASE_URL` correct ? |
| Erreur connection PostgreSQL | Attendre healthcheck DB (30s) avant API |
| Erreur connection Redis | Vérifier `REDIS_PASSWORD` dans .env |
| SSL ne se génère pas | Vérifier DNS + port 80 ouvert |
| Plugins non chargés | Vérifier `ENABLE_PLUGINS` variable |
| Timeout appels API externes | Augmenter timeout ou vérifier réseau |

### Commandes Utiles

```bash
# Voir tous les conteneurs
docker ps -a

# Logs en temps réel
docker logs -f b2b-prospector-api

# Redémarrer un service
docker restart b2b-prospector-api

# Accéder au shell API
docker exec -it b2b-prospector-api bash

# Tester la DB
docker exec -it b2b-prospector-db psql -U prospector -d prospector_db

# Vérifier l'espace disque
df -h

# Nettoyer les vieux images
docker image prune -af
```

---

## 🎉 DÉPLOIEMENT RÉUSSI !

Une fois toutes les cases cochées :

✅ Votre application est **production-ready**  
✅ Les données sont **persistantes et sauvegardées**  
✅ Le HTTPS est **activé et sécurisé**  
✅ Les plugins sont **opérationnels**  

**Prochaines étapes :**
1. Importer vos premiers prospects
2. Configurer vos séquences d'outreach
3. Inviter votre équipe commerciale
4. Suivre les métriques de conversion

📖 Documentation complète : `https://prospector.votre-domaine.com/docs`

---

**Support :** Consultez `COOLIFY_SETUP.md` pour les détails techniques.
