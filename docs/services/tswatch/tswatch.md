# TSWatch Service
 
TSWatch is a helper service that monitors the TeamSpeak 3 server and provides metrics for the dashboard.

## Description

This service connects to the TeamSpeak 3 Server Query interface to retrieve the current number of connected users and the maximum allowed slots. It exposes this data via a simple REST API that [Homepage](https://gethomepage.dev/) can consume.

## Docker Setup

The service is defined in `docker-compose.yml` and builds from `./services/tswatch`.

### Environment Variables

| Variable | Description | Default |
| --- | --- | --- |
| `TS3_QUERY_USER` | The Server Query username | `serveradmin` |
| `TS3_QUERY_PASSWORD` | The Server Query password | (required) |
| `TS3_QUERY_IP` | The IP/hostname of the TS3 server | `teamspeak3` |
| `TS3_QUERY_PORT` | The Server Query port | `10011` |

## Dashboard Integration

The metrics are displayed on the dashboard using a `customapi` widget.

```yaml
widget:
    type: customapi
    url: http://tswatch:5000/status
    mappings:
    - label: Users
        value: users
    - label: Max
        value: max_users
```

## Security

- The service runs on the internal `server_net` network.
- It is not exposed to the internet via Caddy.
- It uses Server Query credentials which should be kept secure in `.env`.
