#!/bin/sh
###############################################################################
# docker-entrypoint.sh — Nginx Frontend (B2B Prospector)
#
# Recrée la structure /tmp/nginx/* au démarrage car :
#  - /tmp est monté en tmpfs par Coolify → vide à chaque restart
#  - nginx a besoin de ces dossiers pour client_body_temp_path, proxy_temp_path...
#
# Affiche aussi un récap du contenu HTML servi pour faciliter le diagnostic
# d'un éventuel "écran noir" (= bundle JS pas servi).
###############################################################################

set -e

# Crée la structure si elle n'existe pas (idempotent)
mkdir -p /tmp/nginx/client_temp \
         /tmp/nginx/proxy_temp \
         /tmp/nginx/fastcgi_temp \
         /tmp/nginx/uwsgi_temp \
         /tmp/nginx/scgi_temp

# Diagnostic au boot : on affiche les fichiers présents et un extrait du HTML
echo "[entrypoint] /usr/share/nginx/html contient :"
ls -la /usr/share/nginx/html/ 2>/dev/null | head -10 || true
echo "[entrypoint] index.html (premières lignes) :"
head -20 /usr/share/nginx/html/index.html 2>/dev/null || echo "(pas de index.html !)"
echo "[entrypoint] index.html contient les scripts ? :"
grep -c '<script type="module" crossorigin src="/assets/' /usr/share/nginx/html/index.html \
    && echo "[entrypoint] OK : scripts module trouvés" \
    || echo "[entrypoint] ATTENTION : aucune balise <script> trouvée — l'app ne démarrera pas !"

# Validation de la conf (échec rapide si erreur)
nginx -t -q

# Lancement de la commande passée à l'image (= CMD)
exec "$@"
