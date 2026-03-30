#!/bin/sh
# Pull latest versions of pre-built images and restart
cd "$(dirname "$0")/.."
docker compose pull caddy cloudflared tutor
docker compose up -d caddy cloudflared tutor
echo "Images updated at $(date)"
