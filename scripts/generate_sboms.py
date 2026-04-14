#!/usr/bin/env python
"""Genera SBOMs (Software Bill of Materials) usando Syft"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from rich.console import Console

console = Console()

class SBOMGenerator:
    def __init__(self, repos_dir: str, output_dir: str):
        self.repos_dir = Path(repos_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_sbom(self, repo_path: Path) -> dict:
        """Genera un SBOM para un repositorio específico"""
        repo_name = repo_path.name
        
        console.print(f"\n[cyan]Generando SBOM para:[/cyan] {repo_name}")
        
        output_file = self.output_dir / f"{repo_name}-sbom.json"
        
        try:
            # Ejecutar syft
            cmd = [
                "syft",
                str(repo_path),
                "-o", "json",
                f"--file={output_file}"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                console.print(f"[green]✓ SBOM generado:[/green] {output_file}")
                return {
                    "repo": repo_name,
                    "status": "success",
                    "output_file": str(output_file),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                console.print(f"[red]✗ Error generando SBOM:[/red] {result.stderr}")
                return {
                    "repo": repo_name,
                    "status": "error",
                    "error": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            console.print(f"[red]✗ Timeout generando SBOM para {repo_name}[/red]")
            return {"repo": repo_name, "status": "timeout"}
        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")
            return {"repo": repo_name, "status": "error", "error": str(e)}

    def run(self):
        """Ejecuta generación de SBOMs para todos los repositorios"""
        console.print("[bold cyan]═══════════════════════════════[/bold cyan]")
        console.print("[bold cyan]GENERADOR DE SBOMs - Syft[/bold cyan]")
        console.print("[bold cyan]═══════════════════════════════[/bold cyan]")
        
        repos = [d for d in self.repos_dir.iterdir() if d.is_dir()]
        
        if not repos:
            console.print("[yellow]No se encontraron repositorios[/yellow]")
            return
        
        results = []
        for repo in repos:
            result = self.generate_sbom(repo)
            results.append(result)
        
        # Guardar resumen
        summary_file = self.output_dir / "sbom-summary.json"
        with open(summary_file, "w") as f:
            json.dump(results, f, indent=2)
        
        console.print(f"\n[blue]Resumen guardado en:[/blue] {summary_file}")

def main():
    repos_dir = "data/repos"
    output_dir = "data/results"
    
    generator = SBOMGenerator(repos_dir, output_dir)
    generator.run()

if __name__ == "__main__":
    main()
