# Complete Server Setup Guide

This guide describes the process of setting up the entire server from a fresh Ubuntu installation to a fully running environment with all services.

## 1. Prerequisites

* **Operating System**: Fresh installation of Ubuntu 24.04 LTS (recommended).
* **User**: A non-root user with `sudo` privileges.
* **Domain**: A registered domain name pointing to your server's public IP.

## 2. Initial Setup

### 2.1. Install Git and uv

First, ensure Git is installed and then install the `uv` Python package manager, which is used to run all management scripts.

```bash
# Update local package index
sudo apt update

# Install Git
sudo apt install git -y

# Install uv (Python Package Manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Reload your shell to make uv available
source $HOME/.cargo/env
```

### 2.2. Clone the Repository

Clone this configuration repository to your server:

```bash
git clone <your-repository-url> ~/server-config
cd ~/server-config
```

## 3. Automated System Hardening

We use the built-in CLI to perform system updates, SSH hardening, firewall configuration, and Docker installation.

```bash
# This command is interactive and will guide you through:
# - System updates & package installation
# - SSH Hardening (Disabling root login & passwords)
# - Firewall configuration (UFW)
# - Automatic security updates
# - Fail2Ban installation & configuration
# - Docker & Docker Compose installation
# - Environment variable initialization (.env)

uv run tools.py setup-system
```

> **Note**: After the SSH hardening step, ensure you have your SSH keys correctly configured on your local machine, as password login will be disabled.

## 4. Environment Configuration

If you didn't complete the full `.env` setup during `setup-system`, or need to modify it:

```bash
uv run tools.py setup-env
```

Ensure the following variables are set correctly:

* `DOMAIN_NAME`: Your base domain (e.g., `example.com`).
* `LETSENCRYPT_EMAIL`: Your email for SSL certificate notifications.
* `TS3SERVER_LICENSE`: Set to `accept`.

## 5. Deploying Services

Once the system is secured and the environment is configured, you can bring up all dockerized services.

```bash
# Deploy all services defined in docker-compose.yml
uv run tools.py docker deploy
```

Wait a few minutes for Caddy to automatically provision SSL certificates for your domains.

## 6. Post-Deployment Configuration

### 6.1. Secure Web Services (Authentication)

By default, the Dashboard and Netdata are accessible but should be secured with Basic Auth.

```bash
# Add an admin user for the Dashboard
uv run tools.py auth add-user admin --vhost dashboard.yourdomain.com

# Add an admin user for Netdata
uv run tools.py auth add-user admin --vhost netdata.yourdomain.com

# Reload Caddy to apply changes
docker exec caddy caddy reload --config /etc/caddy/Caddyfile
```

### 6.2. Enable Automated Cloud Backups

Rclone runs as a Docker container, so no host-side installation is required.

1. **Build the rclone image**:

    ```bash
    docker compose --profile backup build rclone
    ```

2. **Configure your cloud remote** (interactive wizard runs inside the container):

    ```bash
    uv run tools.py backup-config
    ```

    The config is saved to `services/rclone/config/rclone.conf`.
    See `docs/services/rclone/rclone.md` for full configuration details including
    optional client-side encryption.

3. **Setup daily root crontab**:

    ```bash
    uv run tools.py setup-backup-cron
    ```

## 7. Verification

Check the status of all running services:

```bash
uv run tools.py docker status
```

You should now be able to access:

* **Dashboard**: `https://dashboard.yourdomain.com`
* **Netdata**: `https://netdata.yourdomain.com`
* **TeamSpeak**: Connect via your domain on the default TS3 ports.

## 8. Summary of CLI Commands

| Command | Purpose |
| :--- | :--- |
| `uv run tools.py list-services` | See all configured services. |
| `uv run tools.py docker logs [service]` | View logs for troubleshooting. |
| `uv run tools.py housekeep` | Perform periodic maintenance (Update, Backup, Prune). |
| `uv run tools.py backup-create` | Create a manual local backup. |
| `uv run tools.py backup-upload` | Manually push backups to the cloud. |
