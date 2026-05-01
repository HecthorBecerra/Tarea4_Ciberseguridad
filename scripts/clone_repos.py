#!/usr/bin/env python
"""Clona repositorios desde URLs individuales o desde organizaciones de GitHub"""

import json
import sys
import logging
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

from subprocess_utils import run_command

console = Console()
_print_lock = threading.Lock()

GITHUB_API = "https://api.github.com"


def _safe_print(*args, **kwargs):
    """Imprime de forma thread-safe."""
    with _print_lock:
        console.print(*args, **kwargs)

console = Console() # Keep console for rich printing
_print_lock = threading.Lock() # Keep lock for thread-safe printing


class RepoCloner:
    def __init__(self, config_path: str = "data/config.json", max_workers: int = 4, explicit_repo_urls: list[str] | None = None):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.repos_dir = Path(self.config.get("repos_dir", "data/repos"))
        self.repos_dir.mkdir(parents=True, exist_ok=True)
        self.clone_options = self.config.get("clone_options", {})
        self.results = []
        self.explicit_repo_urls = explicit_repo_urls

        # Concurrencia
        concurrency = self.config.get("concurrency", {})
        self.parallel_enabled = concurrency.get("enabled", True)
        self.max_workers = max_workers if max_workers is not None else concurrency.get("max_workers", 4)

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

    def _get_org_repos(self, org_name: str, github_token: str | None = None) -> list:
        """Obtiene la lista de repositorios de una organización de GitHub"""
        logger.info(f"Obteniendo repositorios de la organización: {org_name}")

        repos = []
        page = 1
        max_repos = self.clone_options.get("max_repos", 50)
        skip_archived = self.clone_options.get("skip_archived", True)
        skip_forks = self.clone_options.get("skip_forks", True)
        headers = {"Authorization": f"token {github_token}"} if github_token else {}

        while True:
            url = f"{GITHUB_API}/orgs/{org_name}/repos?per_page=100&page={page}&type=public"
            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 403:
                logger.warning("Límite de API de GitHub alcanzado. Usa un token para más requests. Exporta: GITHUB_TOKEN=tu_token")
                break
            elif response.status_code != 200:
                logger.error(f"Error al obtener repos de {org_name}: {response.status_code} - {response.text}")
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

        logger.info(f"  → {len(repos)} repositorios activos encontrados para {org_name}")
        return repos

    def get_top_starred_github_repos(self, org_name: str | None, limit: int, github_token: str | None) -> list[str]:
        """
        Fetches the Git clone URLs of the top N most starred repositories from GitHub.
        Can be global or within a specific organization.
        """
        repo_urls = []
        headers = {"Authorization": f"token {github_token}"} if github_token else {}
        
        query = "stars:>1"
        if org_name:
            query = f"org:{org_name}+{query}"

        logger.info(f"Buscando los {limit} repositorios de GitHub más estrellados (query: '{query}')...")

        page = 1
        per_page = 100 # Max per_page for GitHub Search API

        while len(repo_urls) < limit:
            params = {
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": per_page,
                "page": page
            }
            
            try:
                response = requests.get(GITHUB_SEARCH_API, headers=headers, params=params, timeout=30)
                
                if response.status_code == 403:
                    logger.warning("Límite de API de GitHub alcanzado. Usa un token para más requests. Exporta: GITHUB_TOKEN=tu_token")
                    break
                elif response.status_code != 200:
                    logger.error(f"Error al buscar repositorios de GitHub: {response.status_code} - {response.text}")
                    break
                
                data = response.json()
                items = data.get("items", [])
                
                if not items:
                    break # No more results
                
                for item in items:
                    repo_urls.append(item["clone_url"])
                    if len(repo_urls) >= limit:
                        break
                
                page += 1
            except requests.exceptions.RequestException as e:
                logger.error(f"Error de red al buscar repositorios de GitHub: {e}")
                break
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
            logger.info(f"  Ya existe, actualizando: {repo_name}")
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

        logger.info(f"  Clonando: {repo_name}")
        result = run_command(
            ["git", "clone", "--depth", "1", clone_url, str(dest_path)],
            timeout=300,
        )

        if result.success:
            logger.info(f"  Clonado: {repo_name}")
            return {
                "repo": repo_name,
                "url": clone_url,
                "status": "cloned",
                "path": str(dest_path),
            }
        elif result.error_message and "Timeout" in result.error_message:
            logger.error(f"  Timeout clonando {repo_name}")
            return {"repo": repo_name, "url": clone_url, "status": "timeout"}
        else:
            logger.error(f"  Error al clonar {repo_name}: {result.stderr[:150]}")
            return {
                "repo": repo_name,
                "url": clone_url,
                "status": "error",
                "error": result.error_message or result.stderr[:200],
            }

    def run(self):
        """Ejecuta el proceso de clonación"""
        _safe_print("[bold cyan]═══════════════════════════════════════[/bold cyan]")
        _safe_print("[bold cyan]  CLONADOR DE REPOSITORIOS[/bold cyan]")
        _safe_print("[bold cyan]═══════════════════════════════════════[/bold cyan]")

        all_urls = []

        # 1) Repositorios individuales del config
        individual_repos = self.config.get("repositories", [])
        if individual_repos:
            logger.info(f"{len(individual_repos)} repositorio(s) individual(es) configurado(s)")
            for url in individual_repos:
                all_urls.append({"clone_url": url, "name": None})

        # 2) Repositorios de organizaciones
        organizations = self.config.get("organizations", [])
        if organizations:
            github_token = self.config.get("github_token", None) # Or from config if available
            for org in organizations:
                org_repos = self._get_org_repos(org, github_token=github_token)
                for repo in org_repos:
                    all_urls.append({
                        "clone_url": repo["clone_url"],
                        "name": repo["name"]
                    })

        # If explicit_repo_urls are provided (e.g., from gh-discover command), use them
        if self.explicit_repo_urls:
            all_urls.extend([{"clone_url": url, "name": None} for url in self.explicit_repo_urls])
        elif not all_urls:
            _safe_print("\n[yellow]⚠ No hay repositorios configurados.[/yellow]")
            _safe_print("[yellow]  Edita data/config.json para agregar URLs o nombres de organizaciones.[/yellow]")
            return

        # 3) Clonar todos (en paralelo o secuencial)
        workers = self.max_workers if self.parallel_enabled else 1
        mode = f"paralelo ({workers} workers)" if workers > 1 else "secuencial"
        _safe_print(f"\n[blue]🔄 Clonando {len(all_urls)} repositorio(s) — modo {mode}...[/blue]")

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
                result = self._clone_repo(repo_info["clone_url"], repo_info.get("name"))
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

        cloned = sum(1 for r in self.results if r["status"] in ("cloned", "updated"))
        errors = sum(1 for r in self.results if r["status"] in ("error", "timeout"))
        console.print(f"\n[green]✓ {cloned} exitosos[/green]  [red]✗ {errors} errores[/red]")

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
