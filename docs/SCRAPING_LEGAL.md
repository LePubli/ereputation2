# ⚖️ Avertissement légal — Scraping multi-sources

> Cette page documente le statut juridique des 5 sources de données utilisées
> par B2B Prospector pour l'enrichissement automatique des prospects.

## ✅ Sources publiques (sans risque)

### 1. INSEE / Sirene
- **URL** : https://recherche-entreprises.api.gouv.fr
- **Statut** : API officielle gérée par data.gouv.fr
- **Licence** : Licence Ouverte 2.0 (Etalab)
- **Limites** : 7 requêtes/seconde par IP (sans clé)
- **Légalité** : 🟢 100 % conforme — utilisation libre

### 2. BODACC
- **URL** : https://bodacc-datadila.opendatasoft.com
- **Statut** : Service public Opendatasoft / data.gouv.fr
- **Licence** : Licence Ouverte 2.0
- **Limites** : 10 000 requêtes/jour
- **Légalité** : 🟢 100 % conforme — utilisation libre

## 🟡 Sources scrapées (zone grise)

### 3. Pappers
- **URL** : https://www.pappers.fr
- **Statut** : Données légales publiques (RNCS) republiées
- **CGU** : interdisent le scraping automatisé
- **Mitigation** :
  - Délai mini de 2s entre requêtes
  - User-Agent identifiant le bot et nous
  - Cache 24h en BDD (réduction du volume)
  - Volume cible < 50 requêtes/jour
- **Recommandation** : passer à l'API officielle Pappers (49 €/mois) si volume > 100/jour
- **Risque juridique** : faible mais non nul — cadre des « données factuelles publiques »

### 4. Pages Jaunes (SoLocal)
- **URL** : https://www.pagesjaunes.fr
- **Statut** : annuaire professionnel
- **CGU** : interdisent le scraping
- **Mitigation** :
  - Délai mini de 3s
  - User-Agent identifié
  - Cache 24h
- **Recommandation** : volume < 30 requêtes/jour
- **Risque juridique** : faible — données pro publiques sans données personnelles

### 5. Google Maps
- **URL** : https://www.google.com/maps
- **Statut** : service Google
- **CGU** : interdisent strictement le scraping
- **Mitigation** :
  - Playwright headless (volume très faible)
  - User-Agent navigateur réel
  - Cache 24h
- **Risque** : 🟠 À grand volume, risque de blocage IP + violation CGU
- **Recommandation FORTE** : passer à l'API Google Places (1 $/1000 requêtes) dès volume > 50/jour

## 📊 Stratégie recommandée par volume

| Volume / jour | Recommandation                                                              |
|--------------:|------------------------------------------------------------------------------|
| < 30          | Tout le scraping est OK avec les délais polite implémentés                   |
| 30 - 100      | INSEE+BODACC OK ; envisager API Pappers ; réduire Google Maps                |
| > 100         | INSEE+BODACC OK ; **API Pappers obligatoire**, **API Google Places obligatoire** |

## 🛡️ RGPD

L'application traite **uniquement des données B2B publiques** issues du RNCS et de
sources officielles. Aucune donnée personnelle de prospect particulier n'est collectée.

Les contacts dirigeants sont issus du registre du commerce (légalement publics).

Les fonctionnalités de **droit d'opposition** et **suppression** sont implémentées via :
- Champ `opt_out` (bool) sur les prospects
- Endpoint `DELETE /api/v1/prospects/{id}` (suppression complète)
- Endpoint `PATCH /api/v1/prospects/{id}` avec `opt_out=true` (anonymisation)

## 🔍 Audit & traçabilité

Chaque action de scraping est tracée dans :
- `scrape_cache` : qui a été scrapé, quand, depuis quelle source
- `audit_logs` : qui a déclenché le scraping (ajouts via UI/API)

## 📌 Bonnes pratiques opérationnelles

1. **Respecter les Robots.txt** des sites concernés (vérification ponctuelle)
2. **Pas de parallélisation agressive** — max 5 requêtes simultanées par scraper
3. **User-Agent identifiant** pour permettre aux sites de nous contacter
4. **Mise en cache** systématique des résultats (24h par défaut, configurable)
5. **Préférer toujours les API officielles** quand elles existent et que le volume le justifie
