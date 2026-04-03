#!/bin/sh
# Fix ownership of cloned repo directories so webhook user can write
# (bind-mounted paths may be owned by the host user with a different UID)
if [ -d /app/repo/projects ]; then
    chown -R webhook:webhook /app/repo/projects 2>/dev/null || true
fi

exec su-exec webhook python webhook-listener.py
