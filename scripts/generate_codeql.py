#!/usr/bin/env python
"""Realiza análisis estático usando CodeQL"""

import json
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from rich.console import Console

console = Console()

class CodeQLAnalyzer:
    def __init__(self, repos_dir: str, output_dir: str):
        self.repos_dir = Path(repos_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.db_dir = self.output_dir / "databases"
        self.db_dir.mkdir(exist_ok=True)

    def analyze_repo(self, repo_path: Path) -> dict:
        """Analiza un repositorio con CodeQL"""
        repo_name = repo_path.name
        
        console.print(f"\n[cyan]Analizando con CodeQL:[/cyan] {repo_name}")
        
        # Crear base de datos
        db_path = self.db_dir / f"{repo_name}-db"
        results_file = self.output_dir / f"{repo_name}-codeql.json"
        
        try:
            # Paso 1: Crear base de datos
            console.print(f"  [yellow]→ Creando base de datos...[/yellow]")
            
            # Detectar lenguaje
            languages = self._detect_languages(repo_path)
            
            if not languages:
                console.print(f"  [yellow]! No se detectaron lenguajes soportados[/yellow]")
                return {
                    "repo": repo_name,
                    "status": "skipped",
                    "reason": "no_supported_languages"
                }
            
            for lang in languages:
                cmd = [
                    "codeql", "database", "create",
                    str(db_path),
                    "--language", lang,
                    "--source-root", str(repo_path)
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
                
                if result.returncode != 0:
                    console.print(f"  [red]✗ Error creando BD para {lang}[/red]")
                    return {
                        "repo": repo_name,
                        "status": "error",
                        "language": lang,
                        "error": result.stderr[:200]
                    }
            
            # Paso 2: Analizar
            console.print(f"  [yellow]→ Analizando...[/yellow]")
            
            sarif_file = self.output_dir / f"{repo_name}-codeql.sarif"
            
            # Mapeo de lenguaje a query pack
            query_packs = {
                "python": "codeql/python-queries:codeql-suites/python-security-and-quality.qls",
                "javascript": "codeql/javascript-queries:codeql-suites/javascript-security-and-quality.qls",
                "java": "codeql/java-queries:codeql-suites/java-security-and-quality.qls",
                "cpp": "codeql/cpp-queries:codeql-suites/cpp-security-and-quality.qls",
                "csharp": "codeql/csharp-queries:codeql-suites/csharp-security-and-quality.qls",
            }
            
            # Usar el primer lenguaje detectado para seleccionar query pack
            lang = languages[0]
            query_pack = query_packs.get(lang, f"codeql/{lang}-queries")
            
            cmd = [
                "codeql", "database", "analyze",
                str(db_path),
                query_pack,
                "--format=sarif-latest",
                f"--output={sarif_file}",
                "--download"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
            
            if result.returncode == 0:
                # Convertir SARIF a JSON simplificado
                findings = self._sarif_to_json(sarif_file, results_file)
                console.print(f"[green]✓ Análisis completado: {len(findings)} hallazgo(s)[/green]")
                return {
                    "repo": repo_name,
                    "status": "success",
                    "languages": languages,
                    "findings_count": len(findings),
                    "output_file": str(results_file),
                    "sarif_file": str(sarif_file),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                console.print(f"[red]✗ Error en análisis[/red]")
                return {
                    "repo": repo_name,
                    "status": "error",
                    "error": result.stderr[:200]
                }
                
        except subprocess.TimeoutExpired:
            console.print(f"[red]✗ Timeout analizando {repo_name}[/red]")
            return {"repo": repo_name, "status": "timeout"}
        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")
            return {"repo": repo_name, "status": "error", "error": str(e)}

    def _sarif_to_json(self, sarif_file: Path, json_file: Path) -> list:
        """Convierte SARIF a JSON simplificado"""
        try:
            with open(sarif_file) as f:
                sarif = json.load(f)
            
            findings = []
            for run in sarif.get("runs", []):
                tool_name = run.get("tool", {}).get("driver", {}).get("name", "unknown")
                rules = {r["id"]: r for r in run.get("tool", {}).get("driver", {}).get("rules", [])}
                
                for result in run.get("results", []):
                    rule_id = result.get("ruleId", "unknown")
                    rule_info = rules.get(rule_id, {})
                    
                    locations = []
                    for loc in result.get("locations", []):
                        phys = loc.get("physicalLocation", {})
                        locations.append({
                            "file": phys.get("artifactLocation", {}).get("uri", ""),
                            "startLine": phys.get("region", {}).get("startLine", 0),
                            "endLine": phys.get("region", {}).get("endLine", 0)
                        })
                    
                    findings.append({
                        "rule_id": rule_id,
                        "severity": rule_info.get("defaultConfiguration", {}).get("level", "warning"),
                        "name": rule_info.get("shortDescription", {}).get("text", rule_id),
                        "description": result.get("message", {}).get("text", ""),
                        "locations": locations,
                        "tool": tool_name
                    })
            
            with open(json_file, "w") as f:
                json.dump({"findings": findings, "total": len(findings)}, f, indent=2)
            
            return findings
        except Exception as e:
            console.print(f"  [yellow]! Error convirtiendo SARIF: {e}[/yellow]")
            return []

    def _detect_languages(self, repo_path: Path) -> list:
        """Detecta lenguajes en el repositorio"""
        languages = set()
        
        file_patterns = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "javascript",
            ".jsx": "javascript",
            ".tsx": "javascript",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "cpp",
            ".cs": "csharp",
        }
        
        for pattern, lang in file_patterns.items():
            if list(repo_path.rglob(f"*{pattern}")):
                languages.add(lang)
        
        return list(languages)

    def run(self):
        """Ejecuta análisis para todos los repositorios"""
        console.print("[bold cyan]═══════════════════════════════[/bold cyan]")
        console.print("[bold cyan]ANÁLISIS ESTÁTICO - CodeQL[/bold cyan]")
        console.print("[bold cyan]═══════════════════════════════[/bold cyan]")
        
        repos = [d for d in self.repos_dir.iterdir() if d.is_dir()]
        
        if not repos:
            console.print("[yellow]No se encontraron repositorios[/yellow]")
            return
        
        results = []
        for repo in repos:
            result = self.analyze_repo(repo)
            results.append(result)
        
        # Guardar resumen
        summary_file = self.output_dir / "codeql-summary.json"
        with open(summary_file, "w") as f:
            json.dump(results, f, indent=2)
        
        console.print(f"\n[blue]Resumen guardado en:[/blue] {summary_file}")

def main():
    repos_dir = "data/repos"
    output_dir = "data/results"
    
    analyzer = CodeQLAnalyzer(repos_dir, output_dir)
    analyzer.run()

if __name__ == "__main__":
    main()
