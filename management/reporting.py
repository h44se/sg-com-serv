import datetime
import os
import smtplib
import socket
import ssl
import subprocess
import tempfile
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path

import typer

from .runner import CommandRunner


@dataclass
class Finding:
    status: str
    section: str
    metric: str
    value: str
    threshold: str
    note: str = ""


class ReportingManager:
    def __init__(self):
        self.repo_dir = Path(os.getcwd())
        self.backups_dir = self.repo_dir / "backups"
        self.report_dir = self.backups_dir / "reports"
        self.now = datetime.datetime.now()
        self.hostname = socket.gethostname()
        self.findings: list[Finding] = []

    def send_weekly_report(self):
        typer.secho("Preparing weekly server report...", fg=typer.colors.CYAN)
        self._collect_all()
        report_text = self._render_report()
        subject = self._build_subject()

        try:
            self._send_smtp(subject, report_text)
            typer.secho("Weekly report sent successfully.", fg=typer.colors.GREEN)
        except Exception as exc:
            self._persist_report(report_text)
            typer.secho(
                f"Failed to send report via SMTP: {exc}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=1)

    def setup_cron(self, schedule: str | None = None):
        resolved_schedule = (
            schedule
            or os.environ.get("REPORT_CRON_SCHEDULE")
            or "0 7 * * 1"
        )
        repo_dir = str(self.repo_dir)
        uv_path = CommandRunner.run("which uv", capture=True).strip() or "uv"
        cron_cmd = (
            f"{resolved_schedule} cd {repo_dir} && "
            f"{uv_path} run tools.py report-send "
            f">> {repo_dir}/backups/reports/cron.log 2>&1"
        )

        typer.echo(f"Setting weekly report schedule to: {resolved_schedule!r}")
        self.report_dir.mkdir(parents=True, exist_ok=True)
        current_cron = CommandRunner.run("sudo crontab -l", check=False, capture=True) or ""
        if "tools.py report-send" in current_cron:
            typer.echo("Crontab entry for weekly report already exists.")
            typer.echo("Remove it via 'sudo crontab -e' to change schedule.")
            return

        new_cron = current_cron.rstrip("\n") + f"\n{cron_cmd}\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".cron", delete=False) as tf:
            tf.write(new_cron)
            temp_name = tf.name

        CommandRunner.run(f"sudo crontab {temp_name}")
        os.unlink(temp_name)
        typer.secho("Weekly report cron added successfully.", fg=typer.colors.GREEN)

    def _collect_all(self):
        self._collect_uptime_load()
        self._collect_memory_swap()
        self._collect_disk_usage()
        self._collect_docker_health()
        self._collect_backup_status()
        self._collect_fail2ban()
        self._collect_crowdsec()
        self._collect_apt_updates()

    def _run_capture(self, cmd: str) -> tuple[int, str, str]:
        proc = subprocess.run(
            cmd,
            shell=True,
            cwd=self.repo_dir,
            capture_output=True,
            text=True,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()

    def _threshold(self, value: float, warn: float, crit: float) -> str:
        if value >= crit:
            return "CRIT"
        if value >= warn:
            return "WARN"
        return "OK"

    def _env_float(self, key: str, default: float) -> float:
        raw = os.environ.get(key, str(default))
        try:
            return float(raw)
        except ValueError:
            return default

    def _collect_uptime_load(self):
        code, out, _ = self._run_capture("uptime")
        if code != 0:
            self.findings.append(Finding("WARN", "System", "uptime", "n/a", "available", "Command failed"))
            return
        self.findings.append(Finding("OK", "System", "uptime/load", out, "informational", ""))

    def _collect_memory_swap(self):
        code, out, _ = self._run_capture("free -m")
        if code != 0:
            self.findings.append(Finding("WARN", "System", "memory", "n/a", "available", "Command failed"))
            return

        lines = [line for line in out.splitlines() if line.strip()]
        mem = next((line for line in lines if line.startswith("Mem:")), "")
        swap = next((line for line in lines if line.startswith("Swap:")), "")
        if mem:
            parts = mem.split()
            total = float(parts[1])
            used = float(parts[2])
            used_pct = (used / total * 100.0) if total else 0.0
            mem_warn = self._env_float("REPORT_MEM_WARN_PCT", 85)
            mem_crit = self._env_float("REPORT_MEM_CRIT_PCT", 95)
            status = self._threshold(used_pct, mem_warn, mem_crit)
            self.findings.append(
                Finding(
                    status,
                    "System",
                    "memory used",
                    f"{used_pct:.1f}% ({int(used)}/{int(total)} MB)",
                    f"warn>={mem_warn:.0f}% crit>={mem_crit:.0f}%",
                )
            )

        if swap:
            parts = swap.split()
            total = float(parts[1])
            used = float(parts[2])
            used_pct = (used / total * 100.0) if total else 0.0
            swap_warn = self._env_float("REPORT_SWAP_WARN_PCT", 25)
            swap_crit = self._env_float("REPORT_SWAP_CRIT_PCT", 50)
            status = self._threshold(used_pct, swap_warn, swap_crit)
            self.findings.append(
                Finding(
                    status,
                    "System",
                    "swap used",
                    f"{used_pct:.1f}% ({int(used)}/{int(total)} MB)",
                    f"warn>={swap_warn:.0f}% crit>={swap_crit:.0f}%",
                )
            )

    def _collect_disk_usage(self):
        code, out, _ = self._run_capture("df -P")
        if code != 0:
            self.findings.append(Finding("WARN", "System", "disk usage", "n/a", "available", "Command failed"))
            return

        disk_warn = self._env_float("REPORT_DISK_WARN_PCT", 80)
        disk_crit = self._env_float("REPORT_DISK_CRIT_PCT", 90)
        for line in out.splitlines()[1:]:
            parts = line.split()
            if len(parts) < 6:
                continue
            mount = parts[5]
            if mount not in {"/", "/var", "/home"}:
                continue
            used_pct = float(parts[4].replace("%", ""))
            status = self._threshold(used_pct, disk_warn, disk_crit)
            self.findings.append(
                Finding(
                    status,
                    "System",
                    f"disk {mount}",
                    f"{used_pct:.0f}%",
                    f"warn>={disk_warn:.0f}% crit>={disk_crit:.0f}%",
                )
            )

    def _collect_docker_health(self):
        code, out, err = self._run_capture("docker compose ps --format json")
        if code != 0:
            note = err or "docker compose ps failed"
            self.findings.append(Finding("WARN", "Containers", "compose status", "n/a", "available", note))
            return

        lines = [line for line in out.splitlines() if line.strip()]
        if not lines:
            self.findings.append(Finding("WARN", "Containers", "compose status", "no services", "at least 1", "No compose services found"))
            return

        bad = 0
        total = 0
        for line in lines:
            total += 1
            if "running" not in line.lower() or "unhealthy" in line.lower():
                bad += 1

        status = "OK" if bad == 0 else "CRIT"
        self.findings.append(
            Finding(status, "Containers", "healthy/running", f"{total - bad}/{total}", "all running+healthy", "")
        )

    def _collect_backup_status(self):
        if not self.backups_dir.exists():
            self.findings.append(Finding("CRIT", "Backups", "backup directory", "missing", "present", "No backups directory"))
            return

        archives = sorted(self.backups_dir.glob("backup_*.tar.gz"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not archives:
            self.findings.append(Finding("CRIT", "Backups", "latest backup", "none", "<=7 days", "No backup archives found"))
            return

        latest = archives[0]
        age = self.now - datetime.datetime.fromtimestamp(latest.stat().st_mtime)
        age_days = age.total_seconds() / 86400
        warn_days = self._env_float("REPORT_BACKUP_WARN_DAYS", 8)
        crit_days = self._env_float("REPORT_BACKUP_CRIT_DAYS", 14)
        status = self._threshold(age_days, warn_days, crit_days)
        self.findings.append(
            Finding(
                status,
                "Backups",
                "latest backup age",
                f"{age_days:.1f} days ({latest.name})",
                f"warn>={warn_days:.0f}d crit>={crit_days:.0f}d",
            )
        )

    def _collect_fail2ban(self):
        code, out, err = self._run_capture("sudo fail2ban-client status")
        if code != 0:
            self.findings.append(Finding("WARN", "Security", "fail2ban", "unavailable", "available", err or "Command failed"))
            return

        jail_line = next((line for line in out.splitlines() if "Jail list:" in line), "")
        jail_count = len([j.strip() for j in jail_line.split(":", 1)[-1].split(",") if j.strip()]) if jail_line else 0
        status = "OK" if jail_count > 0 else "WARN"
        self.findings.append(Finding(status, "Security", "fail2ban jails", str(jail_count), ">=1", ""))

    def _collect_crowdsec(self):
        code, out, err = self._run_capture("docker exec crowdsec cscli alerts list -o raw")
        if code != 0:
            self.findings.append(Finding("WARN", "Security", "crowdsec alerts", "unavailable", "available", err or "Command failed"))
            return

        alert_count = len([line for line in out.splitlines() if line.strip()])
        status = "WARN" if alert_count > 0 else "OK"
        self.findings.append(Finding(status, "Security", "crowdsec alerts", str(alert_count), "0 preferred", ""))

    def _collect_apt_updates(self):
        code, out, err = self._run_capture("apt list --upgradable 2>/dev/null")
        if code != 0:
            self.findings.append(Finding("WARN", "Updates", "apt upgradable", "unavailable", "available", err or "Command failed"))
            return

        lines = [line for line in out.splitlines() if line.strip() and not line.startswith("Listing")]
        count = len(lines)
        status = "OK" if count == 0 else "WARN"
        self.findings.append(Finding(status, "Updates", "apt updates pending", str(count), "0 preferred", ""))

    def _build_subject(self) -> str:
        prefix = os.environ.get("REPORT_SUBJECT_PREFIX", "")
        date_part = self.now.strftime("%Y-%m-%d")
        subject = f"Weekly Root Server Report - {self.hostname} - {date_part}"
        return f"{prefix} {subject}".strip()

    def _render_report(self) -> str:
        counts = {"CRIT": 0, "WARN": 0, "OK": 0}
        for finding in self.findings:
            counts[finding.status] = counts.get(finding.status, 0) + 1

        lines: list[str] = []
        lines.append(f"Weekly Root Server Report - {self.hostname}")
        lines.append(f"Generated: {self.now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        lines.append("")
        lines.append("Executive Summary")
        lines.append(f"CRIT: {counts['CRIT']} | WARN: {counts['WARN']} | OK: {counts['OK']}")
        lines.append("")

        if counts["CRIT"] > 0 or counts["WARN"] > 0:
            lines.append("Action Required")
            for finding in self.findings:
                if finding.status in {"CRIT", "WARN"}:
                    lines.append(
                        f"{finding.status} | {finding.section} | {finding.metric} | {finding.value} | {finding.threshold} | {finding.note}"
                    )
            lines.append("")

        lines.append("Detailed Metrics")
        for finding in self.findings:
            lines.append(
                f"{finding.status} | {finding.section} | {finding.metric} | {finding.value} | {finding.threshold} | {finding.note}"
            )

        return "\n".join(lines)

    def _send_smtp(self, subject: str, body: str):
        host = self._required_env("REPORT_SMTP_HOST")
        port = int(os.environ.get("REPORT_SMTP_PORT", "587"))
        user = self._required_env("REPORT_SMTP_USER")
        password = self._required_env("REPORT_SMTP_PASS")
        from_addr = os.environ.get("REPORT_FROM", user)
        recipients = self._parse_recipients(self._required_env("REPORT_TO"))
        use_starttls = os.environ.get("REPORT_SMTP_STARTTLS", "true").lower() in {"1", "true", "yes", "on"}

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = ", ".join(recipients)
        msg.set_content(body)

        with smtplib.SMTP(host, port, timeout=30) as smtp:
            smtp.ehlo()
            if use_starttls:
                smtp.starttls(context=ssl.create_default_context())
                smtp.ehlo()
            smtp.login(user, password)
            smtp.send_message(msg)

    def _required_env(self, key: str) -> str:
        value = os.environ.get(key, "").strip()
        if not value:
            raise RuntimeError(f"Missing required environment variable: {key}")
        return value

    def _parse_recipients(self, raw: str) -> list[str]:
        recipients = [item.strip() for item in raw.split(",") if item.strip()]
        if not recipients:
            raise RuntimeError("REPORT_TO must include at least one email address")
        return recipients

    def _persist_report(self, report_text: str):
        self.report_dir.mkdir(parents=True, exist_ok=True)
        timestamp = self.now.strftime("%Y%m%d_%H%M%S")
        path = self.report_dir / f"weekly_{timestamp}.txt"
        path.write_text(report_text + "\n", encoding="utf-8")
        typer.echo(f"Stored report at {path}")
