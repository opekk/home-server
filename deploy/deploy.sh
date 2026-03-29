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

# Build new image while old container keeps serving traffic
cd "$COMPOSE_DIR"
echo "Building new image (old container still serving)..." | tee -a "$LOG_FILE"
docker compose build --no-cache "$SERVICE" 2>&1 | tee -a "$LOG_FILE"

# Fast swap: Caddy retries during the ~1-2s gap
echo "Swapping containers..." | tee -a "$LOG_FILE"
docker compose up -d --force-recreate "$SERVICE" 2>&1 | tee -a "$LOG_FILE"

# Wait for the new container to pass health check
echo "Waiting for health check..." | tee -a "$LOG_FILE"
TRIES=0
MAX_TRIES=30
while [ "$TRIES" -lt "$MAX_TRIES" ]; do
    HEALTH=$(docker inspect --format='{{.State.Health.Status}}' "$SERVICE" 2>/dev/null || echo "none")
    if [ "$HEALTH" = "healthy" ]; then
        echo "Container is healthy!" | tee -a "$LOG_FILE"
        break
    fi
    if [ "$HEALTH" = "none" ]; then
        echo "No health check configured, skipping wait." | tee -a "$LOG_FILE"
        break
    fi
    TRIES=$((TRIES + 1))
    echo "Health: $HEALTH (attempt $TRIES/$MAX_TRIES)" | tee -a "$LOG_FILE"
    sleep 2
done

if [ "$TRIES" -eq "$MAX_TRIES" ]; then
    echo "WARNING: Container did not become healthy within timeout" | tee -a "$LOG_FILE"
fi

echo "=== Deploy finished: ${REPO_NAME} at $(date) ===" | tee -a "$LOG_FILE"
