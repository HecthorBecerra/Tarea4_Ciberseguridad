#!/usr/bin/env python
"""Utilidades centralizadas para ejecución de subprocesos.

Provee una función `run_command()` y un dataclass `CommandResult`
que eliminan la repetición de manejo de excepciones en todos los scripts.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class CommandResult:
    """Resultado inmutable de la ejecución de un comando externo."""
    returncode: int
    stdout: str
    stderr: str
    success: bool
    error_message: str | None = field(default=None)

    @property
    def failed(self) -> bool:
        return not self.success


def run_command(
    cmd: list[str],
    *,
    timeout: int = 300,
    cwd: str | None = None,
) -> CommandResult:
    """Ejecuta un comando externo con manejo robusto de errores.

    Args:
        cmd: Lista de argumentos del comando (e.g. ["git", "clone", ...]).
        timeout: Tiempo máximo de ejecución en segundos.
        cwd: Directorio de trabajo para el comando.

    Returns:
        CommandResult con returncode, stdout, stderr, success y error_message.
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )
        return CommandResult(
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            success=(result.returncode == 0),
        )

    except subprocess.TimeoutExpired:
        return CommandResult(
            returncode=-1,
            stdout="",
            stderr="",
            success=False,
            error_message=f"Timeout después de {timeout}s ejecutando: {' '.join(cmd[:3])}...",
        )

    except FileNotFoundError:
        tool_name = cmd[0] if cmd else "unknown"
        return CommandResult(
            returncode=-1,
            stdout="",
            stderr="",
            success=False,
            error_message=f"Herramienta no encontrada: '{tool_name}'. ¿Está instalada y en PATH?",
        )

    except OSError as exc:
        return CommandResult(
            returncode=-1,
            stdout="",
            stderr="",
            success=False,
            error_message=f"Error del sistema ejecutando comando: {exc}",
        )
