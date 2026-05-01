#!/usr/bin/env python
"""Script principal para ejecutar todos los análisis"""

import json
import logging
import sys
import click
from pathlib import Path

# Configuración básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Agregar scripts al path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from generate_sboms import SBOMGenerator
from generate_grype import GrypeScanner
from generate_codeql import CodeQLAnalyzer
from clone_repos import RepoCloner # RepoCloner will now handle GitHub API calls
from generate_reports import ReportGenerator

# Constantes para rutas por defecto
DEFAULT_CONFIG_PATH = "data/config.json"
DEFAULT_REPOS_DIR = "data/repos"
DEFAULT_OUTPUT_DIR = "data/results"


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
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"No se pudo cargar la configuración de concurrencia desde '{config_path}'. Usando 4 workers por defecto. Error: {e}")
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


@cli.command(name="clone")
@click.option("--config", default=DEFAULT_CONFIG_PATH, help="Ruta al archivo de configuración")
@click.option("--workers", default=None, type=int, help="Número de workers paralelos (override config)")
def clone(config, workers):
    """📥 Clonar repositorios desde config.json"""
    max_workers = _load_max_workers(config, workers)
    cloner = RepoCloner(config, max_workers=max_workers)
    logger.info(f"Iniciando clonación de repositorios con {max_workers} workers.")
    cloner.run()
    logger.info("Clonación de repositorios completada.")


@cli.command(name="gh-discover")
@click.option("--org", type=str, default=None,
              help="Nombre de la organización de GitHub para buscar repositorios (opcional).")
@click.option("--limit", type=int, default=50, help="Número de repositorios más estrellados a buscar.")
@click.option("--gh-token", envvar="GITHUB_TOKEN", default=None,
              help="Token de GitHub para autenticación (opcional). Puede ser una variable de entorno GITHUB_TOKEN.")
@click.option("--workers", default=None, type=int, help="Número de workers paralelos (override config)")
@click.option("--config", default=DEFAULT_CONFIG_PATH, help="Ruta al archivo de configuración para opciones de clonación.")
def gh_discover(org, limit, gh_token, workers, config):
    """✨ Descubre y clona repositorios de GitHub por popularidad (estrellas)."""
    max_workers = _load_max_workers(config, workers)
    
    # Instantiate RepoCloner to use its GitHub API methods
    temp_cloner = RepoCloner(config, max_workers=max_workers)
    
    logger.info(f"Buscando los {limit} repositorios de GitHub más estrellados {'en la organización ' + org if org else 'globalmente'}...")
    gh_repo_urls = temp_cloner.get_top_starred_github_repos(org_name=org, limit=limit, github_token=gh_token)
    
    if gh_repo_urls:
        cloner = RepoCloner(config, max_workers=max_workers, explicit_repo_urls=gh_repo_urls)
        cloner.run()
        logger.info(f"Clonación de {len(gh_repo_urls)} repositorios de GitHub completada.")

@cli.command(name="sbom")
@click.option("--config", default=DEFAULT_CONFIG_PATH, help="Ruta al archivo de configuración") # Añadido para consistencia
@click.option("--repos-dir", default=DEFAULT_REPOS_DIR, help="Directorio con repositorios")
@click.option("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Directorio de salida")
@click.option("--workers", default=None, type=int, help="Número de workers paralelos (override config)")
def sbom(config, repos_dir, output_dir, workers): # Añadido config
    """📦 Generar SBOMs con Syft"""
    max_workers = _load_max_workers(config, workers) # Usar la variable config
    generator = SBOMGenerator(repos_dir, output_dir, max_workers=max_workers)
    logger.info(f"Iniciando generación de SBOMs con {max_workers} workers.")
    generator.run()
    logger.info("Generación de SBOMs completada.")


@cli.command(name="grype")
@click.option("--config", default=DEFAULT_CONFIG_PATH, help="Ruta al archivo de configuración") # Añadido para consistencia
@click.option("--repos-dir", default=DEFAULT_REPOS_DIR, help="Directorio con repositorios")
@click.option("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Directorio de salida")
@click.option("--workers", default=None, type=int, help="Número de workers paralelos (override config)")
def grype(config, repos_dir, output_dir, workers): # Añadido config
    """🔓 Escanear vulnerabilidades con Grype"""
    max_workers = _load_max_workers(config, workers) # Usar la variable config
    scanner = GrypeScanner(repos_dir, output_dir, max_workers=max_workers)
    logger.info(f"Iniciando escaneo de vulnerabilidades con Grype con {max_workers} workers.")
    scanner.run()
    logger.info("Escaneo de vulnerabilidades con Grype completado.")


@cli.command(name="codeql")
@click.option("--config", default=DEFAULT_CONFIG_PATH, help="Ruta al archivo de configuración") # Añadido para consistencia
@click.option("--repos-dir", default=DEFAULT_REPOS_DIR, help="Directorio con repositorios")
@click.option("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Directorio de salida")
@click.option("--workers", default=None, type=int, help="Número de workers paralelos (override config)")
def codeql(config, repos_dir, output_dir, workers): # Añadido config
    """🔍 Analizar código con CodeQL"""
    max_workers = _load_max_workers(config, workers) # Usar la variable config
    analyzer = CodeQLAnalyzer(repos_dir, output_dir, max_workers=max_workers)
    logger.info(f"Iniciando análisis de código con CodeQL con {max_workers} workers.")
    analyzer.run()
    logger.info("Análisis de código con CodeQL completado.")


@cli.command(name="report")
@click.option("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Directorio de resultados")
def report(output_dir):
    """📊 Generar reporte consolidado"""
    generator = ReportGenerator(output_dir)
    generator.generate_report()


@cli.command(name="all")
@click.option("--config", default=DEFAULT_CONFIG_PATH, help="Ruta al archivo de configuración")
@click.option("--repos-dir", default=DEFAULT_REPOS_DIR, help="Directorio con repositorios")
@click.option("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Directorio de salida")
@click.option("--workers", default=None, type=int, help="Número de workers paralelos (override config)")
def run_all(config, repos_dir, output_dir, workers):
    """🚀 Ejecutar pipeline completo (clone → sbom → grype → codeql → report)"""
    max_workers = _load_max_workers(config, workers)

    logger.info(f"\n[Pipeline] Workers configurados: {max_workers}")

    try:
        logger.info("\n[1/5] 📥 Clonando repositorios...")
        cloner = RepoCloner(config, max_workers=max_workers)
        cloner.run()
        logger.info("Clonación de repositorios completada.")

        logger.info("\n[2/5] 📦 Generando SBOMs...")
        generator = SBOMGenerator(repos_dir, output_dir, max_workers=max_workers)
        generator.run()
        logger.info("Generación de SBOMs completada.")

        logger.info("\n[3/5] 🔓 Escaneando vulnerabilidades...")
        scanner = GrypeScanner(repos_dir, output_dir, max_workers=max_workers)
        scanner.run()
        logger.info("Escaneo de vulnerabilidades completado.")

        logger.info("\n[4/5] 🔍 Analizando código...")
        analyzer = CodeQLAnalyzer(repos_dir, output_dir, max_workers=max_workers)
        analyzer.run()
        logger.info("Análisis de código completado.")

        logger.info("\n[5/5] 📊 Generando reporte...")
        report_gen = ReportGenerator(output_dir)
        report_gen.generate_report()
        logger.info("Generación de reporte completada.")

        logger.info("\n✅ Pipeline completo ejecutado con éxito.")
        logger.info(f"   Resultados en: {output_dir}/")
    except Exception as e:
        logger.error(f"❌ El pipeline falló en una de las etapas: {e}", exc_info=True)
        sys.exit(1) # Salir con un código de error


if __name__ == "__main__":
    cli()
