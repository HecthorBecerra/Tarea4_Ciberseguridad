import json
import pandas as pd
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


class VulnerabilityAnalyzer:
    def __init__(self, results_dir="data/results", output_file="data/results/analysis_summary.json"):
        self.results_dir = Path(results_dir)
        self.output_file = Path(output_file)

    def run(self):
        """Procesa todos los resultados del Miner y genera un dataset para el Visualizer"""
        console.print(
            "\n[bold cyan]════════════════════════════════════════[/bold cyan]")
        console.print(
            "[bold cyan]🧠 PREPARADOR DE DATOS DEL ANALYZER[/bold cyan]")
        console.print(
            "[bold cyan]════════════════════════════════════════[/bold cyan]")

        all_data = []

        # 1. Procesar resultados de Grype (Dependencias)
        for file in self.results_dir.glob("*-grype.json"):
            repo_name = file.name.replace("-grype.json", "")
            try:
                with open(file) as f:
                    content = json.load(f)
                    for match in content.get("matches", []):
                        vuln = match.get("vulnerability", {})
                        all_data.append({
                            "repo": repo_name,
                            "type": "Dependency",
                            "id": vuln.get("id"),
                            "severity": vuln.get("severity", "Unknown").upper(),
                            "category": vuln.get("cwes", [{"cwe": "Unknown"}])[0].get("cwe", "Unknown"),
                            "package": match.get("artifact", {}).get("name")
                        })
            except Exception as e:
                print(f"⚠️ Error analizando {file.name}: {e}")

        # 2. Procesar resultados de CodeQL (Código Fuente)
        for file in self.results_dir.glob("*-codeql.json"):
            repo_name = file.name.replace("-codeql.json", "")
            try:
                with open(file) as f:
                    content = json.load(f)
                    for finding in content.get("findings", []):
                        all_data.append({
                            "repo": repo_name,
                            "type": "Static Analysis",
                            "id": finding.get("rule_id"),
                            "severity": finding.get("severity", "Unknown").upper(),
                            "category": finding.get("name"),
                            "package": "Source Code"
                        })
            except Exception as e:
                print(f"⚠️ Error analizando {file.name}: {e}")

        if not all_data:
            console.print(
                "[bold red]❌ No se encontraron datos para analizar. Ejecuta Grype/CodeQL primero.[/bold red]")
            return {"status": "no_data"}

        df = pd.DataFrame(all_data)

        # 3. Caracterización Sistemática (Métricas)
        summary = {
            "total_vulnerabilities": len(df),
            "severity_distribution": df['severity'].value_counts().to_dict(),
            "type_distribution": df['type'].value_counts().to_dict(),
            "top_vulnerable_repos": df['repo'].value_counts().head(5).to_dict(),
            "most_common_categories": df['category'].value_counts().head(10).to_dict(),
            "patterns": self._identify_patterns(df)
        }

        # Guardar resultado para que el Visualizer lo lea
        with open(self.output_file, "w") as f:
            json.dump(summary, f, indent=2)

        # También guardamos el CSV crudo para que el Notebook (Analyzer Exploratorio) lo use
        df.to_csv(self.results_dir / "vulnerabilities_dataset.csv", index=False)

        # 4. Guardar dataset estructurado directo en el Visualizer (React)
        visualizer_data_dir = Path("visualizer/public")
        visualizer_data_dir.mkdir(parents=True, exist_ok=True)
        visualizer_file = visualizer_data_dir / "data.json"

        with open(visualizer_file, "w", encoding="utf-8") as f:
            json.dump({
                "summary": summary,
                "vulnerabilities": all_data
            }, f, indent=2, ensure_ascii=False)

        # --- OUTPUT VISUAL ---
        console.print(
            f"\n[green]✅ Dataset consolidado con éxito: {len(df)} hallazgos totales.[/green]\n")
        console.print(
            f"[green]✅ Datos inyectados al Visualizer en: {visualizer_file}[/green]\n")

        # Tabla de Severidad
        sev_table = Table(title="Distribución por Severidad")
        sev_table.add_column("Severidad", justify="left", style="cyan")
        sev_table.add_column("Frecuencia", justify="right", style="magenta")
        for sev, count in summary["severity_distribution"].items():
            sev_table.add_row(sev, str(count))

        # Tabla de Repos
        repo_table = Table(title="Top Repositorios Vulnerables")
        repo_table.add_column("Repositorio", justify="left", style="cyan")
        repo_table.add_column("Hallazgos", justify="right", style="magenta")
        for repo, count in summary["top_vulnerable_repos"].items():
            repo_table.add_row(repo, str(count))

        # Imprimir tablas
        console.print(sev_table)
        console.print(repo_table)

        # Patrones
        if summary["patterns"]:
            console.print(
                "\n[bold yellow]🔍 Patrones Iniciales Identificados:[/bold yellow]")
            for p in summary["patterns"]:
                console.print(f"  • {p}")

        # Instrucciones para el usuario
        console.print(
            "\n[bold green]Siguiente Paso (Análisis Exploratorio):[/bold green]")
        info_panel = Panel(
            "Para realizar el análisis sistemático interactivo y ver gráficos,\nabre el siguiente notebook en VS Code:\n\n[bold cyan]👉 nbs/05_analisis_cuantitativo.ipynb[/bold cyan]",
            expand=False,
            border_style="green"
        )
        console.print(info_panel)

        return summary

    def _identify_patterns(self, df):
        """Identifica patrones relevantes en los datos"""
        patterns = []

        # Patrón 1: Críticos en dependencias vs código
        criticals = df[df['severity'] == 'CRITICAL']
        if not criticals.empty:
            source = criticals['type'].value_counts().idxmax()
            patterns.append(f"El mayor riesgo crítico proviene de: {source}")

        # Patrón 2: Repositorios con fallos recurrentes
        if len(df['repo'].unique()) > 1:
            avg_vulns = len(df) / len(df['repo'].unique())
            outliers = df['repo'].value_counts()
            outliers = outliers[outliers > avg_vulns * 1.5].index.tolist()
            if outliers:
                patterns.append(
                    f"Repositorios significativamente sobre el promedio: {', '.join(outliers)}")

        return patterns
