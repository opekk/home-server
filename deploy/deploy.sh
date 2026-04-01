#!/bin/sh
set -e

REPO_NAME="$1"
CLONE_URL="$2"
REPO_PATH="$3"
SERVICE="$4"
BRANCH="${5:-main}"

COMPOSE_DIR="/app/repo"
LOG_FILE="/tmp/deploy-${REPO_NAME}.log"

# Bypass git "dubious ownership" for bind-mounted repos
export GIT_CONFIG_COUNT=1
export GIT_CONFIG_KEY_0=safe.directory
export GIT_CONFIG_VALUE_0='*'

# Run a command, log output, and preserve its exit code.
# Avoids cmd|tee pattern where set -e cannot catch failures.
run_cmd() {
    local tmpout="/tmp/cmd_output.$$"
    if "$@" > "$tmpout" 2>&1; then
        cat "$tmpout" | tee -a "$LOG_FILE"
        rm -f "$tmpout"
    else
        local rc=$?
        cat "$tmpout" | tee -a "$LOG_FILE"
        rm -f "$tmpout"
        echo "ERROR: command failed (exit $rc): $*" | tee -a "$LOG_FILE"
        exit $rc
    fi
}

log() {
    echo "$1" | tee -a "$LOG_FILE"
}

log "=== Deploy started: ${REPO_NAME} at $(date) ==="

# Clone if the repo doesn't exist, otherwise pull
if [ ! -d "$REPO_PATH/.git" ]; then
    log "Cloning ${CLONE_URL} into ${REPO_PATH}..."
    run_cmd git clone --branch "$BRANCH" "$CLONE_URL" "$REPO_PATH"
else
    log "Pulling latest changes..."
    cd "$REPO_PATH"
    run_cmd git fetch origin "$BRANCH"
    run_cmd git reset --hard "origin/$BRANCH"
fi

# Build new image while old container keeps serving traffic
cd "$COMPOSE_DIR"
log "Building new image (old container still serving)..."
run_cmd docker compose build --no-cache "$SERVICE"

# Fast swap: Caddy retries during the ~1-2s gap
log "Swapping containers..."
run_cmd docker compose up -d --force-recreate "$SERVICE"

# Wait for the new container to pass health check
log "Waiting for health check..."
TRIES=0
MAX_TRIES=30
while [ "$TRIES" -lt "$MAX_TRIES" ]; do
    HEALTH=$(docker inspect --format='{{.State.Health.Status}}' "$SERVICE" 2>/dev/null || echo "none")
    if [ "$HEALTH" = "healthy" ]; then
        log "Container is healthy!"
        break
    fi
    if [ "$HEALTH" = "none" ]; then
        log "No health check configured, skipping wait."
        break
    fi
    TRIES=$((TRIES + 1))
    log "Health: $HEALTH (attempt $TRIES/$MAX_TRIES)"
    sleep 2
done

if [ "$TRIES" -eq "$MAX_TRIES" ]; then
    log "WARNING: Container did not become healthy within timeout"
fi

log "=== Deploy finished: ${REPO_NAME} at $(date) ==="
