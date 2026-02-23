import sys
import typer
from typing import List
from management.system import SystemManager
from management.docker import DockerManager
from management.backup import BackupManager
from management.maintenance import MaintenanceManager
from management.utils import lint_markdown, fix_markdown_newlines, setup_dotenv

app = typer.Typer(help="CLI tools for server documentation and setup management.")

@app.command()
def list_services():
    """
    Visualize which services are configured and available in this project.
    """
    typer.echo("")
    typer.secho("📋 Configured Services", fg=typer.colors.CYAN, bold=True)
    typer.echo("─" * 60)
    
    services = [
        ("Host", "Fail2Ban", "Intrusion Prevention (SSH/Proxy)"),
        ("Host", "SSH", "Secure Remote Access"),
        ("Docker", "Dashboard", "Central Services Landing Page"),
        ("Docker", "CrowdSec", "Community Threat Intelligence"),
        ("Docker", "Nginx Proxy", "Automated Reverse Proxy & SSL"),
        ("Docker", "ACME Companion", "SSL (Let's Encrypt) Automation"),
        ("Docker", "TeamSpeak 3", "High-Performance Voice Server"),
        ("Docker", "Netdata", "Real-time System Monitoring"),
    ]
    
    for type_, name, desc in services:
        color = typer.colors.GREEN if type_ == "Docker" else typer.colors.YELLOW
        type_str = typer.style(f"{type_}", fg=color)
        name_str = typer.style(name, bold=True)
        typer.echo(f"[{type_str:^16}] {name_str:<20} │ {desc}")
    
    typer.echo("─" * 60)
    typer.echo("Use 'uv run tools.py docker status' to check live container status.")
    typer.echo("")

@app.command()
def setup_system(
    skip_docker: bool = typer.Option(False, "--skip-docker", help="Skip Docker installation."),
    ports: List[str] = typer.Option(["80/tcp", "443/tcp", "19999/tcp", "9987/udp", "10011/tcp", "30033/tcp"], "--port", "-p", help="Extra ports to allow in firewall.")
):
    """
    Perform full base system setup and hardening.
    """
    sys_mgr = SystemManager()
    sys_mgr.update()
    sys_mgr.harden_ssh()
    sys_mgr.setup_firewall(ports)
    sys_mgr.setup_auto_updates()
    sys_mgr.setup_fail2ban()
    setup_dotenv()
    if not skip_docker:
        sys_mgr.setup_docker()
    typer.echo("Base system setup complete!")

@app.command()
def system_update():
    """
    Update system packages (apt update & upgrade).
    """
    SystemManager().update()
    typer.echo("System update complete!")

docker_app = typer.Typer(help="Docker service management commands.")
app.add_typer(docker_app, name="docker")

@docker_app.command()
def deploy(service: str = typer.Argument("", help="Name of the service (optional).")):
    """
    Deploy dockerized services. Starts all if no service is specified.
    """
    DockerManager().deploy(service)

@docker_app.command()
def stop():
    """
    Stop all dockerized services.
    """
    DockerManager().stop()

@docker_app.command()
def pull():
    """
    Pull latest images for all services.
    """
    DockerManager().pull()

@docker_app.command()
def rebuild():
    """
    Force rebuild and restart of all services.
    """
    DockerManager().rebuild()

@docker_app.command()
def status():
    """
    Show status of dockerized services.
    """
    DockerManager().status()

@docker_app.command()
def logs(
    service: str = typer.Argument("", help="Name of the service (optional)."),
    tail: int = typer.Option(100, "--tail", "-t", help="Number of lines to show."),
    no_follow: bool = typer.Option(False, "--no-follow", help="Disable log following.")
):
    """
    View service logs.
    """
    DockerManager().logs(service=service, follow=not no_follow, tail=tail)

@docker_app.command()
def check_updates():
    """
    Check for available container updates using Watchtower (Monitor-only).
    """
    DockerManager().check_updates()

@docker_app.command()
def test():
    """
    Validate docker-compose configuration using dry-run.
    """
    DockerManager().test()

@app.command()
def backup_create(
    directory: str = typer.Option("backups", "--dir", "-d", help="Directory to store the backup.")
):
    """Create a full backup of services data and configuration."""
    BackupManager(backup_dir=directory).create()

@app.command()
def backup_restore(
    archive: str = typer.Argument(..., help="Path to the backup tar.gz archive."),
    directory: str = typer.Option("backups", "--dir", "-d", help="Directory where temporary files are handled.")
):
    """Restore services data and configuration from a backup archive."""
    BackupManager(backup_dir=directory).restore(archive)

@app.command()
def lint(
    paths: List[str] = typer.Argument(["docs", "README.md"]),
    config: str = typer.Option(".pymarkdown.json", "--config", "-c"),
):
    """Run Markdown linter."""
    lint_markdown(paths, config)

@app.command()
def fix_newlines(directory: str = "."):
    """Fix trailing newlines in markdown files."""
    fix_markdown_newlines(directory)

@app.command()
def setup_env():
    """Initialize .env file from .env.example."""
    setup_dotenv()

@app.command()
def housekeep():
    """
    Perform a complete housekeeping routine: update system, backup data, check for updates, and prune Docker.
    """
    MaintenanceManager().housekeep()
    
auth_app = typer.Typer(help="User authentication management.")
app.add_typer(auth_app, name="auth")

@auth_app.command()
def add_user(
    username: str = typer.Argument(..., help="The username to add/update."),
    vhost: str = typer.Option(..., "--vhost", "-v", help="The VIRTUAL_HOST to secure (e.g., dashboard.example.com)."),
    password: str = typer.Option(None, "--password", "-p", help="The password for the user (prompted if omitted).")
):
    """Add or update a user for a specific virtual host."""
    from management.security import SecurityManager
    SecurityManager().manage_user(username, vhost, password=password)

@auth_app.command()
def remove_user(
    username: str = typer.Argument(..., help="The username to remove."),
    vhost: str = typer.Option(..., "--vhost", "-v", help="The VIRTUAL_HOST (e.g., dashboard.example.com).")
):
    """Remove a user from a specific virtual host."""
    from management.security import SecurityManager
    SecurityManager().manage_user(username, vhost, remove=True)

if __name__ == "__main__":
    app()
