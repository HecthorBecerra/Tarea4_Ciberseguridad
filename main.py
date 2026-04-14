#!/usr/bin/env python
"""Script principal para ejecutar todos los análisis"""

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
def clone(config):
    """📥 Clonar repositorios desde config.json"""
    cloner = RepoCloner(config)
    cloner.run()


@cli.command()
@click.option("--repos-dir", default="data/repos", help="Directorio con repositorios")
@click.option("--output-dir", default="data/results", help="Directorio de salida")
def sbom(repos_dir, output_dir):
    """📦 Generar SBOMs con Syft"""
    generator = SBOMGenerator(repos_dir, output_dir)
    generator.run()


@cli.command()
@click.option("--repos-dir", default="data/repos", help="Directorio con repositorios")
@click.option("--output-dir", default="data/results", help="Directorio de salida")
def grype(repos_dir, output_dir):
    """🔓 Escanear vulnerabilidades con Grype"""
    scanner = GrypeScanner(repos_dir, output_dir)
    scanner.run()


@cli.command()
@click.option("--repos-dir", default="data/repos", help="Directorio con repositorios")
@click.option("--output-dir", default="data/results", help="Directorio de salida")
def codeql(repos_dir, output_dir):
    """🔍 Analizar código con CodeQL"""
    analyzer = CodeQLAnalyzer(repos_dir, output_dir)
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
def run_all(config, repos_dir, output_dir):
    """🚀 Ejecutar pipeline completo (clone → sbom → grype → codeql → report)"""
    click.echo("\n[1/5] 📥 Clonando repositorios...")
    cloner = RepoCloner(config)
    cloner.run()

    click.echo("\n[2/5] 📦 Generando SBOMs...")
    generator = SBOMGenerator(repos_dir, output_dir)
    generator.run()

    click.echo("\n[3/5] 🔓 Escaneando vulnerabilidades...")
    scanner = GrypeScanner(repos_dir, output_dir)
    scanner.run()

    click.echo("\n[4/5] 🔍 Analizando código...")
    analyzer = CodeQLAnalyzer(repos_dir, output_dir)
    analyzer.run()

    click.echo("\n[5/5] 📊 Generando reporte...")
    report_gen = ReportGenerator(output_dir)
    report_gen.generate_report()

    click.echo("\n✅ Pipeline completo ejecutado con éxito.")
    click.echo(f"   Resultados en: {output_dir}/")


if __name__ == "__main__":
    cli()
