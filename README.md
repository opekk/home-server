# Home Server

Self-hosted infrastructure running on a ThinkPad T430 with Debian 13. All services run in Docker containers, exposed to the internet through a Cloudflare Tunnel and proxied by Caddy.

## Architecture

```
Internet → Cloudflare Tunnel → Caddy (reverse proxy)
                                  ├── portfolio.opekk.dev   → Astro static site
                                  ├── sensors.opekk.dev     → Temperature dashboard
                                  └── webhook.opekk.dev     → Deploy webhook
```

## Services

| Service | Image / Build | Description |
|---------|---------------|-------------|
| **Caddy** | `caddy:2.11-alpine` | Reverse proxy with security headers, routes traffic to all services |
| **Cloudflared** | `cloudflare/cloudflared:2026.3.0` | Cloudflare Tunnel — exposes services to the internet without opening ports |
| **Portfolio** | Built from [opekk/portfolio](https://github.com/opekk/portfolio) | Static portfolio site built with Astro |
| **Sensors** | Built from [opekk/temperature-sensor](https://github.com/opekk/temperature-sensor) | Reads temperature data from an ESP32 over serial and serves a dashboard |
| **Webhook** | Built from `deploy/` | Receives GitHub push events, pulls changes, and rebuilds services with zero downtime |

## CI/CD

A push to `main` on a configured repo triggers automatic deployment:

1. GitHub sends a webhook with HMAC-SHA256 signature
2. `webhook-listener.py` verifies the signature and matches the repo to a service via `repos.json`
3. `deploy.sh` pulls the latest code, builds a new image, and swaps the container while Caddy retries during the brief gap

## File Structure

```
home-server/
├── docker-compose.yml       # All service definitions
├── Caddyfile                # Reverse proxy routes
├── .env                     # Secrets (not committed)
├── projects/                # Cloned project repos (git-ignored)
│   ├── portfolio/           # github.com/opekk/portfolio
│   └── temperature-sensor/  # github.com/opekk/temperature-sensor
└── deploy/
    ├── webhook-listener.py  # GitHub webhook receiver
    ├── deploy.sh            # Clone/pull + rebuild script
    ├── repos.json           # Repo → service mapping
    ├── Dockerfile           # Webhook container image
    ├── cleanup.sh           # Docker image pruning
    └── update-images.sh     # Pull latest base images
```
