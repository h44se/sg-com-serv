import os
import subprocess
import typer


def load_dotenv(path: str = ".env", override: bool = False):
    """Load key/value pairs from a dotenv file into os.environ.

    Existing environment variables are preserved unless override=True.
    """
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

            if not key:
                continue

            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"\"", "'"}:
                value = value[1:-1]

            if override or key not in os.environ:
                os.environ[key] = value

def lint_markdown(paths, config):
    """Run Markdown linter."""
    typer.echo(f"Linting: {', '.join(paths)}")
    cmd = ["pymarkdown", "-c", config, "scan"] + paths
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)

def fix_markdown_newlines(directory):
    """Fix trailing newlines in markdown files."""
    for root, _, files in os.walk(directory):
        if any(s in root for s in [".venv", ".git"]): continue
        for f in files:
            if f.endswith(".md"):
                p = os.path.join(root, f)
                with open(p, "r") as file: content = file.read()
                if not content.endswith("\n"):
                    with open(p, "a") as file: file.write("\n")
                    typer.echo(f"Fixed {p}")

def setup_dotenv():
    """Initialize .env file from .env.example with user prompts."""
    if os.path.exists(".env"):
        overwrite = typer.confirm(".env file already exists. Do you want to overwrite it?", default=False)
        if not overwrite:
            return

    if not os.path.exists(".env.example"):
        typer.secho("Error: .env.example not found.", fg=typer.colors.RED)
        return

    typer.secho("\n🔧 Environment Configuration", fg=typer.colors.CYAN, bold=True)
    typer.echo("Leave blank to use the default value shown in brackets.\n")
    
    env_content = []
    with open(".env.example", "r") as f:
        lines = f.readlines()

    for line in lines:
        original_line = line.rstrip()
        stripped = original_line.strip()
        
        # Keep comments and empty lines
        if not stripped or stripped.startswith("#"):
            env_content.append(original_line)
            continue
        
        if "=" in stripped:
            key, default_value = stripped.split("=", 1)
            # Use typer.prompt to get user input
            user_value = typer.prompt(f"  {key}", default=default_value, show_default=True)
            env_content.append(f"{key}={user_value}")
        else:
            env_content.append(original_line)

    with open(".env", "w") as f:
        f.write("\n".join(env_content) + "\n")
    
    typer.echo("")
    typer.secho("✅ Successfully created .env file!", fg=typer.colors.GREEN, bold=True)
