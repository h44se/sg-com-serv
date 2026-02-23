import typer
from .runner import CommandRunner

class DockerManager:
    """Manages docker-compose services."""
    
    def deploy(self, service: str = ""):
        if service:
            typer.echo(f"Bringing up service: {service}...")
            CommandRunner.run(f"docker compose up -d {service}")
        else:
            typer.echo("Bringing up all docker-compose services...")
            CommandRunner.run("docker compose up -d")

    def stop(self):
        typer.echo("Stopping docker-compose services...")
        CommandRunner.run("docker compose down")

    def pull(self):
        typer.echo("Pulling latest images...")
        CommandRunner.run("docker compose pull")

    def rebuild(self):
        typer.echo("Rebuilding and restarting services...")
        CommandRunner.run("docker compose up -d --build --force-recreate")

    def status(self):
        CommandRunner.run("docker compose ps")

    def logs(self, service: str = "", follow: bool = True, tail: int = 100):
        cmd = f"docker compose logs"
        if follow:
            cmd += " -f"
        if tail > 0:
            cmd += f" --tail {tail}"
        if service:
            cmd += f" {service}"
        CommandRunner.run(cmd)

    def check_updates(self):
        typer.echo("Checking for available container updates (this may take a moment)...")
        # Run watchtower in run-once, monitor-only mode
        cmd = "docker run --rm -v /var/run/docker.sock:/var/run/docker.sock containrrr/watchtower --run-once --monitor-only"
        CommandRunner.run(cmd)

    def test(self):
        typer.echo("Validating docker-compose configuration (dry-run)...")
        CommandRunner.run("docker compose up --dry-run")
