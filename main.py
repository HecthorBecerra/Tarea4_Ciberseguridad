#!/usr/bin/env python
"""Script principal para ejecutar todos los análisis"""

import click
import json
from scripts.generate_sboms import SBOMGenerator
from scripts.generate_grype import GrypeScanner
from scripts.generate_codeql import CodeQLAnalyzer
from scripts.clone_repos import RepoCloner
from scripts.analyzer import VulnerabilityAnalyzer
from scripts.generate_reports import ReportGenerator
import sys
from pathlib import Path

# Important: Add scripts directory to path BEFORE importing local modules
sys.path.insert(0, str(Path(__file__).parent / "scripts"))


def _load_max_workers(config_path: str, workers_override: int | None) -> int:
    """Carga max_workers desde config o usa el override del CLI."""
    if workers_override is not None:
        return workers_override
    try:
        with open(config_path) as f:
            config = json.load(f)
        concurrency = config.get("concurrency", {})
        if not concurrency.get("enabled", True):
            return 1
        return concurrency.get("max_workers", 4)
    except (FileNotFoundError, json.JSONDecodeError):
        return 4


@click.group()
def cli():
    """🔒 Herramienta de análisis de seguridad

    Flujo recomendado:

    \b
      1. Configura repos en data/config.json
      2. uv run python main.py clone
      3. uv run python main.py sbom
      4. uv run python main.py grype
      5. uv run python main.py codeql
      6. uv run python main.py report
    \b
    O ejecuta todo de una vez:
      uv run python main.py all
    """
    pass


@cli.command()
@click.option("--config", default="data/config.json", help="Ruta al archivo de configuración")
@click.option("--workers", default=None, type=int, help="Número de workers paralelos (override config)")
def clone(config, workers):
    """📥 Clonar repositorios desde config.json"""
    max_workers = _load_max_workers(config, workers)
    cloner = RepoCloner(config, max_workers=max_workers)
    cloner.run()


@cli.command()
@click.option("--repos-dir", default="data/repos", help="Directorio con repositorios")
@click.option("--output-dir", default="data/results", help="Directorio de salida")
@click.option("--workers", default=None, type=int, help="Número de workers paralelos (override config)")
def sbom(repos_dir, output_dir, workers):
    """📦 Generar SBOMs con Syft"""
    max_workers = _load_max_workers("data/config.json", workers)
    generator = SBOMGenerator(repos_dir, output_dir, max_workers=max_workers)
    generator.run()


@cli.command()
@click.option("--repos-dir", default="data/repos", help="Directorio con repositorios")
@click.option("--output-dir", default="data/results", help="Directorio de salida")
@click.option("--workers", default=None, type=int, help="Número de workers paralelos (override config)")
def grype(repos_dir, output_dir, workers):
    """🔓 Escanear vulnerabilidades con Grype"""
    max_workers = _load_max_workers("data/config.json", workers)
    scanner = GrypeScanner(repos_dir, output_dir, max_workers=max_workers)
    scanner.run()


@cli.command()
@click.option("--repos-dir", default="data/repos", help="Directorio con repositorios")
@click.option("--output-dir", default="data/results", help="Directorio de salida")
@click.option("--workers", default=None, type=int, help="Número de workers paralelos (override config)")
def codeql(repos_dir, output_dir, workers):
    """🔍 Analizar código con CodeQL"""
    max_workers = _load_max_workers("data/config.json", workers)
    analyzer = CodeQLAnalyzer(repos_dir, output_dir, max_workers=max_workers)
    analyzer.run()


@cli.command()
@click.option("--output-dir", default="data/results", help="Directorio de resultados")
def report(output_dir):
    """📊 Generar reporte consolidado"""
    generator = ReportGenerator(output_dir)
    generator.generate_report()


@cli.command()
@click.option("--output-dir", default="data/results", help="Directorio con JSONs del miner")
def analyze(output_dir):
    """🧠 Ejecutar el Analyzer sistemático para caracterizar vulnerabilidades"""
    logic_analyzer = VulnerabilityAnalyzer(output_dir)
    logic_analyzer.run()


@cli.command(name="all")
@click.option("--config", default="data/config.json", help="Ruta al archivo de configuración")
@click.option("--repos-dir", default="data/repos", help="Directorio con repositorios")
@click.option("--output-dir", default="data/results", help="Directorio de salida")
@click.option("--workers", default=None, type=int, help="Número de workers paralelos (override config)")
def run_all(config, repos_dir, output_dir, workers):
    """🚀 Ejecutar pipeline completo (clone → sbom → grype → codeql → report)"""
    max_workers = _load_max_workers(config, workers)

    click.echo(f"\n[Pipeline] Workers configurados: {max_workers}")

    click.echo("\n[1/5] 📥 Clonando repositorios...")
    cloner = RepoCloner(config, max_workers=max_workers)
    cloner.run()

    click.echo("\n[2/5] 📦 Generando SBOMs...")
    generator = SBOMGenerator(repos_dir, output_dir, max_workers=max_workers)
    generator.run()

    click.echo("\n[3/5] 🔓 Escaneando vulnerabilidades...")
    scanner = GrypeScanner(repos_dir, output_dir, max_workers=max_workers)
    scanner.run()

    click.echo("\n[4/5] 🔍 Analizando código...")
    analyzer = CodeQLAnalyzer(repos_dir, output_dir, max_workers=max_workers)
    analyzer.run()

    click.echo("\n[4.5/5] 🧠 Caracterizando vulnerabilidades (Analyzer)...")
    logic_analyzer = VulnerabilityAnalyzer(output_dir)
    logic_analyzer.run()

    click.echo("\n[5/5] 📊 Generando reporte...")
    report_gen = ReportGenerator(output_dir)
    report_gen.generate_report()

    click.echo("\n✅ Pipeline completo ejecutado con éxito.")
    click.echo(f"   Resultados en: {output_dir}/")


@cli.command(name="stream")
@click.option("--config", default="data/config.json", help="Ruta al archivo de configuración")
@click.option("--repos-dir", default="data/repos", help="Directorio con repositorios")
@click.option("--output-dir", default="data/results", help="Directorio de salida")
def stream(config, repos_dir, output_dir):
    """🌊 Ejecutar pipeline End-to-End por repositorio (Actualiza Visualizer en tiempo real)"""
    from rich.console import Console
    from scripts.subprocess_utils import run_command
    console = Console()

    console.print(
        "\n[bold cyan]🌊 INICIANDO MODO STREAM (Cascada por Repositorio)[/bold cyan]")
    console.print(
        "Este modo clona, escanea y actualiza el Visualizer uno por uno.\n")

    cloner = RepoCloner(config, max_workers=1)
    sbom_gen = SBOMGenerator(repos_dir, output_dir, max_workers=1)
    grype_scan = GrypeScanner(repos_dir, output_dir, max_workers=1)
    codeql_analyzer = CodeQLAnalyzer(repos_dir, output_dir, max_workers=1)
    logic_analyzer = VulnerabilityAnalyzer(output_dir)

    # 1. Obtener URLs
    all_urls = []
    individual_repos = cloner.config.get("repositories", [])
    for url in individual_repos:
        all_urls.append({"clone_url": url, "name": None})

    for org in cloner.config.get("organizations", []):
        org_repos = cloner._get_org_repos(org)
        for repo in org_repos:
            all_urls.append(
                {"clone_url": repo["clone_url"], "name": repo["name"]})

    if not all_urls:
        console.print(
            "[yellow]⚠ No hay repositorios configurados en config.json.[/yellow]")
        return

    console.print(
        f"[bold blue]📋 Total a procesar: {len(all_urls)} repositorios[/bold blue]")

    # Actualizar BD de Grype al inicio para no repetirlo en cada repo
    console.print(
        "\n[yellow]Actualizando base de datos de Grype antes de empezar...[/yellow]")
    run_command(["grype", "db", "update"], timeout=120)

    # 2. Procesar uno a uno
    for idx, item in enumerate(all_urls, 1):
        repo_id = item.get("name") or item["clone_url"].rstrip(
            "/").split("/")[-1]
        if repo_id.endswith(".git"):
            repo_id = repo_id[:-4]

        console.print(
            f"\n[bold magenta]► [{idx}/{len(all_urls)}] PROCESANDO REPOSITORIO: {repo_id}[/bold magenta]")
        console.print(
            "[bold magenta]──────────────────────────────────────────────────[/bold magenta]")

        # Paso 1: Clonar
        result = cloner._clone_repo(item["clone_url"], item.get("name"))
        if result["status"] in ["cloned", "updated"] and "path" in result:
            repo_path = Path(result["path"])

            # Paso 2, 3 y 4: SBOM, Grype y CodeQL para ESTE repo en particular
            sbom_gen.generate_sbom(repo_path)
            grype_scan.scan_repo(repo_path)
            codeql_analyzer.analyze_repo(repo_path)

            # Paso 5: Analyzer (Re-escribe el data.json inyectando este nuevo repo)
            console.print(
                "\n[bold green]🔄 Actualizando Dashboard (Visualizer)...[/bold green]")
            logic_analyzer.run()
        else:
            console.print(
                f"[red]✗ Error al clonar/actualizar {repo_id}, saltando análisis.[/red]")

    console.print(
        "\n[bold green]🌊 ✅ MODO STREAM FINALIZADO CON ÉXITO.[/bold green]")


if __name__ == "__main__":
    cli()
