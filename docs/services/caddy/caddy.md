# Caddy Reverse Proxy Documentation

This service provides an automated reverse proxy and SSL certificate management (via Let's Encrypt/ZeroSSL) for all dockerized services.

## Overview

Unlike the previous Nginx setup, Caddy handles both proxying and SSL certificate management in a single container. It is configured via a `Caddyfile`.

## Docker Setup

### Configuration

The proxy is configured to listen on ports `80` (HTTP) and `443` (HTTPS).

#### Setup for Proxied Services:

To put a service behind the proxy:
1.  Ensure the service is on the `server_net` network.
2.  Add a site block to `./caddy/Caddyfile`.

Example Site Block:
```caddy
myservice.{$DOMAIN_NAME} {
    reverse_proxy my-container:8080
}
```

### Volumes

- `./caddy/Caddyfile`: The main configuration file.
- `./caddy/data`: Persistent storage for SSL certificates and Caddy state.
- `./caddy/config`: Caddy configuration storage.
- `./caddy/auth`: Directory for basic authentication snippets.
- `./caddy/logs`: Access logs.

## Usage

### Adding a Service

1. Update your `.env` file with `DOMAIN_NAME` and `LETSENCRYPT_EMAIL`.
2. Update the `caddy/Caddyfile` with the new service details.
3. Reload Caddy:
   ```bash
   docker exec caddy caddy reload --config /etc/caddy/Caddyfile
   ```

### Logs
View proxy logs:
```bash
docker compose logs -f caddy
```

## Troubleshooting

- **Certificate Issues**: Check the `caddy` logs. Ensure your domain's A-record points to the server's public IP and that ports 80 and 443 are open in the firewall.
- **502 Bad Gateway**: This usually means Caddy cannot reach the upstream container. Ensure both are on the same Docker network (`server_net`) and the container name/port in `Caddyfile` is correct.
