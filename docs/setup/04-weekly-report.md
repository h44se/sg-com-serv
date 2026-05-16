# Weekly Owner Report (SMTP)

This guide configures a weekly email report with the key health and security metrics for your root server.

## What the report includes

- Host summary: uptime/load, memory usage, swap usage, disk usage.
- Docker status: running/healthy service ratio.
- Backup status: age of newest backup archive in `backups/`.
- Security status: Fail2Ban jail count and CrowdSec alert count.
- Update posture: number of pending APT updates.

Each check is evaluated as `OK`, `WARN`, or `CRIT` based on configurable thresholds.

## 1) Configure SMTP and thresholds

Add these variables to `.env`:

```bash
REPORT_SMTP_HOST=smtp.example.com
REPORT_SMTP_PORT=587
REPORT_SMTP_USER=your-smtp-user@example.com
REPORT_SMTP_PASS=your-smtp-app-password
REPORT_SMTP_STARTTLS=true
REPORT_FROM=server-report@example.com
REPORT_TO=you@example.com
REPORT_SUBJECT_PREFIX=[server]
REPORT_CRON_SCHEDULE=0 7 * * 1

REPORT_DISK_WARN_PCT=80
REPORT_DISK_CRIT_PCT=90
REPORT_MEM_WARN_PCT=85
REPORT_MEM_CRIT_PCT=95
REPORT_SWAP_WARN_PCT=25
REPORT_SWAP_CRIT_PCT=50
REPORT_BACKUP_WARN_DAYS=8
REPORT_BACKUP_CRIT_DAYS=14
```

`REPORT_TO` supports comma-separated recipients.

## 2) Send a test report manually

```bash
uv run tools.py report-send
```

If SMTP delivery fails, the report is written to `backups/reports/weekly_YYYYMMDD_HHMMSS.txt`.

## 3) Install weekly cron

Recommended schedule: Monday 07:00 server time.

```bash
uv run tools.py setup-report-cron --schedule "0 7 * * 1"
```

Without `--schedule`, the command uses:
1. `REPORT_CRON_SCHEDULE`
2. fallback `0 7 * * 1`

The cron output is appended to `backups/reports/cron.log`.
