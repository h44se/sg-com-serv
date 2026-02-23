# CrowdSec Documentation

CrowdSec is a collaborative, open-source security engine that analyzes visitor behavior and provides a global threat intelligence network to block known malicious IPs.

## Overview

Unlike Fail2Ban which relies solely on local logs, CrowdSec shares "signals" with a global community. When an IP is banned on thousands of other servers, it is proactively blocked on yours as well.

## Docker Setup

### Configuration

- **Image**: `crowdsecurity/crowdsec:v1.6`
- **Port**: Internal API only (unexposed by default)

#### Environment Variables:
- `COLLECTIONS`: Pre-installed detection sets (Linux, Nginx, SSHD, Whitelists).

### Volumes

- `./services/crowdsec/config`: Main configuration files.
  - `acquis.yaml`: Defines which logs CrowdSec should monitor.
- `./services/crowdsec/data`: Persistent database for local signals.
- `/var/log`: Mounted as **read-only** to allow the container to analyze system and service logs.

## Integrations

### Fail2Ban vs CrowdSec
This project uses **both**:
- **Fail2Ban**: Handles immediate, local rule-based bans (e.g., rapid SSH failures).
- **CrowdSec**: Provides a wider net of security using behavioral analysis and global community blocklists.

### Nginx Proxy
CrowdSec monitors Nginx logs via the `/var/log` mount to detect Layer 7 attacks (HTTP probing, known exploit patterns).

## Usage

### Viewing Alerts
To see what CrowdSec has detected:
```bash
docker exec crowdsec cscli alerts list
```

### Checking Decisions (Bans)
To see current active bans:
```bash
docker exec crowdsec cscli decisions list
```

## Security Policies

- **Global Intelligence**: Requires an outbound connection to CrowdSec's CAPI (Central API) to download community blocklists.
- **Privacy**: Only metadata about attacks (IP, scenario met, timestamp) is shared; no personal data or actual log content is sent to the central API.
