#!/usr/bin/env python
"""Realiza análisis estático usando CodeQL"""

import json
import threading
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console

from .subprocess_utils import run_command

console = Console()
_print_lock = threading.Lock()


def _safe_print(*args, **kwargs):
    """Imprime de forma thread-safe."""
    with _print_lock:
        console.print(*args, **kwargs)


# Lenguajes interpretados que soportan --build-mode=none (sin compilacion)
_INTERPRETED_LANGS = frozenset({"python", "javascript", "ruby"})


class CodeQLAnalyzer:
    def __init__(self, repos_dir: str, output_dir: str, max_workers: int = 4,
                 *, primary_language_only: bool = True):
        self.repos_dir = Path(repos_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.db_dir = self.output_dir / "databases"
        self.db_dir.mkdir(exist_ok=True)
        self.max_workers = max_workers
        self.primary_language_only = primary_language_only

        # Detectar recursos disponibles del sistema
        self._threads = self._detect_threads()
        self._ram_mb = self._detect_ram()

    @staticmethod
    def _detect_threads() -> int:
        """Detecta el numero de CPUs disponibles."""
        import os
        return os.cpu_count() or 4

    @staticmethod
    def _detect_ram() -> int:
        """Detecta la RAM disponible y reserva una porcion para CodeQL."""
        import subprocess as sp
        try:
            result = sp.run(
                ["free", "-m"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                # Linea "Mem:" -> columna "available"
                for line in result.stdout.splitlines():
                    if line.startswith("Mem:"):
                        available = int(line.split()[-1])
                        # Usar 75% de la RAM disponible, minimo 1024 MB
                        return max(1024, int(available * 0.75))
        except (OSError, ValueError, sp.TimeoutExpired):
            pass
        return 2048  # fallback

    def _estimate_timeout(self, repo_path: Path) -> int:
        """Estima un timeout razonable basado en el tamano del repositorio."""
        import subprocess as sp
        try:
            result = sp.run(
                ["du", "-sb", str(repo_path)],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                size_bytes = int(result.stdout.split()[0])
                size_mb = size_bytes / (1024 * 1024)
            else:
                size_mb = 100  # fallback
            # Entre 10 min (minimo) y 60 min (maximo), escalando ~5s por MB
            return max(600, min(3600, int(size_mb * 5)))
        except (OSError, ValueError, sp.TimeoutExpired):
            return 900  # 15 min por defecto si no se puede calcular

    def analyze_repo(self, repo_path: Path) -> dict:
        """Analiza un repositorio con CodeQL.

        Crea una BD separada por cada lenguaje detectado, continúa si algún
        lenguaje falla y consolida los hallazgos de todos los lenguajes
        exitosos en un único JSON de salida.
        """
        repo_name = repo_path.name

        _safe_print(f"\n[cyan]Analizando con CodeQL:[/cyan] {repo_name}")

        results_file = self.output_dir / f"{repo_name}-codeql.json"

        try:
            # Paso 1: Detectar lenguajes
            _safe_print(f"  [yellow]→ Detectando lenguajes...[/yellow]")
            languages = self._detect_languages(repo_path)

            if not languages:
                _safe_print(
                    f"  [yellow]! No se detectaron lenguajes soportados (umbral mínimo: 5 archivos)[/yellow]")
                return {
                    "repo": repo_name,
                    "status": "skipped",
                    "reason": "no_supported_languages"
                }

            # Solo analizar el lenguaje principal si esta habilitado
            if self.primary_language_only:
                languages = languages[:1]
                _safe_print(
                    f"  [blue]  Lenguaje principal: {languages[0]}[/blue]")
            else:
                _safe_print(
                    f"  [blue]  Lenguajes detectados: {', '.join(languages)}[/blue]")

            # Timeout adaptativo segun tamano del repo
            db_timeout = self._estimate_timeout(repo_path)
            _safe_print(
                f"  [blue]  Timeout estimado: {db_timeout // 60} min[/blue]")
            _safe_print(
                f"  [blue]  Threads: {self._threads} | RAM: {self._ram_mb} MB[/blue]")

            # Query suites: security-extended es ~3x mas rapido que security-and-quality
            # (54 vs 176 queries) y cubre las vulnerabilidades relevantes
            query_packs = {
                "python": "codeql/python-queries:codeql-suites/python-security-extended.qls",
                "javascript": "codeql/javascript-queries:codeql-suites/javascript-security-extended.qls",
                "java": "codeql/java-queries:codeql-suites/java-security-extended.qls",
                "cpp": "codeql/cpp-queries:codeql-suites/cpp-security-extended.qls",
                "csharp": "codeql/csharp-queries:codeql-suites/csharp-security-extended.qls",
            }

            all_findings = []
            successful_langs = []
            errors = []

            for lang in languages:
                # Paso 2: Crear BD separada por lenguaje
                lang_db_path = self.db_dir / f"{repo_name}-{lang}-db"
                _safe_print(f"  [yellow]→ Creando BD para {lang}...[/yellow]")

                cmd = [
                    "codeql", "database", "create",
                    str(lang_db_path),
                    "--language", lang,
                    "--source-root", str(repo_path),
                    "--overwrite",
                    f"--threads={self._threads}",
                ]
                # Para lenguajes interpretados, --build-mode=none es mas rapido
                if lang in _INTERPRETED_LANGS:
                    cmd.append("--build-mode=none")

                result = run_command(cmd, timeout=db_timeout)

                if not result.success:
                    error_detail = result.error_message or result.stderr[:200]
                    _safe_print(
                        f"  [red]✗ Error creando BD para {lang}: {error_detail[:100]}[/red]")
                    errors.append(
                        {"language": lang, "phase": "create", "error": error_detail})
                    continue  # Continuar con el siguiente lenguaje

                # Paso 3: Analizar la BD creada
                _safe_print(f"  [yellow]→ Analizando {lang}...[/yellow]")

                sarif_file = self.output_dir / \
                    f"{repo_name}-{lang}-codeql.sarif"
                query_pack = query_packs.get(lang, f"codeql/{lang}-queries")

                cmd = [
                    "codeql", "database", "analyze",
                    str(lang_db_path),
                    query_pack,
                    "--format=sarif-latest",
                    f"--output={sarif_file}",
                    "--download",
                    f"--threads={self._threads}",
                    f"--ram={self._ram_mb}",
                ]

                analyze_timeout = max(900, db_timeout)
                result = run_command(cmd, timeout=analyze_timeout)

                if result.success:
                    findings = self._parse_sarif(sarif_file)
                    all_findings.extend(findings)
                    successful_langs.append(lang)
                    _safe_print(
                        f"  [green]✓ {lang}: {len(findings)} hallazgo(s)[/green]")
                else:
                    error_detail = result.error_message or result.stderr[:200]
                    _safe_print(
                        f"  [red]✗ Error analizando {lang}: {error_detail[:100]}[/red]")
                    errors.append(
                        {"language": lang, "phase": "analyze", "error": error_detail})

            # Paso 4: Consolidar resultados
            if successful_langs:
                with open(results_file, "w") as f:
                    json.dump({"findings": all_findings,
                              "total": len(all_findings)}, f, indent=2)

                _safe_print(f"[green]✓ Análisis completado para {repo_name}: "
                            f"{len(all_findings)} hallazgo(s) en {', '.join(successful_langs)}[/green]")
                result_dict = {
                    "repo": repo_name,
                    "status": "success" if not errors else "partial",
                    "languages": successful_langs,
                    "findings_count": len(all_findings),
                    "output_file": str(results_file),
                    "timestamp": datetime.now().isoformat()
                }
                if errors:
                    result_dict["errors"] = errors
                return result_dict
            else:
                _safe_print(
                    f"[red]✗ No se pudo analizar ningún lenguaje en {repo_name}[/red]")
                return {
                    "repo": repo_name,
                    "status": "error",
                    "errors": errors
                }

        except Exception as e:
            _safe_print(f"[red]✗ Error: {e}[/red]")
            return {"repo": repo_name, "status": "error", "error": str(e)}

    def _parse_sarif(self, sarif_file: Path) -> list:
        """Parsea un archivo SARIF y devuelve lista de hallazgos."""
        try:
            with open(sarif_file) as f:
                sarif = json.load(f)

            findings = []
            for run in sarif.get("runs", []):
                tool_name = run.get("tool", {}).get(
                    "driver", {}).get("name", "unknown")
                rules = {r["id"]: r for r in run.get(
                    "tool", {}).get("driver", {}).get("rules", [])}

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

            return findings
        except Exception as e:
            _safe_print(f"  [yellow]! Error parseando SARIF: {e}[/yellow]")
            return []

    def _detect_languages(self, repo_path: Path, min_files: int = 5) -> list:
        """Detecta lenguajes en el repositorio con umbral mínimo.

        Solo reporta un lenguaje si se encuentran al menos `min_files`
        archivos de ese lenguaje, evitando falsos positivos por archivos
        de configuración aislados (p.ej. un solo .eleventy.js).

        Los lenguajes se devuelven ordenados por cantidad de archivos
        (el más predominante primero).

        Usa `find` del sistema para máxima velocidad en repos grandes.
        """
        import subprocess as sp

        language_counts: dict[str, int] = {}

        # Agrupamos extensiones por lenguaje para hacer menos llamadas
        lang_extensions = {
            "python": [".py"],
            "javascript": [".js", ".ts", ".jsx", ".tsx"],
            "java": [".java"],
            "cpp": [".cpp", ".c"],
            "csharp": [".cs"],
        }

        for lang, extensions in lang_extensions.items():
            # Construir comando find con múltiples -name OR
            find_args = ["find", str(repo_path), "-type", "f", "("]
            for i, ext in enumerate(extensions):
                if i > 0:
                    find_args.append("-o")
                find_args.extend(["-name", f"*{ext}"])
            find_args.append(")")

            try:
                result = sp.run(
                    find_args,
                    capture_output=True, text=True, timeout=60
                )
                if result.returncode == 0 and result.stdout.strip():
                    count = result.stdout.strip().count("\n") + 1
                    language_counts[lang] = count
            except (sp.TimeoutExpired, OSError):
                pass

        # Filtrar por umbral mínimo
        qualified = {
            lang: count for lang, count in language_counts.items()
            if count >= min_files
        }

        if qualified:
            _safe_print(
                f"  [dim]  Conteo de archivos: {dict(sorted(language_counts.items(), key=lambda x: -x[1]))}[/dim]")
            if len(language_counts) > len(qualified):
                skipped = set(language_counts) - set(qualified)
                _safe_print(
                    f"  [dim]  Lenguajes descartados (< {min_files} archivos): {skipped}[/dim]")

        # Ordenar por cantidad descendente (el principal primero)
        return sorted(qualified.keys(), key=lambda l: qualified[l], reverse=True)

    def run(self):
        """Ejecuta análisis para todos los repositorios"""
        _safe_print("[bold cyan]═══════════════════════════════[/bold cyan]")
        _safe_print("[bold cyan]ANÁLISIS ESTÁTICO - CodeQL[/bold cyan]")
        _safe_print("[bold cyan]═══════════════════════════════[/bold cyan]")

        repos = [d for d in self.repos_dir.iterdir() if d.is_dir()]

        if not repos:
            _safe_print("[yellow]No se encontraron repositorios[/yellow]")
            return

        workers = self.max_workers
        mode = f"paralelo ({workers} workers)" if workers > 1 else "secuencial"
        _safe_print(
            f"\n[blue]🔍 Analizando {len(repos)} repositorio(s) — modo {mode}...[/blue]")

        results = []
        if workers > 1:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {
                    executor.submit(self.analyze_repo, repo): repo
                    for repo in repos
                }
                for future in as_completed(futures):
                    results.append(future.result())
        else:
            for repo in repos:
                result = self.analyze_repo(repo)
                results.append(result)

        # Guardar resumen
        summary_file = self.output_dir / "codeql-summary.json"
        with open(summary_file, "w") as f:
            json.dump(results, f, indent=2)

        _safe_print(f"\n[blue]Resumen guardado en:[/blue] {summary_file}")


def main():
    repos_dir = "data/repos"
    output_dir = "data/results"

    analyzer = CodeQLAnalyzer(repos_dir, output_dir)
    analyzer.run()


if __name__ == "__main__":
    main()
