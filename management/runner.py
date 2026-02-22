import subprocess
import typer

class CommandRunner:
    @staticmethod
    def run(cmd: str, check: bool = True):
        typer.echo(f"Executing: {cmd}")
        return subprocess.run(cmd, shell=True, check=check)
