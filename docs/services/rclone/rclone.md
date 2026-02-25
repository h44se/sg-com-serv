# Rclone Cloud Backup Service

Rclone is a command-line program to manage files on cloud storage. It is used here to
synchronize local backups (created by `tools.py backup-create`) to external providers
such as Google Drive, AWS S3, Backblaze B2, or Dropbox.

## Overview

Rclone runs as a **Docker container** within this project rather than being installed on
the host system. This has two key advantages:

1. **Root access** — the container runs as `uid 0:0`, so it can read every service
   volume regardless of which user each service uses internally (e.g. TeamSpeak,
   Netdata, Caddy all write data as different UIDs).
2. **No host dependency** — you do not need to install or update rclone on the host;
   the version is pinned in `services/rclone/Dockerfile` and tracked in Git.

The service is declared with `profiles: [backup]` in `docker-compose.yml`. This means
it **never starts automatically** with `docker compose up`; it is only spun up on-demand
via `docker compose run` (or through the `tools.py` CLI wrappers).

### Volume Mapping

| Host path | Container path | Access |
|---|---|---|
| `./services/rclone/config/` | `/config/rclone/` | read-write — rclone config lives here |
| `./backups/` | `/backups/` | read-write — backup archives to upload/download |
| `./services/` | `/services/` | read-only — service data for future direct backup use |

---

## Initial Setup

### 1. Build the container image

```bash
docker compose --profile backup build rclone
```

### 2. Configure your cloud remote

The `rclone config` wizard runs interactively inside the container. The resulting config
file is saved to `./services/rclone/config/rclone.conf` on the host (via the volume mount).

```bash
docker compose --profile backup run --rm rclone config
```

Or, equivalently, via the project CLI:

```bash
uv run tools.py backup-config
```

Follow the prompts to add a new remote. Common choices:

| Provider | Type to select |
|---|---|
| Google Drive | `drive` |
| AWS S3 / Backblaze B2 | `s3` |
| Dropbox | `dropbox` |
| SFTP | `sftp` |

Give your remote a short name such as `gdrive` or `b2` — you will reference this name
when running backups.

### 3. Optional but strongly recommended: Encryption (Crypt remote)

Wrap your cloud remote with an rclone **Crypt** remote so that files are encrypted
client-side before they leave the server.

```bash
docker compose --profile backup run --rm rclone config
```

1. Choose `n` → *New remote*.
2. Name it `backup-crypt` (or similar).
3. Choose type `crypt`.
4. Set the *remote* to point at your existing remote's bucket, e.g. `gdrive:Backups`.
5. Choose password + salt and store them somewhere safe (e.g. a password manager).

From this point on, always reference `backup-crypt:` in your upload/download commands
instead of the raw remote.

---

## Usage

### Manual upload

```bash
uv run tools.py backup-upload --remote backup-crypt:
```

### Manual download (disaster recovery)

```bash
uv run tools.py backup-download --remote backup-crypt:
```

### Direct Docker invocation

You can also call rclone directly — useful for one-off inspection or testing:

```bash
# List remote contents
docker compose --profile backup run --rm rclone ls backup-crypt:

# Check copy without transferring (dry-run)
docker compose --profile backup run --rm rclone copy /backups backup-crypt: --dry-run
```

---

## Automated Daily Backups (Cron)

The following command adds an entry to **root's** crontab (sudo required):

```bash
# Default schedule: 02:00 AM every night
uv run tools.py setup-backup-cron

# Custom schedule via --schedule flag (standard crontab syntax)
uv run tools.py setup-backup-cron --schedule "0 4 * * *"   # 04:00 AM

# Or set once in .env and forget:
#   BACKUP_CRON_SCHEDULE=0 4 * * *
uv run tools.py setup-backup-cron
```

The schedule is resolved in this priority order:
1. The `--schedule` / `-s` CLI flag
2. The `BACKUP_CRON_SCHEDULE` environment variable (set in `.env`)
3. Hardcoded default: `0 2 * * *` (02:00 AM daily)

The job:
1. Creates a local backup of all service data and configuration archives.
2. Uploads the backup to the configured remote.
3. Deletes remote files older than 14 days.
4. Logs all output to `backups/cron.log`.

The crontab is installed for root so that Docker and the bind-mounted volumes are always
accessible. To remove or edit the entry run `sudo crontab -e`.

---

## Retention Policy

The `backup-upload` command (and the cron job) automatically deletes files from the
remote that are **older than 14 days** using `rclone delete --min-age 14d`.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `image not found` / build errors | Run `docker compose --profile backup build rclone` |
| `no remote found` / config empty | Run `uv run tools.py backup-config` to set up remotes |
| Permission denied on `/backups` | Ensure `./backups/` exists on the host (`mkdir -p backups`) |
| Cron job not running | Check `/var/log/syslog` and `backups/cron.log`; verify `sudo crontab -l` |
