# Security: Basic Authentication Setup

This repository allows you to easily secure your web services (like the Dashboard and Netdata) using Caddy Basic Authentication.

## Prerequisites

- You must have the `apache2-utils` package installed to use the `htpasswd` command (the CLI uses it to generate secure hashes).
  ```bash
  sudo apt install apache2-utils -y
  ```

## How to Enable Basic Auth

To secure a service, you need to create an authentication snippet named exactly after its `VIRTUAL_HOST` in the `caddy/auth/` directory. You can do this using the built-in CLI tools.

### Using the CLI (Recommended)

The repository includes a helper to manage users:

```bash
# Add or update a user for the dashboard
uv run tools.py auth add-user admin --vhost dashboard.example.com

# Add a user with a specific password
uv run tools.py auth add-user user1 --vhost netdata.example.com --password mysecret

# Remove a user
uv run tools.py auth remove-user user1 --vhost netdata.example.com
```

### Manual Configuration

If you prefer to do it manually, create a file at `caddy/auth/your.vhost.com.caddy` with the following content:

```caddy
basic_auth {
    username hashed_password
}
```

You can generate the `hashed_password` using `htpasswd -nbB user password` (the second part of the output) or using the `caddy hash-password` command inside the container.

### Update domain names

The files MUST match the domain name defined in `caddy/Caddyfile`.

- **For the Dashboard**: `dashboard.yourserver.com.caddy`
- **For Netdata**: `netdata.yourserver.com.caddy`

### Reload Caddy

After adding or modifying files in `caddy/auth/`, reload Caddy:

```bash
docker exec caddy caddy reload --config /etc/caddy/Caddyfile
```

## Security Note

- The `caddy/auth/` directory is automatically excluded from Git to prevent leaking credentials.
- The `tools.py` backup system **includes** this directory, so your credentials will be preserved in backups.
- Ensure only the `caddy` container and administrative users have access to these files.
