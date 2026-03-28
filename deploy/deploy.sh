#!/bin/sh
set -e

REPO_NAME="${1:-portfolio}"
REPO_DIR="/app/repo"
LOG_FILE="/app/deploy-${REPO_NAME}.log"

echo "=== Deploy started: ${REPO_NAME} at $(date) ===" | tee "$LOG_FILE"

cd "$REPO_DIR"

# Pull latest changes
git pull origin main 2>&1 | tee -a "$LOG_FILE"

# Map repo names to docker compose service names
# Add more mappings as you add repos
case "$REPO_NAME" in
  portfolio|portfolio-site)
    SERVICE="portfolio"
    ;;
  *)
    SERVICE="$REPO_NAME"
    ;;
esac

# Rebuild and restart the service
docker compose build --no-cache "$SERVICE" 2>&1 | tee -a "$LOG_FILE"
docker compose up -d "$SERVICE" 2>&1 | tee -a "$LOG_FILE"

echo "=== Deploy finished: ${REPO_NAME} at $(date) ===" | tee -a "$LOG_FILE"
