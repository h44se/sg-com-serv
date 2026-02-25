# CrowdSec

CrowdSec is a collaborative, open-source security engine that analyzes visitor behavior
and provides a global threat intelligence network to proactively block known malicious IPs.

## Architecture

This project uses a **split architecture**:

| Component | Where it runs | Role |
|---|---|---|
| **Security Engine** | Docker container (`crowdsec`) | Analyzes logs, makes ban decisions, exposes Local API (LAPI) |
| **Firewall Bouncer** | Host machine (systemd service) | Reads decisions from LAPI, applies them to host firewall (iptables/nftables) |

The bouncer **must run on the host** because it needs root privileges to manipulate the
kernel's firewall rules. The engine runs in Docker and exposes its LAPI on
`127.0.0.1:8080` so only the local host can reach it.

### Why the Bouncer Matters

Without the bouncer, CrowdSec only *detects* attacks — it does not block anything.
The firewall bouncer is what actually drops packets from banned IPs at the kernel level.

---

## Initial Setup

### Step 1: Add the CrowdSec APT Repository

```bash
curl -s https://packagecloud.io/install/repositories/crowdsec/crowdsec/script.deb.sh \
  | sudo bash
```

### Step 2: Deploy the CrowdSec Container

The engine is already defined in `docker-compose.yml`. Start it with the rest of the
stack:

```bash
uv run tools.py docker deploy
```

CrowdSec will automatically:
- Read the `COLLECTIONS` environment variable from `.env` and install the corresponding
  detection scenarios.
- Begin tailing `/var/log` and the Caddy log volume.

### Step 3: Determine Your Host Firewall Backend

Check which firewall system your kernel uses:

```bash
iptables -V
```

- If the output mentions `nf_tables` → you are on **nftables** (Ubuntu 22.04+).
- Otherwise → you are on **iptables**.

### Step 4: Install the Firewall Bouncer

**nftables (Ubuntu 22.04 / 24.04):**

```bash
sudo apt install crowdsec-firewall-bouncer-nftables
```

**iptables (older systems):**

```bash
sudo apt install crowdsec-firewall-bouncer-iptables
```

### Step 5: Register the Bouncer with the LAPI

The bouncer needs an API key to authenticate with the CrowdSec engine running in Docker.
Generate one via `cscli` inside the container:

```bash
docker exec crowdsec cscli bouncers add firewall-bouncer-host
```

This prints an API key — **copy it immediately**, it will not be shown again.

Example output:
```
Api key for 'firewall-bouncer-host':

   a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4

Please keep this key since you will not be able to retrieve it!
```

### Step 6: Configure the Bouncer

Edit the bouncer's configuration file:

```bash
sudo nano /etc/crowdsec/bouncers/crowdsec-firewall-bouncer.yaml
```

Set these values:

```yaml
# Point to the CrowdSec container LAPI — bound to loopback in docker-compose.yml
api_url: http://127.0.0.1:8080

# Paste the key from Step 5
api_key: <YOUR_API_KEY_HERE>

# Choose the mode that matches your firewall (Step 3)
mode: nftables      # or: iptables
```

> **Note**: The LAPI is already exposed on `127.0.0.1:8080` in `docker-compose.yml`
> (`ports: ["127.0.0.1:8080:8080"]`), so no compose changes are needed.

### Step 7: Start and Enable the Bouncer

```bash
sudo systemctl enable crowdsec-firewall-bouncer
sudo systemctl start crowdsec-firewall-bouncer
```

Check it started cleanly:

```bash
sudo systemctl status crowdsec-firewall-bouncer
```

---

## Verify the Full Stack

### Confirm the bouncer is registered

```bash
docker exec crowdsec cscli bouncers list
```

Expected output includes your `firewall-bouncer-host` with a recent `Last Pull` time.

### Check active decisions

```bash
docker exec crowdsec cscli decisions list
```

### Check active alerts

```bash
docker exec crowdsec cscli alerts list
```

### Verify firewall rules are applied (nftables)

```bash
sudo nft list ruleset | grep crowdsec
```

### Verify firewall rules are applied (iptables)

```bash
sudo iptables -L -n | grep crowdsec
```

---

## Configuration Reference

### Log Sources (`acquis.yaml`)

CrowdSec reads from the containers listed in `./services/crowdsec/config/acquis.yaml`.
The key log sources in this project:

| Source | Why |
|---|---|
| `/var/log/auth.log` | SSH brute-force detection |
| `/var/log/syslog` | General system events |
| `/caddy/` (mounted from `./services/caddy/logs`) | HTTP-layer attack detection (scanning, exploit probing) |
| Docker socket | Container-level log tailing |

### Collections (`.env`)

The `CROWDSEC_COLLECTIONS` variable controls which detection parsers and scenarios are
installed at startup:

```bash
# Recommended baseline:
CROWDSEC_COLLECTIONS=crowdsecurity/linux crowdsecurity/sshd crowdsecurity/caddy crowdsecurity/whitelist-good-actors
```

To add a new collection without restarting:

```bash
docker exec crowdsec cscli collections install crowdsecurity/<name>
docker restart crowdsec
```

---

## How Bans Work End-to-End

```
Log file → CrowdSec engine (Docker) → LAPI decision stored
                                          ↓
                        Firewall Bouncer (host) polls LAPI every 10s
                                          ↓
                        Bouncer inserts DROP rule into nftables/iptables
                                          ↓
                        Kernel drops all packets from the banned IP
```

---

## Maintenance

### Manually ban an IP

```bash
docker exec crowdsec cscli decisions add --ip 1.2.3.4 --duration 24h --reason "manual ban"
```

### Remove a ban

```bash
docker exec crowdsec cscli decisions delete --ip 1.2.3.4
```

### Update all collections

```bash
docker exec crowdsec cscli collections upgrade --all
```

### View bouncer metrics

```bash
docker exec crowdsec cscli metrics
```

---

## Troubleshooting

| Problem | Likely cause | Fix |
|---|---|---|
| Bouncer fails to start | Wrong `api_url` or `api_key` | Re-check `/etc/crowdsec/bouncers/crowdsec-firewall-bouncer.yaml` |
| `connection refused` on LAPI | Container not running | `docker compose ps crowdsec` |
| Bouncer registered but no bans applied | Mode mismatch | Change `mode:` in bouncer config to match `iptables -V` output |
| No alerts appearing | Log sources not configured | Check `acquis.yaml`; verify `/var/log` mount |
| `Last Pull` shows old time | Bouncer service stopped | `sudo systemctl restart crowdsec-firewall-bouncer` |
| Banned IP can still connect | UFW is in front of iptables/nftables | Ensure UFW is not set to `--policy ACCEPT` overriding CrowdSec rules |
