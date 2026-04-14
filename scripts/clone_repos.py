#!/usr/bin/env python
"""Clona repositorios desde URLs individuales o desde organizaciones de GitHub"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from rich.console import Console
from rich.table import Table

try:
    import requests
except ImportError:
    print("Error: 'requests' no está instalado. Ejecuta: uv sync")
    sys.exit(1)

console = Console()

GITHUB_API = "https://api.github.com"


class RepoCloner:
    def __init__(self, config_path: str = "data/config.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.repos_dir = Path(self.config.get("repos_dir", "data/repos"))
        self.repos_dir.mkdir(parents=True, exist_ok=True)
        self.clone_options = self.config.get("clone_options", {})
        self.results = []

    def _load_config(self) -> dict:
        """Carga la configuración desde config.json"""
        if not self.config_path.exists():
            console.print(f"[red]✗ No se encontró {self.config_path}[/red]")
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
        console.print(f"\n[cyan]Obteniendo repositorios de la organización:[/cyan] {org_name}")

        repos = []
        page = 1
        max_repos = self.clone_options.get("max_repos", 50)
        skip_archived = self.clone_options.get("skip_archived", True)
        skip_forks = self.clone_options.get("skip_forks", True)

        while True:
            url = f"{GITHUB_API}/orgs/{org_name}/repos?per_page=100&page={page}&type=public"
            response = requests.get(url, timeout=30)

            if response.status_code == 403:
                console.print("[yellow]⚠ Límite de API de GitHub alcanzado. Usa un token para más requests.[/yellow]")
                console.print("[yellow]  Exporta: GITHUB_TOKEN=tu_token[/yellow]")
                break
            elif response.status_code != 200:
                console.print(f"[red]✗ Error al obtener repos de {org_name}: {response.status_code}[/red]")
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

        console.print(f"[green]  → {len(repos)} repositorios activos encontrados[/green]")
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
            console.print(f"  [yellow]⟳ Ya existe, actualizando:[/yellow] {repo_name}")
            try:
                result = subprocess.run(
                    ["git", "-C", str(dest_path), "pull", "--ff-only"],
                    capture_output=True, text=True, timeout=120
                )
                status = "updated" if result.returncode == 0 else "update_failed"
            except Exception as e:
                status = "update_failed"
            return {
                "repo": repo_name,
                "url": clone_url,
                "status": status,
                "path": str(dest_path)
            }

        console.print(f"  [cyan]↓ Clonando:[/cyan] {repo_name}")
        try:
            result = subprocess.run(
                ["git", "clone", "--depth", "1", clone_url, str(dest_path)],
                capture_output=True, text=True, timeout=300
            )

            if result.returncode == 0:
                console.print(f"  [green]✓ Clonado:[/green] {repo_name}")
                return {
                    "repo": repo_name,
                    "url": clone_url,
                    "status": "cloned",
                    "path": str(dest_path)
                }
            else:
                console.print(f"  [red]✗ Error:[/red] {result.stderr[:150]}")
                return {
                    "repo": repo_name,
                    "url": clone_url,
                    "status": "error",
                    "error": result.stderr[:200]
                }

        except subprocess.TimeoutExpired:
            console.print(f"  [red]✗ Timeout clonando {repo_name}[/red]")
            return {"repo": repo_name, "url": clone_url, "status": "timeout"}
        except Exception as e:
            return {"repo": repo_name, "url": clone_url, "status": "error", "error": str(e)}

    def run(self):
        """Ejecuta el proceso de clonación"""
        console.print("[bold cyan]═══════════════════════════════════════[/bold cyan]")
        console.print("[bold cyan]  CLONADOR DE REPOSITORIOS[/bold cyan]")
        console.print("[bold cyan]═══════════════════════════════════════[/bold cyan]")

        all_urls = []

        # 1) Repositorios individuales del config
        individual_repos = self.config.get("repositories", [])
        if individual_repos:
            console.print(f"\n[blue]📋 {len(individual_repos)} repositorio(s) individual(es) configurado(s)[/blue]")
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
            console.print("\n[yellow]⚠ No hay repositorios configurados.[/yellow]")
            console.print("[yellow]  Edita data/config.json para agregar URLs o nombres de organizaciones.[/yellow]")
            return

        # 3) Clonar todos
        console.print(f"\n[blue]🔄 Clonando {len(all_urls)} repositorio(s)...[/blue]")

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
