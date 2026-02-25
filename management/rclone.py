import os
import typer
from .runner import CommandRunner


class RCloneManager:
    """Manages cloud backups using the rclone Docker container."""

    def __init__(self):
        self.backup_dir = os.path.abspath("backups")
        # Config is volume-mounted into the container at /config/rclone
        # so rclone picks it up automatically — no --config flag needed.

    def _run(self, *args: str):
        """Run an rclone command inside the Docker container."""
        joined = " ".join(args)
        cmd = f"docker compose --profile backup run --rm rclone {joined}"
        CommandRunner.run(cmd)

    def _ensure_backup_dir(self):
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

    def upload(self, remote: str = "backup:"):
        """Upload the local backups/ directory to a remote and rotate old files."""
        typer.echo(f"📤  Uploading backups to {remote} via Docker container...")
        # Inside the container ./backups is mounted at /backups
        self._run("copy", "/backups", remote, "--progress")

        typer.echo("🗑️   Cleaning up remote files older than 14 days...")
        self._run("delete", remote, "--min-age", "14d")

        typer.secho("✅  Upload and rotation complete.", fg=typer.colors.GREEN)

    def download(self, remote: str = "remote:backup"):
        """Download backups from a remote into the local backups/ directory."""
        typer.echo(f"📥  Downloading backups from {remote} via Docker container...")
        self._ensure_backup_dir()
        self._run("copy", remote, "/backups", "--progress")
        typer.secho("✅  Download complete.", fg=typer.colors.GREEN)

    def config(self):
        """Open the interactive rclone config wizard inside the container."""
        typer.echo("🔧  Launching rclone config inside Docker container...")
        typer.echo("    Config will be saved to services/rclone/config/rclone.conf")
        cmd = "docker compose --profile backup run --rm rclone config"
        CommandRunner.run(cmd)


    def setup_cron(self, schedule: str | None = None):
        """Add a root-crontab entry for daily backup → upload.

        The cron schedule is resolved in priority order:
          1. ``schedule`` argument (passed from CLI --schedule option)
          2. ``BACKUP_CRON_SCHEDULE`` environment variable (set in .env)
          3. Hardcoded default: ``0 5 * * 3``  (05:00 AM, every mittwoch)
        """
        repo_dir = os.getcwd()
        uv_path = CommandRunner.run("which uv", capture=True).strip() or "uv"

        # Resolve schedule with priority: CLI arg > .env var > default
        resolved_schedule = (
            schedule
            or os.environ.get("BACKUP_CRON_SCHEDULE")
            or "0 5 * * 3"
        )

        # Build cron entry — runs as root so Docker socket + file access is guaranteed
        cron_cmd = (
            f"{resolved_schedule} cd {repo_dir} && "
            f"{uv_path} run tools.py docker stop && "
            f"{uv_path} run tools.py backup-create && "
            f"{uv_path} run tools.py backup-upload ; "
            f"{uv_path} run tools.py docker deploy "
            f">> {repo_dir}/backups/cron.log 2>&1"
        )

        typer.echo(f"⏰  Setting up crontab entry with schedule: {resolved_schedule!r}")

        # Read existing root crontab
        current_cron = CommandRunner.run("sudo crontab -l", check=False, capture=True) or ""

        if "tools.py backup-upload" in current_cron:
            typer.echo("Crontab entry already exists — nothing to do.")
            typer.echo("  Remove it with 'sudo crontab -e' to change the schedule.")
            return

        new_cron = current_cron.rstrip("\n") + f"\n{cron_cmd}\n"

        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".cron", delete=False) as tf:
            tf.write(new_cron)
            temp_name = tf.name

        CommandRunner.run(f"sudo crontab {temp_name}")
        os.unlink(temp_name)
        typer.secho("✅  Crontab entry added successfully.", fg=typer.colors.GREEN)
