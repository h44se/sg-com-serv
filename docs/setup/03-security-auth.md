# Security: Basic Authentication Setup

This repository allows you to easily secure your web services (like the Dashboard and Netdata) using Nginx Basic Authentication.

## Prerequisites

- You must have the `apache2-utils` package installed to use the `htpasswd` command (or use an online generator).
  ```bash
  sudo apt install apache2-utils -y
  ```

## How to Enable Basic Auth

To secure a service, you need to create a credential file named exactly after its `VIRTUAL_HOST` in the `nginx/htpasswd/` directory. You can do this manually or using the built-in CLI tools.

### Using the CLI (Recommended)

The repository includes a helper to manage users without needing to remember file paths:

```bash
# Add or update a user for the dashboard
uv run tools.py auth add-user admin --vhost dashboard.example.com

# Add a user with a specific password
uv run tools.py auth add-user user1 --vhost netdata.example.com --password mysecret

# Remove a user
uv run tools.py auth remove-user user1 --vhost netdata.example.com
```

### Manual Configuration

If you prefer to do it manually:

#### 1. Create your credentials

You can generate a credential line using `htpasswd`:
```bash
# Output format: username:hashed_password
htpasswd -nb admin yoursecretpassword
```

### 2. Name the files correctly

The files MUST match the `VIRTUAL_HOST` environment variable defined in `docker-compose.yml`.

- **For the Dashboard**: `dashboard.yourserver.com`
- **For Netdata**: `netdata.yourserver.com`

If you want the SAME password for both, you can copy the same content into both files:

```bash
# Create the directory if it doesn't exist
mkdir -p nginx/htpasswd

# Example for a server with DOMAIN_NAME=example.com
echo "admin:HASHED_PASSWORD" > nginx/htpasswd/dashboard.example.com
echo "admin:HASHED_PASSWORD" > nginx/htpasswd/netdata.example.com
```

### 3. Restart Services

After adding or modifying files in `nginx/htpasswd/`, restart the proxy:

```bash
uv run tools.py docker rebuild
```

## Security Note

- The `nginx/htpasswd/` directory is automatically excluded from Git to prevent leaking credentials.
- The `tools.py` backup system **includes** this directory, so your credentials will be preserved in backups.
- Ensure only the `nginx-proxy` and administrative users have access to these files.
