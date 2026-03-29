#!/bin/sh
set -e

REPO_NAME="$1"
CLONE_URL="$2"
REPO_PATH="$3"
SERVICE="$4"
BRANCH="${5:-main}"

COMPOSE_DIR="/app/repo"
LOG_FILE="/app/deploy-${REPO_NAME}.log"

echo "=== Deploy started: ${REPO_NAME} at $(date) ===" | tee "$LOG_FILE"

# Clone if the repo doesn't exist, otherwise pull
if [ ! -d "$REPO_PATH/.git" ]; then
    echo "Cloning ${CLONE_URL} into ${REPO_PATH}..." | tee -a "$LOG_FILE"
    git clone --branch "$BRANCH" "$CLONE_URL" "$REPO_PATH" 2>&1 | tee -a "$LOG_FILE"
else
    echo "Pulling latest changes..." | tee -a "$LOG_FILE"
    cd "$REPO_PATH"
    git fetch origin "$BRANCH" 2>&1 | tee -a "$LOG_FILE"
    git reset --hard "origin/$BRANCH" 2>&1 | tee -a "$LOG_FILE"
fi

# Rebuild and restart the service
cd "$COMPOSE_DIR"
docker compose build --no-cache "$SERVICE" 2>&1 | tee -a "$LOG_FILE"
docker compose up -d "$SERVICE" 2>&1 | tee -a "$LOG_FILE"

echo "=== Deploy finished: ${REPO_NAME} at $(date) ===" | tee -a "$LOG_FILE"
