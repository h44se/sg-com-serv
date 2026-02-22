import typer
from .system import SystemManager
from .backup import BackupManager
from .docker import DockerManager
from .runner import CommandRunner

class MaintenanceManager:
    """Orchestrates multi-step maintenance and cleanup tasks."""
    
    def housekeep(self):
        typer.secho("🚀 Starting Housekeeping Routine", fg=typer.colors.CYAN, bold=True)
        
        # 1. System Update
        typer.echo("\n# Step 1: Updating System Packages")
        SystemManager().update()
        
        # 2. Backup
        typer.echo("\n# Step 2: Creating Safety Backup")
        BackupManager().create()
        
        # 3. Check for Container Updates
        typer.echo("\n# Step 3: Checking for Container Updates")
        DockerManager().check_updates()
        
        # 4. Docker Cleanup
        typer.echo("\n# Step 4: Cleaning up unused Docker resources")
        CommandRunner.run("docker system prune -f")
        
        typer.secho("\n✅ Housekeeping Complete!", fg=typer.colors.GREEN, bold=True)
