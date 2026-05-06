#!/bin/sh
###############################################################################
# docker-entrypoint.sh — Nginx Frontend (B2B Prospector)
#
# Recrée la structure /tmp/nginx/* au démarrage car :
#  - /tmp est monté en tmpfs par Coolify → vide à chaque restart
#  - nginx a besoin de ces dossiers pour client_body_temp_path, proxy_temp_path...
#  - on tourne en USER nginx (non-root) sans privilège pour mkdir runtime
#
# Ce wrapper s'exécute en USER nginx (non-root) — donc /tmp doit être
# writable par nginx (uid 101 sur Alpine), ce qui est le cas avec tmpfs:/tmp
# en mode RW (mode par défaut tmpfs Docker).
###############################################################################

set -e

# Crée la structure si elle n'existe pas (idempotent)
mkdir -p /tmp/nginx/client_temp \
         /tmp/nginx/proxy_temp \
         /tmp/nginx/fastcgi_temp \
         /tmp/nginx/uwsgi_temp \
         /tmp/nginx/scgi_temp

# Validation de la conf (échec rapide si erreur)
nginx -t -q

# Lancement de la commande passée à l'image (= CMD)
exec "$@"
