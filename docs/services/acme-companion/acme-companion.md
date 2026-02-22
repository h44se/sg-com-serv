# ACME Companion Documentation

The **ACME Companion** is a companion container for the Nginx Reverse Proxy. It automates the creation, renewal, and installation of SSL certificates from Let's Encrypt using the `acme.sh` script.

## Overview

Working alongside the `nginx-proxy`, this service monitors other Docker containers. When a container is started with the `LETSENCRYPT_HOST` environment variable, the ACME Companion automatically requests a certificate and configures the proxy to use it.

## Docker Configuration

### Environment Variables

- `DEFAULT_EMAIL`: The default email address used for Let's Encrypt registration and expiration notifications. (Configured via `${LETSENCRYPT_EMAIL}`).

### Volumes

- `/var/run/docker.sock`: Required to monitor Docker events (container start/stop).
- `./nginx/certs`: Shared with the proxy to store and retrieve SSL certificates.
- `./nginx/vhost`: Shared with the proxy for virtual host configurations.
- `./nginx/html`: Used for the ACME HTTP-01 challenge (verifying domain ownership).
- `acme`: Persistent volume for the `acme.sh` configuration and status.

## Usage

The ACME Companion does not require manual intervention for most tasks. 

### Triggering a Manual Certificate Update

To force a check/renewal of certificates, you can restart the container:

```bash
uv run tools.py docker deploy acme-companion
```

### Viewing Logs

To monitor certificate generation and verification:

```bash
uv run tools.py docker logs acme-companion
```

## Healthchecks

The container includes a healthcheck that ensures the `acme.sh` process is manageable:

- **Test**: `pgrep -f acme.sh`
- **Interval**: 1 minute
- **Retries**: 3

## Important Notes

1. **Domain Reachability**: For Let's Encrypt to issue a certificate using the HTTP-01 challenge, your server **must** be reachable from the internet on port 80.
2. **Rate Limits**: Be aware of Let's Encrypt's rate limits. Rebuilding containers too frequently might trigger blocks if certificates are requested too often.
3. **Shared Network**: This service must share the same network as the `nginx-proxy` (`server_net`).
