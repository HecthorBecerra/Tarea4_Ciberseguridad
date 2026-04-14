#!/usr/bin/env python
"""Genera reportes consolidados de todos los análisis"""

import json
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table

console = Console()


class ReportGenerator:
    def __init__(self, results_dir: str):
        self.results_dir = Path(results_dir)

    def generate_report(self):
        """Genera un reporte consolidado"""
        console.print("[bold cyan]═══════════════════════════════[/bold cyan]")
        console.print("[bold cyan]GENERADOR DE REPORTES[/bold cyan]")
        console.print("[bold cyan]═══════════════════════════════[/bold cyan]")

        report = {
            "generated_at": datetime.now().isoformat(),
            "sbom": self._load_summary("sbom-summary.json"),
            "grype": self._load_summary("grype-summary.json"),
            "codeql": self._load_summary("codeql-summary.json"),
        }

        # Mostrar resumen
        self._print_summary(report)

        # Guardar reporte
        report_file = self.results_dir / "consolidated-report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        console.print(f"\n[blue]Reporte guardado en:[/blue] {report_file}")

    def _load_summary(self, filename: str) -> list:
        """Carga un archivo de resumen"""
        summary_file = self.results_dir / filename
        if summary_file.exists():
            with open(summary_file) as f:
                return json.load(f)
        return []

    def _print_summary(self, report: dict):
        """Imprime un resumen del reporte"""
        # Tabla de SBOMs
        if report["sbom"]:
            table = Table(title="SBOMs Generados")
            table.add_column("Repositorio", style="cyan")
            table.add_column("Estado", style="green")
            for item in report["sbom"]:
                table.add_row(item.get("repo", "N/A"), item.get("status", "N/A"))
            console.print(table)

        # Tabla de vulnerabilidades
        if report["grype"]:
            table = Table(title="Vulnerabilidades (Grype)")
            table.add_column("Repositorio", style="cyan")
            table.add_column("Vulnerabilidades", style="magenta")
            table.add_column("Estado", style="green")
            for item in report["grype"]:
                table.add_row(
                    item.get("repo", "N/A"),
                    str(item.get("vulnerabilities", "N/A")),
                    item.get("status", "N/A"),
                )
            console.print(table)

        # Tabla de CodeQL
        if report["codeql"]:
            table = Table(title="Análisis Estático (CodeQL)")
            table.add_column("Repositorio", style="cyan")
            table.add_column("Lenguajes", style="magenta")
            table.add_column("Estado", style="green")
            for item in report["codeql"]:
                langs = ", ".join(item.get("languages", []))
                table.add_row(
                    item.get("repo", "N/A"), langs or "N/A", item.get("status", "N/A")
                )
            console.print(table)


def main():
    results_dir = "data/results"
    generator = ReportGenerator(results_dir)
    generator.generate_report()


if __name__ == "__main__":
    main()
