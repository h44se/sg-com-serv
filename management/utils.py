import os
import subprocess
import typer

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
