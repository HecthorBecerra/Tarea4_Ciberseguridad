#!/usr/bin/env python
"""Escanea vulnerabilidades usando Grype"""

import json
import threading
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.table import Table

from .subprocess_utils import run_command

console = Console()
_print_lock = threading.Lock()


def _safe_print(*args, **kwargs):
    """Imprime de forma thread-safe."""
    with _print_lock:
        console.print(*args, **kwargs)


class GrypeScanner:
    def __init__(self, repos_dir: str, output_dir: str, max_workers: int = 4):
        self.repos_dir = Path(repos_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.max_workers = max_workers

    def scan_repo(self, repo_path: Path) -> dict:
        """Escanea un repositorio en busca de vulnerabilidades"""
        repo_name = repo_path.name

        _safe_print(f"\n[cyan]Escaneando vulnerabilidades:[/cyan] {repo_name}")

        output_file = self.output_dir / f"{repo_name}-grype.json"

        sbom_file = self.output_dir / f"{repo_name}-sbom.json"
        if sbom_file.exists():
            scan_target = f"sbom:{sbom_file}"
            _safe_print(f"[dim]  → usando SBOM: {sbom_file.name}[/dim]")
        else:
            scan_target = str(repo_path)
            _safe_print(
                f"[yellow]  → SBOM no encontrado, escaneando directorio[/yellow]")

        cmd = [
            "grype",
            scan_target,
            "-o", "json",
            f"--file={output_file}"
        ]

        result = run_command(cmd, timeout=600)

        if result.success or "Found:" in result.stdout:
            # Leer el archivo de salida para obtener estadísticas
            if output_file.exists():
                try:
                    with open(output_file) as f:
                        data = json.load(f)
                        vuln_count = len(data.get("matches", []))
                except (json.JSONDecodeError, IOError):
                    vuln_count = 0

                _safe_print(
                    f"[green]✓ Escaneo completado:[/green] {vuln_count} vulnerabilidades encontradas")

                return {
                    "repo": repo_name,
                    "status": "success",
                    "vulnerabilities": vuln_count,
                    "output_file": str(output_file),
                    "timestamp": datetime.now().isoformat()
                }
        elif result.error_message and "Timeout" in result.error_message:
            _safe_print(f"[red]✗ Timeout escaneando {repo_name}[/red]")
            return {"repo": repo_name, "status": "timeout"}

        _safe_print(
            f"[yellow]! Escaneo completado sin vulnerabilidades[/yellow]")
        return {
            "repo": repo_name,
            "status": "success",
            "vulnerabilities": 0,
            "output_file": str(output_file),
        }

    def run(self):
        """Ejecuta escaneo para todos los repositorios"""
        _safe_print("[bold cyan]═══════════════════════════════[/bold cyan]")
        _safe_print(
            "[bold cyan]ESCANER DE VULNERABILIDADES - Grype[/bold cyan]")
        _safe_print("[bold cyan]═══════════════════════════════[/bold cyan]")

        # Actualizar base de datos (SIEMPRE secuencial, antes de cualquier escaneo)
        _safe_print(
            "\n[yellow]Actualizando base de datos de Grype...[/yellow]")
        run_command(["grype", "db", "update"], timeout=120)

        repos = [d for d in self.repos_dir.iterdir() if d.is_dir()]

        if not repos:
            _safe_print("[yellow]No se encontraron repositorios[/yellow]")
            return

        workers = self.max_workers
        mode = f"paralelo ({workers} workers)" if workers > 1 else "secuencial"
        _safe_print(
            f"\n[blue]🔓 Escaneando {len(repos)} repositorio(s) — modo {mode}...[/blue]")

        results = []
        if workers > 1:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {
                    executor.submit(self.scan_repo, repo): repo
                    for repo in repos
                }
                for future in as_completed(futures):
                    results.append(future.result())
        else:
            for repo in repos:
                result = self.scan_repo(repo)
                results.append(result)

        # Mostrar tabla resumen
        table = Table(title="Resumen de Escaneo")
        table.add_column("Repositorio", style="cyan")
        table.add_column("Vulnerabilidades", style="magenta")
        table.add_column("Estado", style="green")

        for result in results:
            vuln = result.get("vulnerabilities", "N/A")
            status = result.get("status", "unknown")
            table.add_row(result["repo"], str(vuln), status)

        console.print(table)

        # Guardar resumen
        summary_file = self.output_dir / "grype-summary.json"
        with open(summary_file, "w") as f:
            json.dump(results, f, indent=2)

        _safe_print(f"\n[blue]Resumen guardado en:[/blue] {summary_file}")


def main():
    repos_dir = "data/repos"
    output_dir = "data/results"

    scanner = GrypeScanner(repos_dir, output_dir)
    scanner.run()


if __name__ == "__main__":
    main()
