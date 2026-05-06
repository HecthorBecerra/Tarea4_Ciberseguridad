#!/usr/bin/env python
"""Genera SBOMs (Software Bill of Materials) usando Syft"""

import json
import threading
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console

from .subprocess_utils import run_command

console = Console()
_print_lock = threading.Lock()


def _safe_print(*args, **kwargs):
    """Imprime de forma thread-safe."""
    with _print_lock:
        console.print(*args, **kwargs)


class SBOMGenerator:
    def __init__(self, repos_dir: str, output_dir: str, max_workers: int = 4):
        self.repos_dir = Path(repos_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.max_workers = max_workers

    def generate_sbom(self, repo_path: Path) -> dict:
        """Genera un SBOM para un repositorio específico"""
        repo_name = repo_path.name

        _safe_print(f"\n[cyan]Generando SBOM para:[/cyan] {repo_name}")

        output_file = self.output_dir / f"{repo_name}-sbom.json"

        cmd = [
            "syft",
            str(repo_path),
            "-o", "json",
            f"--file={output_file}"
        ]

        result = run_command(cmd, timeout=300)

        if result.success:
            _safe_print(f"[green]✓ SBOM generado:[/green] {output_file}")
            return {
                "repo": repo_name,
                "status": "success",
                "output_file": str(output_file),
                "timestamp": datetime.now().isoformat()
            }
        elif result.error_message and "Timeout" in result.error_message:
            _safe_print(
                f"[red]✗ Timeout generando SBOM para {repo_name}[/red]")
            return {"repo": repo_name, "status": "timeout"}
        else:
            error_msg = result.error_message or result.stderr
            _safe_print(f"[red]✗ Error generando SBOM:[/red] {error_msg}")
            return {
                "repo": repo_name,
                "status": "error",
                "error": error_msg
            }

    def run(self):
        """Ejecuta generación de SBOMs para todos los repositorios"""
        _safe_print("[bold cyan]═══════════════════════════════[/bold cyan]")
        _safe_print("[bold cyan]GENERADOR DE SBOMs - Syft[/bold cyan]")
        _safe_print("[bold cyan]═══════════════════════════════[/bold cyan]")

        repos = [d for d in self.repos_dir.iterdir() if d.is_dir()]

        if not repos:
            _safe_print("[yellow]No se encontraron repositorios[/yellow]")
            return

        workers = self.max_workers
        mode = f"paralelo ({workers} workers)" if workers > 1 else "secuencial"
        _safe_print(
            f"\n[blue]📦 Procesando {len(repos)} repositorio(s) — modo {mode}...[/blue]")

        results = []
        if workers > 1:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {
                    executor.submit(self.generate_sbom, repo): repo
                    for repo in repos
                }
                for future in as_completed(futures):
                    results.append(future.result())
        else:
            for repo in repos:
                result = self.generate_sbom(repo)
                results.append(result)

        # Guardar resumen
        summary_file = self.output_dir / "sbom-summary.json"
        with open(summary_file, "w") as f:
            json.dump(results, f, indent=2)

        _safe_print(f"\n[blue]Resumen guardado en:[/blue] {summary_file}")


def main():
    repos_dir = "data/repos"
    output_dir = "data/results"

    generator = SBOMGenerator(repos_dir, output_dir)
    generator.run()


if __name__ == "__main__":
    main()
