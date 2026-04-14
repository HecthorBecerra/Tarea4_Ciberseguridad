# Security Analyzer

Herramienta automatizada para análisis de seguridad en repositorios.

## Características

- 📦 **SBOM** - Generar Software Bill of Materials con Syft
- 🔓 **Grype** - Escanear vulnerabilidades en dependencias
- 🔍 **CodeQL** - Análisis estático de código
- 📊 **Reportes** - Visualización de resultados

## Inicio Rápido

```bash
# Instalar dependencias
uv sync

# Generar SBOMs
uv run main.py sbom

# Escanear vulnerabilidades
uv run main.py grype

# Analizar código
uv run main.py codeql

# O ejecutar todo
uv run main.py all
```

## Requisitos

- Docker
- VS Code con Dev Containers Extension

## Estructura

```
├── scripts/          # Scripts de análisis
├── nbs/             # Jupyter Notebooks
├── data/
│   ├── repos/       # Repositorios a analizar
│   └── results/     # Resultados de análisis
├── .devcontainer/   # Configuración del dev container
└── README.md
```
