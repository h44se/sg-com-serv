import os
import typer
from .runner import CommandRunner

class SecurityManager:
    """Manages service security and authentication."""
    
    def __init__(self, htpasswd_dir: str = "nginx/htpasswd"):
        self.htpasswd_dir = os.path.abspath(htpasswd_dir)
        if not os.path.exists(self.htpasswd_dir):
            os.makedirs(self.htpasswd_dir)

    def manage_user(self, username: str, vhost: str, password: str = "", remove: bool = False):
        htpasswd_file = os.path.join(self.htpasswd_dir, vhost)

        if remove:
            if not os.path.exists(htpasswd_file):
                typer.secho(f"Error: No auth file found for {vhost} at {htpasswd_file}", fg=typer.colors.RED)
                return
            typer.echo(f"Removing user {username} from {vhost}...")
            CommandRunner.run(f"htpasswd -D {htpasswd_file} {username}")
        else:
            if not password:
                password = typer.prompt(f"Enter password for {username}", hide_input=True, confirmation_prompt=True)
            
            typer.echo(f"Adding/Updating user {username} for {vhost}...")
            # -b for batch, -B for bcrypt, -c to create
            flags = "-bB"
            if not os.path.exists(htpasswd_file):
                flags += "c"
            
            CommandRunner.run(f"htpasswd {flags} {htpasswd_file} {username} {password}")
            
        typer.secho("\n✅ Done! Remember to rebuild the proxy to apply changes:", fg=typer.colors.GREEN, bold=True)
        typer.echo("uv run tools.py docker rebuild")
