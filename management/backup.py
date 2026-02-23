import os
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

    def create(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_folder_name = f"backup_{timestamp}"
        tmp_dir = os.path.join(self.backup_dir, backup_folder_name)
        os.makedirs(tmp_dir)

        typer.echo("Stopping services for consistent backup...")
        CommandRunner.run("docker compose down", check=False)

        # Backup files/directories
        items_to_copy = [".env", "docker-compose.yml", "services"]
        for item in items_to_copy:
            src = os.path.join(self.repo_dir, item)
            if os.path.exists(src):
                typer.echo(f"Backing up {item}...")
                dst = os.path.join(tmp_dir, item)
                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)

        # Backup named volumes
        volumes = ["netdataconfig", "netdatalib", "netdatacache", "acme"]
        for vol in volumes:
            typer.echo(f"Backing up volume: {vol}")
            vol_check = subprocess.run(f"docker volume inspect {vol}", shell=True, capture_output=True)
            if vol_check.returncode == 0:
                CommandRunner.run(f"docker run --rm -v {vol}:/volume -v {tmp_dir}:/backup alpine tar czf /backup/{vol}.tar.gz -C /volume .")
            else:
                typer.echo(f"Warning: Volume {vol} not found, skipping.")

        # Create master archive
        master_archive = os.path.join(self.backup_dir, f"{backup_folder_name}.tar.gz")
        CommandRunner.run(f"tar -czf {master_archive} -C {self.backup_dir} {backup_folder_name}")
        shutil.rmtree(tmp_dir)
        
        typer.echo(f"Backup created successfully: {master_archive}")
        typer.echo("Restarting services...")
        CommandRunner.run("docker compose up -d")

    def restore(self, archive_path: str):
        archive_path = os.path.abspath(archive_path)
        if not os.path.exists(archive_path):
            typer.echo(f"Error: Archive {archive_path} not found.")
            raise typer.Exit(code=1)

        typer.echo("Stopping services for restore...")
        CommandRunner.run("docker compose down", check=False)

        tmp_extract_dir = os.path.join(self.backup_dir, "tmp_restore")
        if os.path.exists(tmp_extract_dir):
            shutil.rmtree(tmp_extract_dir)
        os.makedirs(tmp_extract_dir)

        typer.echo("Extracting archive...")
        CommandRunner.run(f"tar -xzf {archive_path} -C {tmp_extract_dir}")
        
        extracted_content = os.listdir(tmp_extract_dir)
        if not extracted_content:
            typer.echo("Error: Backup archive is empty.")
            return
        
        content_dir = os.path.join(tmp_extract_dir, extracted_content[0])

        # Restore files/directories
        items_to_restore = [".env", "docker-compose.yml", "services"]
        for item in items_to_restore:
            src = os.path.join(content_dir, item)
            dst = os.path.join(self.repo_dir, item)
            if os.path.exists(src):
                typer.echo(f"Restoring {item}...")
                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)

        # Restore named volumes
        volumes = ["netdataconfig", "netdatalib", "netdatacache", "acme"]
        for vol in volumes:
            vol_archive = os.path.join(content_dir, f"{vol}.tar.gz")
            if os.path.exists(vol_archive):
                typer.echo(f"Restoring volume: {vol}")
                CommandRunner.run(f"docker volume create {vol}")
                CommandRunner.run(f"docker run --rm -v {vol}:/volume -v {content_dir}:/backup alpine sh -c 'rm -rf /volume/* && tar xzf /backup/{vol}.tar.gz -C /volume'")

        shutil.rmtree(tmp_extract_dir)
        typer.echo("Restore complete!")
        typer.echo("Restarting services...")
        CommandRunner.run("docker compose up -d")
