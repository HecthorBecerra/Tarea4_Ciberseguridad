#!/usr/bin/env python
"""Script principal para ejecutar todos los análisis"""

import json
import sys
import click
from pathlib import Path

# Agregar scripts al path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from generate_sboms import SBOMGenerator
from generate_grype import GrypeScanner
from generate_codeql import CodeQLAnalyzer
from clone_repos import RepoCloner
from generate_reports import ReportGenerator


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

    click.echo("\n[5/5] 📊 Generando reporte...")
    report_gen = ReportGenerator(output_dir)
    report_gen.generate_report()

    click.echo("\n✅ Pipeline completo ejecutado con éxito.")
    click.echo(f"   Resultados en: {output_dir}/")


if __name__ == "__main__":
    cli()
