#!/usr/bin/env python
"""Escanea vulnerabilidades usando Grype"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table

console = Console()

class GrypeScanner:
    def __init__(self, repos_dir: str, output_dir: str):
        self.repos_dir = Path(repos_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def scan_repo(self, repo_path: Path) -> dict:
        """Escanea un repositorio en busca de vulnerabilidades"""
        repo_name = repo_path.name
        
        console.print(f"\n[cyan]Escaneando vulnerabilidades:[/cyan] {repo_name}")
        
        output_file = self.output_dir / f"{repo_name}-grype.json"
        
        try:
            # Ejecutar grype
            cmd = [
                "grype",
                str(repo_path),
                "-o", "json",
                f"--file={output_file}"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0 or "Found:" in result.stdout:
                # Leer el archivo de salida para obtener estadísticas
                if output_file.exists():
                    with open(output_file) as f:
                        data = json.load(f)
                        vuln_count = len(data.get("matches", []))
                    
                    console.print(f"[green]✓ Escaneo completado:[/green] {vuln_count} vulnerabilidades encontradas")
                    
                    return {
                        "repo": repo_name,
                        "status": "success",
                        "vulnerabilities": vuln_count,
                        "output_file": str(output_file),
                        "timestamp": datetime.now().isoformat()
                    }
            else:
                console.print(f"[yellow]! Escaneo completado sin vulnerabilidades[/yellow]")
                return {
                    "repo": repo_name,
                    "status": "success",
                    "vulnerabilities": 0,
                    "output_file": str(output_file),
                }
                
        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")
            return {"repo": repo_name, "status": "error", "error": str(e)}

    def run(self):
        """Ejecuta escaneo para todos los repositorios"""
        console.print("[bold cyan]═══════════════════════════════[/bold cyan]")
        console.print("[bold cyan]ESCANER DE VULNERABILIDADES - Grype[/bold cyan]")
        console.print("[bold cyan]═══════════════════════════════[/bold cyan]")
        
        # Actualizar base de datos
        console.print("\n[yellow]Actualizando base de datos de Grype...[/yellow]")
        subprocess.run(["grype", "db", "update"], capture_output=True)
        
        repos = [d for d in self.repos_dir.iterdir() if d.is_dir()]
        
        if not repos:
            console.print("[yellow]No se encontraron repositorios[/yellow]")
            return
        
        results = []
        for repo in repos:
            result = self.scan_repo(repo)
            results.append(result)
        
        # Mostrar tabla resumen
        table = Table(title="Resumen de Escaneo")
        table.add_column("Repositorio", style="cyan")
        table.add_column("Vulnerabilidades", style="magenta")
        table.add_column("Estado", style="green")
        
        for result in results:
            vuln = result.get("vulnerabilities", "N/A")
            status = result.get("status", "unknown")
            table.add_row(result["repo"], str(vuln), status)
        
        console.print(table)
        
        # Guardar resumen
        summary_file = self.output_dir / "grype-summary.json"
        with open(summary_file, "w") as f:
            json.dump(results, f, indent=2)
        
        console.print(f"\n[blue]Resumen guardado en:[/blue] {summary_file}")

def main():
    repos_dir = "data/repos"
    output_dir = "data/results"
    
    scanner = GrypeScanner(repos_dir, output_dir)
    scanner.run()

if __name__ == "__main__":
    main()
