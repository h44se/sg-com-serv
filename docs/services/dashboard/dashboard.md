# Dashboard (Homepage) Documentation

This service provides a modern, centralized landing page for all server services and infrastructure monitoring.

## Overview

The dashboard uses **Homepage**, a highly customizable, static dashboard that integrates with various services to provide real-time status and statistics.

## Docker Setup

### Configuration

The dashboard is accessible via the automated reverse proxy.

- **Image**: `ghcr.io/gethomepage/homepage:latest`
- **Internal Port**: `3000`
- **External Port**: `80 / 443` (via Caddy)

#### Environment Variables:
- `VIRTUAL_HOST`: `dashboard.${DOMAIN_NAME}`
- `VIRTUAL_PORT`: `3000`
- `LETSENCRYPT_HOST`: `dashboard.${DOMAIN_NAME}`
- `LETSENCRYPT_EMAIL`: `${LETSENCRYPT_EMAIL}`

### Volumes

- `./dashboard/config`: Contains YAML configuration files.
  - `services.yaml`: List of services and categories.
  - `widgets.yaml`: Dashboard widgets (CPU, Memory, etc.).
  - `settings.yaml`: Visual settings and theme.
  - `bookmarks.yaml`: External bookmarks.
- `/var/run/docker.sock`: Mounted read-only for Docker status integration.

## Integrations

### Netdata
The dashboard includes a Netdata widget that communicates directly with the `netdata` service on the internal `server_net` network.

### Caddy
All SSL certificates and routing are handled automatically by `caddy` service.

## Usage

### Adding Services
To add a new service to the dashboard, edit `dashboard/config/services.yaml`. Example:

```yaml
- Category Name:
    - Service Name:
        icon: service-icon.png
        href: https://service.example.com
        description: Service description
```

### Restarting
Since the configuration is mounted as a volume, most changes are picked up automatically. If not, restart the container:
```bash
uv run tools.py docker deploy homepage
```

## Security

- **Network**: Isolated within the `server_net` Docker network.
- **Access**: SSL/TLS enabled via Let's Encrypt.
- **Docker**: The Docker socket is mounted as **read-only** (`:ro`) to minimize security risks.
