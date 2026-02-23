# How to Add a New Service

This guide explains the process of adding a new service to this repository, ensuring it is properly configured, secured, and documented.

## 1. Update Docker Compose

Add the service definition to `docker-compose.yml`.

### Best Practices:
- Use specific image tags instead of `latest` for production stability.
- Use `restart: unless-stopped`.
- Connect the service to the `server_net` network.
- Use named volumes for persistent data.
- If the service needs host paths, use relative paths from the repository root.

Example:
```yaml
  my-new-service:
    image: my-image:1.0
    container_name: my-new-service
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - ./my-service/data:/data
    networks:
      - server_net

## 2. Update Caddy Proxy

To make the service accessible via HTTPS, add a site block to `services/caddy/Caddyfile`.

Example:
```caddy
my-service.${DOMAIN_NAME} {
    reverse_proxy my-new-service:8080
}
```

Then reload Caddy:
```bash
docker exec caddy caddy reload --config /etc/caddy/Caddyfile
```

## 3. Update Firewall (UFW)

If the service needs to be accessible from the internet, you must open the required ports.

### Option A: Using `tools.py` (Recommended)
Update the default ports in `tools.py` or run the setup command with the `--port` flag:

```bash
uv run tools.py setup-system --port 8080/tcp
```

### Option B: Manually
```bash
sudo ufw allow 8080/tcp
```

## 3. Configure Fail2Ban (If applicable)

If the service has a login interface or an API that can be brute-forced:

1.  **Create a Filter**: Add a new file in `/etc/fail2ban/filter.d/my-service.conf` with appropriate regex.
2.  **Add a Jail**: Add the jail configuration to `/etc/fail2ban/jail.local`.
3.  **Update `tools.py`**: Add the automation logic to `SystemManager` in `tools.py` to ensure the jail is set up on new server deployments.

## 4. Documentation

Every service must have its own documentation file in `docs/services/<service-name>/<service-name>.md`.

### Document Structure:
- **Description**: What is the service for?
- **Docker Setup**: Port mappings, environment variables, and volumes.
- **Integrations**: How it works with Fail2Ban, Netdata, etc.
- **Usage**: Basic commands and access information.

## 5. Dashboard Integration (If applicable)

To make the service visible on the central landing page:

1.  **Update `services/dashboard/config/services.yaml`**: Add the service under the appropriate category.
2.  **Add an Icon**: Ensure the icon is referenced correctly or added to `services/dashboard/config/icons/`.

Example:
```yaml
- My Category:
    - My Service:
        icon: my-service.png
        href: https://service.${DOMAIN_NAME}
        description: A brief description
```

Finally, add the service to the table in the main `README.md`.

## 6. Security Checklist

Before considering the task "done", verify:
- [ ] Is the service running as a non-root user inside the container?
- [ ] Are sensitive ports restricted to specific IPs if possible?
- [ ] Is there a need for SSL/TLS? (Configure in `services/caddy/Caddyfile`).
- [ ] Is the data being backed up?
