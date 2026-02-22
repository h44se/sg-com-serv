# Nginx Reverse Proxy Documentation

This service provides an automated reverse proxy and SSL certificate management (via Let's Encrypt) for all dockerized services.

## Overview

The setup uses two primary containers:
1.  **nginx-proxy**: Automatically generates Nginx configurations when new containers start with specific environment variables.
2.  **acme-companion**: Handles the creation, renewal, and installation of Let's Encrypt certificates.

## Docker Setup

### Configuration

The proxy is configured to listen on ports `80` (HTTP) and `443` (HTTPS).

#### Environment Variables for Proxied Services:
To put a service behind the proxy, add the following to its `docker-compose.yml` definition:

- `VIRTUAL_HOST`: The domain name (e.g., `netdata.example.com`).
- `VIRTUAL_PORT`: The internal port the service listens on (e.g., `19999`).
- `LETSENCRYPT_HOST`: The domain name for the SSL certificate.
- `LETSENCRYPT_EMAIL`: The email address for Let's Encrypt notifications.

### Volumes

- `./nginx/certs`: Stores SSL certificates.
- `./nginx/vhost`: Stores Nginx virtual host configurations.
- `./nginx/html`: Stores static HTML files and Let's Encrypt challenge files.
- `acme`: Persistent storage for `acme.sh` internal state.

## Usage

### Adding a Service
To add a new service behind the proxy:
1. Update your `.env` file with `DOMAIN_NAME` and `LETSENCRYPT_EMAIL`.
2. Add the required environment variables to the service in `docker-compose.yml`.
3. Ensure the service is on the `server_net` network.

### Logs
View proxy logs:
```bash
docker compose logs -f nginx-proxy
```

View SSL companion logs:
```bash
docker compose logs -f acme-companion
```

## Troubleshooting

- **Certificate Issues**: Check the `acme-companion` logs. Ensure your domain's A-record points to the server's public IP and that ports 80 and 443 are open in the firewall.
- **503 Service Unavailable**: This usually means the proxy cannot reach the upstream container. Ensure both are on the same Docker network (`server_net`).
