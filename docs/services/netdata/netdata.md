# Netdata Service Documentation

Netdata is a comprehensive monitoring tool for real-time infrastructure insights.

## Docker Setup

Netdata is deployed as a Docker container with access to host metrics and the Docker daemon.

### Configuration

Current configuration highlights:
- **Access**: Via reverse proxy at `https://netdata.${DOMAIN_NAME}`
- **Port**: `19999` (Internal to Docker network)
- **SSL**: Automated via Let's Encrypt.
- **Docker Socket**: Mounted as `:ro` to monitor container health and resource usage.
- **Host Metrics**: `/proc`, `/sys`, and `/etc` are mounted to provide full system visibility.

### Volumes

- `netdataconfig`: Persistence for Netdata configuration.
- `netdatalib`: Persistence for history and state info.
- `netdatacache`: Persistence for the metric database.

## Integrations

### Docker Socket Monitoring
Netdata automatically detects and monitors all containers running on the host via the mounted `/var/run/docker.sock`.

### Fail2Ban Monitoring
Netdata monitors Fail2Ban by reading the logs from `fail2ban.log`.
The host's `/var/log` directory is mounted to `/host/var/log` in the container.

To verify Netdata is picking up Fail2Ban metrics:
1. Open Netdata dashboard at `http://<server-ip>:19999`.
2. Look for the **Fail2Ban** section in the right sidebar.

## Usage

Access the dashboard (replace with your domain):
```bash
https://netdata.yourdomain.com
```

View container logs:
```bash
docker compose logs -f netdata
```
