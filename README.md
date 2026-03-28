# Home Server — ThinkPad T430

Self-hosted portfolio site + tutor file sharing, with CI/CD from GitHub.

## Architecture

```
Internet → Cloudflare Tunnel → Caddy (reverse proxy)
                                  ├── portfolio.yourdomain.com  → Astro static site
                                  ├── tutor.yourdomain.com      → FileBrowser
                                  └── webhook.yourdomain.com    → Deploy webhook

GitHub push → Webhook → pull + rebuild → updated container
```

## Prerequisites

- ThinkPad T430 (or any machine) with Debian 12 installed
- A domain name pointed at Cloudflare
- GitHub account

## 1. Debian Setup

Install Debian 12 (Bookworm) from a netinst ISO. After install:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essentials
sudo apt install -y curl git ufw fail2ban

# Firewall — only allow SSH (Cloudflare Tunnel handles web traffic)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw enable

# Enable fail2ban
sudo systemctl enable --now fail2ban
```

## 2. Install Docker

```bash
# Add Docker's official GPG key and repo
sudo apt install -y ca-certificates gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add your user to docker group (log out and back in after)
sudo usermod -aG docker $USER
```

## 3. Clone This Repo on the Server

```bash
git clone https://github.com/YOUR_USER/home-server.git
cd home-server
```

## 4. Set Up Cloudflare Tunnel

1. Buy a domain and add it to Cloudflare (free plan works)
2. Go to **Cloudflare Zero Trust** → **Networks** → **Tunnels**
3. Create a tunnel, copy the token
4. Add public hostname routes:
   - `portfolio.yourdomain.com` → `http://caddy:80`
   - `tutor.yourdomain.com` → `http://caddy:80`
   - `webhook.yourdomain.com` → `http://caddy:80`

## 5. Configure Environment

```bash
cp .env.example .env
# Edit .env with your tunnel token and webhook secret
```

Generate a webhook secret:
```bash
openssl rand -hex 32
```

## 6. Update Domain in Caddyfile

Replace `yourdomain.com` with your actual domain in `Caddyfile`.

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

For each repo you want to auto-deploy:

1. Go to the repo → **Settings** → **Webhooks** → **Add webhook**
2. Payload URL: `https://webhook.yourdomain.com`
3. Content type: `application/json`
4. Secret: same value as `WEBHOOK_SECRET` in your `.env`
5. Events: select **Just the push event**

## 9. LAN Access

Your sites are accessible on LAN at `http://<T430-IP>`. For domain-based LAN access,
add entries to your router's DNS (or `/etc/hosts` on clients):

```
192.168.1.XX  portfolio.yourdomain.com
192.168.1.XX  tutor.yourdomain.com
```

## Services

| Service | URL | Description |
|---------|-----|-------------|
| Portfolio | `portfolio.yourdomain.com` | Static portfolio site built with Astro |
| Tutor Files | `tutor.yourdomain.com` | File browser for tutor materials (default login: `admin` / `admin` — change immediately) |
| Webhook | `webhook.yourdomain.com` | GitHub webhook receiver for CI/CD |

## File Structure

```
home-server/
├── docker-compose.yml     # All service definitions
├── Caddyfile              # Reverse proxy routes
├── .env                   # Secrets (not committed)
├── cloudflared/           # Tunnel config reference
├── portfolio/             # Astro portfolio site
├── tutor/                 # FileBrowser config + data
└── deploy/                # Webhook listener + deploy script
```

## Maintenance

```bash
# View logs
docker compose logs -f <service>

# Rebuild a service
docker compose build --no-cache portfolio
docker compose up -d portfolio

# Update all images
docker compose pull
docker compose up -d

# Backup tutor files
tar czf tutor-backup-$(date +%F).tar.gz tutor/data/
```
