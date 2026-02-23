# TeamSpeak 3 Service Documentation

TeamSpeak is a proprietary voice-over-IP software for real-time voice communication.

## Docker Setup

The service is managed via Docker Compose.

### Configuration

The current setup uses the following ports:
- `9987/udp`: Voice communication (Main port).
- `10011`: Server Query (Used for automated management).
- `30033`: File Transfer.

Environment variables:
- `TS3SERVER_LICENSE=accept`: Automatically accepts the TeamSpeak license agreement.

### Data Persistence

Configuration and database files are stored in:
- `./services/teamspeak/data/` (Mapped to `/var/ts3server/` in the container).

## Fail2Ban Integration

To protect the TeamSpeak Server Query port (10011) against brute-force attacks, you can set up a custom jail.

### 1. Create Filter
Create `/etc/fail2ban/filter.d/teamspeak.conf`:

```ini
[Definition]
failregex = query from .*:<HOST>:[0-9]+ .* failed .*
ignoreregex =
```

### 2. Add Jail
Add to `/etc/fail2ban/jail.local`:

```ini
[teamspeak]
enabled  = true
port     = 10011
filter   = teamspeak
logpath  = ~/server-config/services/teamspeak/data/logs/ts3server_*.log
maxretry = 5
bantime  = 1h
```

> **Note**: Ensure the log path correctly points to your Docker volumes.

## Basic Commands

### Get Server Admin Token
When the container first starts, it generates a Server Admin token. You can find it in the logs:
```bash
docker compose logs teamspeak3 | grep token
```
