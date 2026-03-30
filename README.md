# Home Server — ThinkPad T430

Self-hosted portfolio site + tutor file sharing, with CI/CD from GitHub.

## Architecture

```
Internet → Cloudflare Tunnel → Caddy (reverse proxy)
                                  ├── portfolio.opekk.dev   → Astro static site
                                  ├── tutor.opekk.dev       → dufs file server
                                  └── webhook.opekk.dev     → Deploy webhook

GitHub push → Webhook → pull + rebuild → zero-downtime swap
```

## Prerequisites

- ThinkPad T430 (or any machine) with Debian 13 installed
- A domain name pointed at Cloudflare
- GitHub account

## 1. Debian Setup

Install Debian 13 from a netinst ISO. After install:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl git ufw fail2ban

# Firewall — only allow SSH (Cloudflare Tunnel handles web traffic)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw enable

sudo systemctl enable --now fail2ban
```

## 2. Install Docker

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
sudo systemctl enable docker
# Log out and back in for group to take effect
```

## 3. SSH Hardening

On your Mac, generate a key and copy it to the server:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/t430
ssh-copy-id -i ~/.ssh/t430 maciek@<T430-IP>
```

Then on the T430, disable password login and root access:

```bash
sudo sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart sshd
```

Add to `~/.ssh/config` on your Mac for easy access:

```
Host t430
    HostName <T430-IP>
    User maciek
    IdentityFile ~/.ssh/t430
```

## 4. Clone This Repo

```bash
git clone https://github.com/opekk/home-server.git
cd home-server
```

## 5. Set Up Cloudflare Tunnel

1. Buy a domain and add it to Cloudflare (free plan works)
2. Go to **Cloudflare Zero Trust** → **Networks** → **Tunnels**
3. Create a tunnel, copy the token
4. Add public hostname routes — all pointing to `http://caddy:80`:
   - `portfolio.opekk.dev`
   - `tutor.opekk.dev`
   - `webhook.opekk.dev`

## 6. Configure Environment

```bash
cp .env.example .env
# Edit .env with your tunnel token and webhook secret
```

Generate a webhook secret:
```bash
openssl rand -hex 32
```

## 7. Launch

```bash
docker compose up -d
```

Check that everything is running:
```bash
docker compose ps
docker compose logs -f
```

## 8. Set Up GitHub Webhook

For each repo you want to auto-deploy (e.g. `opekk/portfolio`):

1. Go to the repo → **Settings** → **Webhooks** → **Add webhook**
2. Payload URL: `https://webhook.opekk.dev`
3. Content type: `application/json`
4. Secret: same value as `WEBHOOK_SECRET` in your `.env`
5. Events: select **Just the push event**

Add the repo to `deploy/repos.json` to map it to a Docker Compose service.

## 9. LAN Access

Sites are accessible on LAN at `http://<T430-IP>`. For domain-based LAN access,
add entries to your router's DNS (or `/etc/hosts` on clients):

```
192.168.1.XX  portfolio.opekk.dev
192.168.1.XX  tutor.opekk.dev
```

## Services

| Service | URL | Description |
|---------|-----|-------------|
| Portfolio | `portfolio.opekk.dev` | Static portfolio site built with Astro |
| Tutor Files | `tutor.opekk.dev` | File server for tutor materials (browse, download, upload) |
| Webhook | `webhook.opekk.dev` | GitHub webhook receiver for CI/CD |

## File Structure

```
home-server/
├── docker-compose.yml       # All service definitions
├── Caddyfile                # Reverse proxy routes
├── .env                     # Secrets (not committed)
├── cloudflared/             # Tunnel config reference
├── projects/                # Cloned project repos (git-ignored)
│   └── portfolio/           # Cloned by webhook on first deploy
├── tutor/
│   └── data/                # Tutor files served by dufs
└── deploy/
    ├── webhook-listener.py  # GitHub webhook receiver
    ├── deploy.sh            # Clone/pull + rebuild script
    ├── repos.json           # Repo → service mapping
    ├── cleanup.sh           # Docker image pruning
    └── update-images.sh     # Pull latest base images
```

## Maintenance

```bash
# View logs
docker compose logs -f <service>

# Rebuild a service manually
docker compose build --no-cache portfolio
docker compose up -d --force-recreate portfolio

# Prune old Docker images (runs weekly via cron)
./deploy/cleanup.sh

# Update base images (caddy, cloudflared, dufs)
./deploy/update-images.sh

# Backup tutor files
tar czf tutor-backup-$(date +%F).tar.gz tutor/data/
```

### Automated Maintenance

Set up cron jobs on the T430:

```bash
crontab -e
```

```
# Weekly Docker cleanup (Sunday 3am)
0 3 * * 0 /home/maciek/home-server/deploy/cleanup.sh >> /home/maciek/home-server/cleanup.log 2>&1

# Monthly base image update (1st of month, 4am)
0 4 1 * * /home/maciek/home-server/deploy/update-images.sh >> /home/maciek/home-server/update.log 2>&1
```
