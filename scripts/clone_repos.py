#!/usr/bin/env python
"""Clona repositorios desde URLs individuales o desde organizaciones de GitHub"""

import json
import sys
import threading
from pathlib import Path
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.table import Table

try:
    import requests
except ImportError:
    print("Error: 'requests' no está instalado. Ejecuta: uv sync")
    sys.exit(1)

from .subprocess_utils import run_command

console = Console()
_print_lock = threading.Lock()

GITHUB_API = "https://api.github.com"


def _safe_print(*args, **kwargs):
    """Imprime de forma thread-safe."""
    with _print_lock:
        console.print(*args, **kwargs)


class RepoCloner:
    def __init__(self, config_path: str = "data/config.json", max_workers: int = 4):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.repos_dir = Path(self.config.get("repos_dir", "data/repos"))
        self.repos_dir.mkdir(parents=True, exist_ok=True)
        self.clone_options = self.config.get("clone_options", {})
        self.results = []

        # Concurrencia
        concurrency = self.config.get("concurrency", {})
        self.parallel_enabled = concurrency.get("enabled", True)
        self.max_workers = max_workers or concurrency.get("max_workers", 4)

    def _load_config(self) -> dict:
        """Carga la configuración desde config.json"""
        if not self.config_path.exists():
            _safe_print(f"[red]✗ No se encontró {self.config_path}[/red]")
            sys.exit(1)
        with open(self.config_path) as f:
            return json.load(f)

    def _is_recently_active(self, pushed_at: str) -> bool:
        """Verifica si un repositorio tuvo actividad reciente"""
        max_days = self.clone_options.get("max_inactive_days", 30)
        if not pushed_at:
            return False
        pushed_date = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
        cutoff = datetime.now(timezone.utc) - timedelta(days=max_days)
        return pushed_date >= cutoff

    def _get_org_repos(self, org_name: str) -> list:
        """Obtiene la lista de repositorios de una organización de GitHub"""
        _safe_print(
            f"\n[cyan]Obteniendo repositorios de la organización:[/cyan] {org_name}")

        repos = []
        page = 1
        max_repos = self.clone_options.get("max_repos", 50)
        skip_archived = self.clone_options.get("skip_archived", True)
        skip_forks = self.clone_options.get("skip_forks", True)

        while True:
            url = f"{GITHUB_API}/orgs/{org_name}/repos?per_page=100&page={page}&type=public"
            response = requests.get(url, timeout=30)

            if response.status_code == 403:
                _safe_print(
                    "[yellow]⚠ Límite de API de GitHub alcanzado. Usa un token para más requests.[/yellow]")
                _safe_print(
                    "[yellow]  Exporta: GITHUB_TOKEN=tu_token[/yellow]")
                break
            elif response.status_code != 200:
                _safe_print(
                    f"[red]✗ Error al obtener repos de {org_name}: {response.status_code}[/red]")
                break

            page_repos = response.json()
            if not page_repos:
                break

            for repo in page_repos:
                # Filtrar archivados
                if skip_archived and repo.get("archived", False):
                    continue

                # Filtrar forks
                if skip_forks and repo.get("fork", False):
                    continue

                # Filtrar por actividad reciente
                if not self._is_recently_active(repo.get("pushed_at")):
                    continue

                repos.append({
                    "name": repo["name"],
                    "clone_url": repo["clone_url"],
                    "html_url": repo["html_url"],
                    "pushed_at": repo.get("pushed_at", ""),
                    "language": repo.get("language", "N/A"),
                    "size_kb": repo.get("size", 0),
                })

                if len(repos) >= max_repos:
                    break

            if len(repos) >= max_repos:
                break

            page += 1

        _safe_print(
            f"[green]  → {len(repos)} repositorios activos encontrados[/green]")
        return repos

    def _clone_repo(self, clone_url: str, repo_name: str = None) -> dict:
        """Clona un repositorio individual"""
        if not repo_name:
            # Extraer nombre del URL
            repo_name = clone_url.rstrip("/").split("/")[-1]
            if repo_name.endswith(".git"):
                repo_name = repo_name[:-4]

        dest_path = self.repos_dir / repo_name

        if dest_path.exists():
            _safe_print(
                f"  [yellow]⟳ Ya existe, actualizando:[/yellow] {repo_name}")
            result = run_command(
                ["git", "-C", str(dest_path), "pull", "--ff-only"],
                timeout=120,
            )
            status = "updated" if result.success else "update_failed"
            return {
                "repo": repo_name,
                "url": clone_url,
                "status": status,
                "path": str(dest_path),
            }

        _safe_print(f"  [cyan]↓ Clonando:[/cyan] {repo_name}")
        result = run_command(
            ["git", "clone", "--depth", "1", clone_url, str(dest_path)],
            timeout=300,
        )

        if result.success:
            _safe_print(f"  [green]✓ Clonado:[/green] {repo_name}")
            return {
                "repo": repo_name,
                "url": clone_url,
                "status": "cloned",
                "path": str(dest_path),
            }
        elif result.error_message and "Timeout" in result.error_message:
            _safe_print(f"  [red]✗ Timeout clonando {repo_name}[/red]")
            return {"repo": repo_name, "url": clone_url, "status": "timeout"}
        else:
            _safe_print(f"  [red]✗ Error:[/red] {result.stderr[:150]}")
            return {
                "repo": repo_name,
                "url": clone_url,
                "status": "error",
                "error": result.error_message or result.stderr[:200],
            }

    def run(self):
        """Ejecuta el proceso de clonación"""
        _safe_print(
            "[bold cyan]═══════════════════════════════════════[/bold cyan]")
        _safe_print("[bold cyan]  CLONADOR DE REPOSITORIOS[/bold cyan]")
        _safe_print(
            "[bold cyan]═══════════════════════════════════════[/bold cyan]")

        all_urls = []

        # 1) Repositorios individuales del config
        individual_repos = self.config.get("repositories", [])
        if individual_repos:
            _safe_print(
                f"\n[blue]📋 {len(individual_repos)} repositorio(s) individual(es) configurado(s)[/blue]")
            for url in individual_repos:
                all_urls.append({"clone_url": url, "name": None})

        # 2) Repositorios de organizaciones
        organizations = self.config.get("organizations", [])
        if organizations:
            for org in organizations:
                org_repos = self._get_org_repos(org)
                for repo in org_repos:
                    all_urls.append({
                        "clone_url": repo["clone_url"],
                        "name": repo["name"]
                    })

        if not all_urls:
            _safe_print(
                "\n[yellow]⚠ No hay repositorios configurados.[/yellow]")
            _safe_print(
                "[yellow]  Edita data/config.json para agregar URLs o nombres de organizaciones.[/yellow]")
            return

        # 3) Clonar todos (en paralelo o secuencial)
        workers = self.max_workers if self.parallel_enabled else 1
        mode = f"paralelo ({workers} workers)" if workers > 1 else "secuencial"
        _safe_print(
            f"\n[blue]🔄 Clonando {len(all_urls)} repositorio(s) — modo {mode}...[/blue]")

        if workers > 1:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {
                    executor.submit(self._clone_repo, info["clone_url"], info.get("name")): info
                    for info in all_urls
                }
                for future in as_completed(futures):
                    self.results.append(future.result())
        else:
            for repo_info in all_urls:
                result = self._clone_repo(
                    repo_info["clone_url"], repo_info.get("name"))
                self.results.append(result)

        # 4) Mostrar resumen
        self._print_summary()

        # 5) Guardar log
        self._save_log()

    def _print_summary(self):
        """Muestra tabla resumen"""
        table = Table(title="\nResumen de Clonación")
        table.add_column("Repositorio", style="cyan")
        table.add_column("Estado", style="green")
        table.add_column("Ruta", style="dim")

        status_icons = {
            "cloned": "[green]✓ Clonado[/green]",
            "updated": "[blue]⟳ Actualizado[/blue]",
            "update_failed": "[yellow]! Act. fallida[/yellow]",
            "error": "[red]✗ Error[/red]",
            "timeout": "[red]⏱ Timeout[/red]",
        }

        for r in self.results:
            table.add_row(
                r["repo"],
                status_icons.get(r["status"], r["status"]),
                r.get("path", "N/A")
            )

        console.print(table)

        cloned = sum(1 for r in self.results if r["status"] in (
            "cloned", "updated"))
        errors = sum(1 for r in self.results if r["status"] in (
            "error", "timeout"))
        console.print(
            f"\n[green]✓ {cloned} exitosos[/green]  [red]✗ {errors} errores[/red]")

    def _save_log(self):
        """Guarda log de clonación"""
        output_dir = Path(self.config.get("output_dir", "data/results"))
        output_dir.mkdir(parents=True, exist_ok=True)
        log_file = output_dir / "clone-log.json"
        with open(log_file, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "total": len(self.results),
                "results": self.results
            }, f, indent=2)
        console.print(f"[blue]📄 Log guardado en:[/blue] {log_file}")


def main():
    config_path = "data/config.json"
    if len(sys.argv) > 1:
        config_path = sys.argv[1]

    cloner = RepoCloner(config_path)
    cloner.run()


if __name__ == "__main__":
    main()
