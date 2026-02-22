# First Steps for Server Setup

This guide details the initial steps required to set up a new server instance.

> **💡 Automation Available**: You can perform all steps from section 2 to 7 automatically by running `uv run tools.py setup-system` from this repository.

## 1. Prerequisites

- A clean installation of Ubuntu 24.04 LTS.
- Non-root user with `sudo` privileges.
- SSH access to the server.

## 2. System Update

First, update the system packages:

```bash
sudo apt update && sudo apt upgrade -y
```

## 3. SSH Hardening

Securing SSH is critical for preventing unauthorized access.

### 3.1. Set up SSH Key-Based Authentication

Before disabling password login, ensure your public key is added to `~/.ssh/authorized_keys`:

```bash
# On your local machine
ssh-copy-id username@your_server_ip
```

### 3.2. Update SSH Configuration

Edit the SSH daemon configuration:

```bash
sudo nano /etc/ssh/sshd_config
```

Ensure the following settings are applied:

```bash
# Disable root login
PermitRootLogin no

# Disable password authentication (FORCE KEY-BASED)
PasswordAuthentication no
PermitEmptyPasswords no

# Disable X11 forwarding if not needed
X11Forwarding no

# Optional: Change default SSH port (e.g., to 2222)
# Port 2222
```

### 3.3. Restart SSH Service

Apply the changes:

```bash
sudo sshd -t && sudo systemctl restart ssh
```

> **Warning**: Keep your current SSH session open until you verify you can log in with your key in a new terminal window!

## 4. Firewall Setup (UFW)

Ubuntu comes with UFW (Uncomplicated Firewall). We should only allow necessary incoming traffic.

### 4.1. Allow SSH

First, ensure SSH is allowed so you don't lock yourself out:

```bash
sudo ufw allow ssh
# Or if you changed the port:
# sudo ufw allow 2222/tcp
```

### 4.2. Allow Service Ports

Allow ports for the services running on this server:

```bash
# Netdata
sudo ufw allow 19999/tcp

# TeamSpeak 3
sudo ufw allow 9987/udp
sudo ufw allow 10011/tcp
sudo ufw allow 30033/tcp
```

### 4.3. Enable the Firewall

```bash
sudo ufw enable
```

### 4.4. Verify Status

```bash
sudo ufw status verbose
```

## 5. Enable Automatic Security Updates

To ensure the server stays secure, enable `unattended-upgrades`:

```bash
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure -plow unattended-upgrades
```

This will automatically install security updates. You can verify the status with:

```bash
systemctl status unattended-upgrades
```

## 6. Install Fail2Ban

Fail2Ban is essential for protecting the server against brute-force attacks:

```bash
sudo apt install fail2ban -y
```

Basic configuration is managed in `/etc/fail2ban/jail.local`.
See the [Fail2Ban Service Guide](../services/fail2ban/fail2ban.md) for more details.

## 7. Install Docker and Docker Compose

Install Docker using the official installation script:

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

Ensure your user is in the `docker` group:

```bash
sudo usermod -aG docker $USER
```

## 8. Install uv (Python Package Manager)

We use `uv` for managing Python tooling:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 9. Clone this Repository

Clone the documentation and configuration repository:

```bash
git clone <this-repo-url> ~/server-config
cd ~/server-config
```

## 10. Configure Environment Variables

Some services use environment variables. Create a `.env` file from the example:

```bash
cp .env.example .env
nano .env
```

## 11. Next Steps

Once your base system is set up, you can:
- [Add a new service](./02-add-new-service.md) to the server.
- Configure backups for your data.
- Set up a reverse proxy for secure access to web interfaces.
