import os
import typer
from .runner import CommandRunner

class RCloneManager:
    """Manages cloud backups using rclone."""

    def __init__(self, config_path: str = "services/rclone/rclone.conf"):
        self.config_path = os.path.abspath(config_path)
        self.backup_dir = os.path.abspath("backups")
        
    def _check_installed(self):
        try:
            CommandRunner.run("rclone version", capture=True)
            return True
        except Exception:
            typer.secho("Error: rclone is not installed on the host system.", fg=typer.colors.RED)
            typer.echo("Follow the setup guide: docs/setup/01-first-steps.md")
            return False

    def upload(self, remote: str = "remote:backup"):
        if not self._check_installed():
            return

        typer.echo(f"Uploading backups to {remote}...")
        # Use --config to specify our local config path
        cmd = f"rclone --config {self.config_path} copy {self.backup_dir} {remote} --progress"
        CommandRunner.run(cmd)
        
        # Auto-rotation: Delete files older than 2 weeks on the remote
        typer.echo("Cleaning up old backups on remote (older than 14 days)...")
        cleanup_cmd = f"rclone --config {self.config_path} delete {remote} --min-age 14d"
        CommandRunner.run(cleanup_cmd)
        typer.secho("✅ Upload and rotation complete.", fg=typer.colors.GREEN)

    def download(self, remote: str = "remote:backup"):
        if not self._check_installed():
            return

        typer.echo(f"Downloading backups from {remote}...")
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
            
        cmd = f"rclone --config {self.config_path} copy {remote} {self.backup_dir} --progress"
        CommandRunner.run(cmd)
        typer.secho("✅ Download complete.", fg=typer.colors.GREEN)

    def setup_cron(self):
        """Adds a cronjob for daily backup and upload."""
        # We assume the user wants to run 'tools.py backup-create' and then 'tools.py backup-upload'
        script_path = os.path.abspath("tools.py")
        repo_dir = os.getcwd()
        
        # Find uv path
        uv_path = CommandRunner.run("which uv", capture=True).strip()
        if not uv_path:
            uv_path = "uv" # fallback
            
        # Build the cron command
        cron_cmd = f"0 2 * * * cd {repo_dir} && {uv_path} run tools.py backup-create && {uv_path} run tools.py backup-upload >> {repo_dir}/backups/cron.log 2>&1"
        
        typer.echo("Setting up daily cronjob (at 02:00 AM)...")
        
        # Check if already exists
        current_cron = CommandRunner.run("crontab -l", check=False, capture=True)
        if "tools.py backup-upload" in current_cron:
            typer.echo("Cronjob already exists.")
            return

        new_cron = current_cron + f"\n{cron_cmd}\n"
        
        # Write back
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tf:
            tf.write(new_cron)
            temp_name = tf.name
            
        CommandRunner.run(f"crontab {temp_name}")
        os.unlink(temp_name)
        typer.secho("✅ Cronjob added successfully.", fg=typer.colors.GREEN)
