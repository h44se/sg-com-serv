import os
import typer
from .runner import CommandRunner

class SecurityManager:
    """Manages service security and authentication."""
    
    def __init__(self, auth_dir: str = "services/caddy/auth"):
        self.auth_dir = os.path.abspath(auth_dir)
        if not os.path.exists(self.auth_dir):
            os.makedirs(self.auth_dir)

    def manage_user(self, username: str, vhost: str, password: str = "", remove: bool = False):
        auth_file = os.path.join(self.auth_dir, f"{vhost}.caddy")
        
        # We'll maintain a dictionary of users for this vhost
        users = {}
        if os.path.exists(auth_file):
            with open(auth_file, "r") as f:
                content = f.read()
                # Parse the Caddy basic_auth block
                # Format:
                # basic_auth {
                #     user hash
                # }
                import re
                matches = re.findall(r"^\s*([^\s#{}]*)\s+([^\s#{}]*)\s*$", content, re.MULTILINE)
                for u, h in matches:
                    if u not in ["basic_auth", "{", "}", ""]:
                        users[u] = h

        if remove:
            if username in users:
                typer.echo(f"Removing user {username} from {vhost}...")
                del users[username]
            else:
                typer.secho(f"Error: User {username} not found for {vhost}", fg=typer.colors.RED)
                return
        else:
            if not password:
                password = typer.prompt(f"Enter password for {username}", hide_input=True, confirmation_prompt=True)
            
            typer.echo(f"Adding/Updating user {username} for {vhost}...")
            # Use htpasswd to generate the bcrypt hash
            # -n for stdout, -b for password in args, -B for bcrypt
            res = CommandRunner.run(f"htpasswd -nbB {username} {password}", capture=True)
            # htpasswd output is 'user:hash'
            if ":" in res:
                _, hashed_pwd = res.split(":", 1)
                users[username] = hashed_pwd.strip()
            else:
                typer.secho("Error generating hash with htpasswd", fg=typer.colors.RED)
                return

        # Write back to the .caddy file
        if users:
            new_content = "basic_auth {\n"
            for u, h in users.items():
                new_content += f"    {u} {h}\n"
            new_content += "}\n"
            with open(auth_file, "w") as f:
                f.write(new_content)
        else:
            # If no users left, remove the file or keep it empty
            if os.path.exists(auth_file):
                os.remove(auth_file)
            # Create an empty file so Caddy's import doesn't fail
            open(auth_file, 'a').close()
            
        typer.secho("\n✅ Done! Reload Caddy to apply changes:", fg=typer.colors.GREEN, bold=True)
        typer.echo("docker exec caddy caddy reload --config /etc/caddy/Caddyfile")
