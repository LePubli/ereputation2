# 📜 Scraping Légal et Bonnes Pratiques

## ⚖️ Cadre légal (France / UE)

### Ce qui est autorisé
✅ **Données publiques** : Les données légales des entreprises (SIRENE, BODACC) sont publiques et leur collecte est autorisée.

✅ **Usage raisonnable** : La consultation manuelle ou automatisée modérée est permise tant qu'elle ne perturbe pas le service cible.

✅ **Réutilisation des données SIRENE** : Licence Ouverte / Open Data, réutilisation libre (même commerciale).

### Ce qui est interdit
❌ **Contournement des mesures techniques** : Ne pas bypass les CAPTCHA, rate-limiting, ou protections anti-bot.

❌ **Usage commercial massif** : La revente de bases de données scrapées peut violer les CGU.

❌ **Données personnelles** : RGPD s'applique aux dirigeants (noms, dates de naissance). Droit à l'oubli applicable.

❌ **Perturbation du service** : DDoS, scraping intensif (> 10 req/s sur une même source).

---

## 🛡️ Bonnes pratiques implémentées

### 1. Rate Limiting
Chaque scraper respecte un rate limiting strict :

| Source | Limite | Délai minimum |
|--------|--------|---------------|
| INSEE | 10 req/s | 100ms |
| BODACC | 5 req/s | 200ms |
| Pappers | 2 req/s | 500ms |
| PagesJaunes | 1 req/s | 1000ms |
| Google Maps | 1 req/5s | 5000ms |

### 2. User-Agent transparent
```python
user_agent = "Mozilla/5.0 (compatible; B2BProspector/1.0; +https://votre-domaine.com/bot)"
```
- Identification claire du bot
- URL de contact incluse
- Respect des `robots.txt`

### 3. Cache intelligent
Les données scrapées sont mises en cache (table `scrape_cache`) :
- Évite les requêtes redondantes
- Réduit la charge sur les sources
- TTL configurable (par défaut 7 jours pour INSEE)

### 4. Gestion des erreurs
- Retry exponentiel (max 3 tentatives)
- Backoff progressif (1s, 2s, 4s)
- Logging détaillé pour debugging
- Fallback graceful (si INSEE échoue → Pappers)

---

## 📋 Registre de traitement (RGPD)

### Données collectées
| Catégorie | Source | Finalité | Conservation |
|-----------|--------|----------|--------------|
| Identité entreprise | INSEE | Prospection B2B | 3 ans |
| Dirigeants | INSEE | Connaissance client | 3 ans |
| Coordonnées | PagesJaunes | Contact commercial | 3 ans |
| Mentions légales | BODACC | Due diligence | 5 ans |

### Droits des personnes
- **Accès** : Sur demande, exporter toutes les données d'une entreprise
- **Rectification** : Modification manuelle possible dans l'UI
- **Opposition** : Bouton "Ne plus prospecter" sur chaque fiche
- **Oubli** : Suppression cascade (prospects + audits + logs)

---

## 🔍 Check-list avant production

- [ ] Ajouter une page `/legal` avec mentions légales du bot
- [ ] Configurer un email de contact dans le User-Agent
- [ ] Mettre en place un système de plainte/désinscription
- [ ] Logger toutes les requêtes scrapées (audit trail)
- [ ] Tester le rate limiting en charge réelle
- [ ] Vérifier les `robots.txt` de chaque source mensuellement
- [ ] Souscrire une assurance RC Pro (cyber-risques)

---

## 🚨 En cas de problème

### Vous recevez une mise en demeure
1. **Cesser immédiatement** le scraping de la source concernée
2. **Documenter** les requêtes effectuées (logs)
3. **Consulter** un avocat spécialisé en propriété intellectuelle
4. **Coopérer** avec l'hébergeur/source

### Un site vous bloque
- Vérifier vos logs (code 429 = Too Many Requests)
- Réduire le rate limiting de 50%
- Attendre 24h avant de réessayer
- Contacter le webmaster si besoin légitime

---

## 📚 Ressources utiles

- [CNIL - Prospection B2B](https://www.cnil.fr/fr/prospection-commerciale)
- [INSEE - Licence Ouverte](https://www.insee.fr/fr/information/2004444)
- [Data.gouv.fr - Conditions générales](https://www.data.gouv.fr/fr/cgu/)
- [EUR-Lex - RGPD](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX%3A32016R0679)

---

**⚠️ Disclaimer** : Ce document ne constitue pas un conseil juridique. Consultez un avocat pour valider votre conformité.
