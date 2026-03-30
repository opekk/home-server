#!/bin/sh
# Remove Docker images and build cache older than 7 days
docker image prune -af --filter "until=168h"
docker builder prune -af --filter "until=168h"
echo "Cleanup done at $(date)"
