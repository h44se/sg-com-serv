import os
import json
import datetime
import shutil
import subprocess
import typer
from .runner import CommandRunner


class BackupManager:
    """Manages creation and restoration of service backups."""

    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = os.path.abspath(backup_dir)
        self.repo_dir = os.getcwd()
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

    # ──────────────────────────────────────────────────────────────────
    # Volume discovery
    # ──────────────────────────────────────────────────────────────────

    def _get_compose_volumes(self) -> list[str]:
        """Return all top-level named volume names from docker-compose.yml.

        Uses ``docker compose config --format json`` to get the fully-resolved
        Compose config (handles variable substitution, overrides, etc.) and
        extracts the ``volumes`` keys.  Falls back to an empty list on error
        so the rest of the backup still proceeds.
        """
        try:
            result = subprocess.run(
                ["docker", "compose", "config", "--format", "json"],
                capture_output=True,
                text=True,
                check=True,
                cwd=self.repo_dir,
            )
            config = json.loads(result.stdout)
            # Top-level "volumes" is a dict keyed by volume name
            volumes = list((config.get("volumes") or {}).keys())
            if volumes:
                typer.echo(f"📦  Discovered named volumes: {', '.join(volumes)}")
            else:
                typer.echo("ℹ️   No named volumes found in docker-compose.yml.")
            return volumes
        except subprocess.CalledProcessError as e:
            typer.secho(
                f"⚠️   Could not query Compose volumes: {e.stderr.strip()}",
                fg=typer.colors.YELLOW,
            )
            return []
        except (json.JSONDecodeError, KeyError) as e:
            typer.secho(
                f"⚠️   Could not parse Compose config: {e}",
                fg=typer.colors.YELLOW,
            )
            return []

    def _backup_volume(self, vol: str, tmp_dir: str) -> bool:
        """Tar a named Docker volume into tmp_dir/<vol>.tar.gz.  Returns True on success."""
        check = subprocess.run(
            f"docker volume inspect {vol}",
            shell=True,
            capture_output=True,
        )
        if check.returncode != 0:
            typer.secho(f"  ⚠️   Volume '{vol}' not found — skipping.", fg=typer.colors.YELLOW)
            return False

        typer.echo(f"  📦  Backing up volume: {vol}")
        CommandRunner.run(
            f"docker run --rm "
            f"-v {vol}:/volume:ro "
            f"-v {tmp_dir}:/backup "
            f"alpine tar czf /backup/{vol}.tar.gz -C /volume ."
        )
        return True

    def _restore_volume(self, vol: str, content_dir: str):
        """Restore a named Docker volume from content_dir/<vol>.tar.gz."""
        vol_archive = os.path.join(content_dir, f"{vol}.tar.gz")
        if not os.path.exists(vol_archive):
            typer.secho(f"  ⚠️   Archive for volume '{vol}' not in backup — skipping.", fg=typer.colors.YELLOW)
            return

        typer.echo(f"  📦  Restoring volume: {vol}")
        CommandRunner.run(f"docker volume create {vol}")
        CommandRunner.run(
            f"docker run --rm "
            f"-v {vol}:/volume "
            f"-v {content_dir}:/backup "
            f"alpine sh -c 'rm -rf /volume/* && tar xzf /backup/{vol}.tar.gz -C /volume'"
        )

    # ──────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────

    def create(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_folder_name = f"backup_{timestamp}"
        tmp_dir = os.path.join(self.backup_dir, backup_folder_name)
        os.makedirs(tmp_dir)

        typer.echo("⏹️   Stopping services for consistent backup...")
        CommandRunner.run("docker compose down", check=False)

        # ── Bind-mount files & directories ──────────────────────────
        items_to_copy = [".env", "docker-compose.yml", "services"]
        for item in items_to_copy:
            src = os.path.join(self.repo_dir, item)
            if os.path.exists(src):
                typer.echo(f"  📄  Backing up {item}...")
                dst = os.path.join(tmp_dir, item)
                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
            else:
                typer.secho(f"  ⚠️   {item} not found — skipping.", fg=typer.colors.YELLOW)

        # ── Named Docker volumes (auto-discovered from docker-compose.yml) ──
        typer.echo("🔍  Discovering named volumes from docker-compose.yml...")
        volumes = self._get_compose_volumes()
        for vol in volumes:
            self._backup_volume(vol, tmp_dir)

        # ── Create master archive ────────────────────────────────────
        master_archive = os.path.join(self.backup_dir, f"{backup_folder_name}.tar.gz")
        typer.echo("🗜️   Creating master archive...")
        CommandRunner.run(f"tar -czf {master_archive} -C {self.backup_dir} {backup_folder_name}")
        shutil.rmtree(tmp_dir)

        typer.secho(f"✅  Backup created: {master_archive}", fg=typer.colors.GREEN)
        typer.echo("▶️   Restarting services...")
        CommandRunner.run("docker compose up -d")

    def restore(self, archive_path: str):
        archive_path = os.path.abspath(archive_path)
        if not os.path.exists(archive_path):
            typer.secho(f"Error: Archive {archive_path} not found.", fg=typer.colors.RED)
            raise typer.Exit(code=1)

        typer.echo("⏹️   Stopping services for restore...")
        CommandRunner.run("docker compose down", check=False)

        tmp_extract_dir = os.path.join(self.backup_dir, "tmp_restore")
        if os.path.exists(tmp_extract_dir):
            shutil.rmtree(tmp_extract_dir)
        os.makedirs(tmp_extract_dir)

        typer.echo("📂  Extracting archive...")
        CommandRunner.run(f"tar -xzf {archive_path} -C {tmp_extract_dir}")

        extracted_content = os.listdir(tmp_extract_dir)
        if not extracted_content:
            typer.secho("Error: Backup archive is empty.", fg=typer.colors.RED)
            return

        content_dir = os.path.join(tmp_extract_dir, extracted_content[0])

        # ── Restore bind-mount files & directories ───────────────────
        items_to_restore = [".env", "docker-compose.yml", "services"]
        for item in items_to_restore:
            src = os.path.join(content_dir, item)
            dst = os.path.join(self.repo_dir, item)
            if os.path.exists(src):
                typer.echo(f"  📄  Restoring {item}...")
                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)

        # ── Restore named volumes (discovered from the restored compose file) ──
        # Re-read volumes from the *restored* docker-compose.yml so we restore
        # exactly what was backed up, even if the live compose file differs.
        typer.echo("🔍  Discovering volumes to restore from backup's docker-compose.yml...")
        restored_compose = os.path.join(self.repo_dir, "docker-compose.yml")
        if os.path.exists(restored_compose):
            volumes = self._get_compose_volumes()
        else:
            # Fallback: restore any .tar.gz that looks like a volume archive
            volumes = [
                f.replace(".tar.gz", "")
                for f in os.listdir(content_dir)
                if f.endswith(".tar.gz")
            ]
            typer.echo(f"  ℹ️   Falling back to archive contents: {volumes}")

        for vol in volumes:
            self._restore_volume(vol, content_dir)

        shutil.rmtree(tmp_extract_dir)
        typer.secho("✅  Restore complete!", fg=typer.colors.GREEN)
        typer.echo("▶️   Restarting services...")
        CommandRunner.run("docker compose up -d")
