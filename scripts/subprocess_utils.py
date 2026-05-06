import subprocess
from collections import namedtuple

CommandResult = namedtuple(
    "CommandResult", ["success", "stdout", "stderr", "error_message"])


def run_command(cmd: list[str], timeout: int = 600) -> CommandResult:
    """Ejecuta un comando y captura su salida y errores."""
    try:
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout
        )
        return CommandResult(True, process.stdout, process.stderr, None)
    except subprocess.CalledProcessError as e:
        return CommandResult(False, e.stdout, e.stderr, f"Command failed with exit code {e.returncode}: {e.stderr}")
    except subprocess.TimeoutExpired:
        return CommandResult(False, None, None, f"Timeout: Command exceeded {timeout} seconds.")
    except FileNotFoundError:
        return CommandResult(False, None, None, f"Command not found: {cmd[0]}")
    except Exception as e:
        return CommandResult(False, None, None, f"An unexpected error occurred: {e}")
