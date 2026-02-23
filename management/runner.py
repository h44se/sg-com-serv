import subprocess
import typer

class CommandRunner:
    @staticmethod
    def run(cmd: str, check: bool = True, capture: bool = False):
        typer.echo(f"Executing: {cmd}")
        result = subprocess.run(cmd, shell=True, check=check, capture_output=capture, text=True)
        return result.stdout if capture else result
