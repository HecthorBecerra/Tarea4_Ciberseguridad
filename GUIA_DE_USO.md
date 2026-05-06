# 📖 Guía de Uso - Security Analyzer

Guía completa paso a paso para analizar vulnerabilidades de repositorios usando este proyecto.

---

## 📋 Tabla de Contenidos

1. [Requisitos Previos](#-1-requisitos-previos)
2. [Abrir el Proyecto en Dev Container](#-2-abrir-el-proyecto-en-dev-container)
3. [Configurar Repositorios](#-3-configurar-repositorios-a-analizar)
4. [Ejecutar Análisis de Seguridad](#-4-ejecutar-análisis-de-seguridad)
5. [🚀 Ejecución Simultánea (Modo Demo)](#-5-ejecución-simultánea-modo-demo)
6. [📊 Interpretar los Resultados](#-6-interpretar-los-resultados)
7. [📓 Usar los Notebooks Jupyter](#-7-usar-los-notebooks-jupyter)
8. [🖥️ Usar el Visualizer (Dashboard Interactivo)](#-8-usar-el-visualizer-dashboard-interactivo)
9. [⚡ Comandos de Referencia Rápida](#-9-comandos-de-referencia-rápida)
10. [🆘 Troubleshooting](#-10-troubleshooting)

---

## 🔧 1. Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:

| Requisito | Cómo verificar | Instalación |
|-----------|----------------|-------------|
| **Docker Desktop** | `docker --version` | [docker.com/get-started](https://www.docker.com/get-started/) |
| **VS Code** | Abrirlo | [code.visualstudio.com](https://code.visualstudio.com/) |
| **Extensión Dev Containers** | Panel de extensiones en VS Code | Buscar "Dev Containers" en el Marketplace |
| **Git** | `git --version` | [git-scm.com](https://git-scm.com/) |

> ⚠️ **Importante:** Docker Desktop debe estar **ejecutándose** antes de abrir el Dev Container.

---

## 🐳 2. Abrir el Proyecto en Dev Container

El Dev Container configura automáticamente todas las herramientas necesarias (CodeQL, Grype, Syft, Python, Node.js).

### Paso 2.1: Clonar el repositorio del proyecto

```powershell
git clone <URL_DEL_REPOSITORIO>
cd sbom-vuln-analysis
```

### Paso 2.2: Abrir en VS Code

```powershell
code .
```

### Paso 2.3: Reabrir en Container

1. Presiona `F1` (o `Ctrl+Shift+P`) para abrir la paleta de comandos
2. Escribe: **"Dev Containers: Reopen in Container"**
3. Selecciona la opción y espera a que se construya el container

```
⏳ La primera vez puede tardar 5-15 minutos (descarga de herramientas).
   Las siguientes veces será casi instantáneo.
```

### Paso 2.4: Verificar que todo funciona

Una vez dentro del container, abre una terminal (`Ctrl+`\``) y ejecuta:

```bash
# Verificar herramientas instaladas
codeql version
grype version
syft version
python --version
node --version

# Verificar dependencias de Python
uv run python -c "import click; import rich; print('✓ Dependencias OK')"
```

Si todo muestra versiones sin errores, ¡estás listo!

---

## 📂 3. Configurar Repositorios a Analizar

### ✨ Método recomendado: Usar `data/config.json`

Edita el archivo `data/config.json` para configurar qué repositorios analizar. El sistema los clonará automáticamente.

#### Opción A: Repositorios individuales (URLs)

Agrega las URLs directamente en la lista `repositories`:

```json
{
    "repositories": [
        "https://github.com/pallets/flask",
        "https://github.com/psf/requests",
        "https://github.com/django/django"
    ],
    "organizations": [],
    "clone_options": {
        "max_inactive_days": 30,
        "skip_archived": true,
        "skip_forks": true,
        "max_repos": 50
    }
}
```

#### Opción B: Organización completa de GitHub

Para analizar **todos los repositorios activos** de una organización open source:

```json
{
    "repositories": [],
    "organizations": ["pallets", "OWASP", "apache"],
    "clone_options": {
        "max_inactive_days": 30,
        "skip_archived": true,
        "skip_forks": true,
        "max_repos": 50
    }
}
```

#### Opción C: Combinación de ambos

```json
{
    "repositories": [
        "https://github.com/pallets/flask"
    ],
    "organizations": ["OWASP"],
    "clone_options": {
        "max_inactive_days": 30,
        "skip_archived": true,
        "skip_forks": true,
        "max_repos": 50
    }
}
```

#### Opciones de clonación explicadas

| Opción | Descripción | Valor por defecto |
|--------|-------------|-------------------|
| `max_inactive_days` | Solo clonar repos con commit en los últimos N días | `30` |
| `skip_archived` | Omitir repositorios archivados | `true` |
| `skip_forks` | Omitir forks (solo originales) | `true` |
| `max_repos` | Máximo de repos a clonar por organización | `50` |

### 📥 Clonar los repositorios configurados

Una vez configurado el `config.json`, ejecuta:

```bash
uv run python main.py clone
```

Salida esperada:
```
═══════════════════════════════════════
  CLONADOR DE REPOSITORIOS
═══════════════════════════════════════

📋 1 repositorio(s) individual(es) configurado(s)

🔄 Clonando 1 repositorio(s)...
  ↓ Clonando: flask
  ✓ Clonado: flask

┌─────────────┬────────────┬─────────────────────┐
│ Repositorio │ Estado     │ Ruta                │
├─────────────┼────────────┼─────────────────────┤
│ flask       │ ✓ Clonado  │ data/repos/flask    │
└─────────────┴────────────┴─────────────────────┘

✓ 1 exitosos  ✗ 0 errores
```

### Método alternativo: Clonar manualmente

Si prefieres, puedes clonar repos manualmente:

```bash
cd data/repos
git clone https://github.com/pallets/flask.git
cd /workspaces/sbom-vuln-analysis
```

---

## 🚀 4. Ejecutar Análisis de Seguridad

### 4.1: Ver la ayuda del CLI

```bash
uv run python main.py --help
```

Salida esperada:
```
Usage: main.py [OPTIONS] COMMAND [ARGS]...

  🔒 Herramienta de análisis de seguridad

Commands:
  clone    📥 Clonar repositorios desde config.json
  sbom     📦 Generar SBOMs con Syft
  grype    🔓 Escanear vulnerabilidades con Grype
  codeql   🔍 Analizar código con CodeQL
  analyze  🧠 Caracterizar vulnerabilidades (Analyzer)
  report   📊 Generar reporte consolidado
  all      🚀 Ejecutar pipeline completo
```

---

### 4.2: 🚀 Pipeline completo (recomendado)

Ejecuta **todo el flujo** con un solo comando:

```bash
uv run python main.py all
```

Esto ejecuta automáticamente:
1. **Clone** → Descarga repositorios desde `config.json`
2. **SBOM** → Genera lista de dependencias con Syft
3. **Grype** → Escanea vulnerabilidades en dependencias
4. **CodeQL** → Análisis estático del código fuente
5. **Report** → Genera reporte consolidado

---

### 4.3: Ejecutar pasos individuales

Si prefieres ejecutar paso a paso:

```bash
# Paso 1: Clonar repos
uv run python main.py clone

# Paso 2: Generar SBOMs (lista de dependencias)
uv run python main.py sbom

# Paso 3: Escanear vulnerabilidades en dependencias
uv run python main.py grype

# Paso 4: Análisis estático del código (puede tardar)
uv run python main.py codeql

# Paso 5: Generar reporte consolidado
uv run python main.py report
```

---

### 4.4: Detalle de cada análisis

#### 📦 SBOM (Syft)
- **¿Qué hace?** Lista todos los componentes y dependencias del repositorio
- **Herramienta:** Syft (Anchore)
- **Resultado:** `data/results/<repo>-sbom.json`
- **Tiempo:** ~30 segundos por repo

#### 🔓 Grype
- **¿Qué hace?** Busca CVEs conocidos en las dependencias detectadas
- **Herramienta:** Grype (Anchore)
- **Base de datos:** NVD, GitHub Advisory, OSV
- **Clasifica por:** Critical 🔴 | High 🟠 | Medium 🟡 | Low 🟢
- **Resultado:** `data/results/<repo>-grype.json`
- **Tiempo:** ~1-2 minutos por repo

#### 🔍 CodeQL
- **¿Qué hace?** Encuentra vulnerabilidades en el código fuente (SQL injection, XSS, etc.)
- **Herramienta:** CodeQL (GitHub)
- **Lenguajes soportados:** Python, JavaScript, Java, C++, C#
- **Resultado:** `data/results/<repo>-codeql.json`
- **Tiempo:** ~5-20 minutos por repo (el más lento)

---

## 📊 5. Interpretar los Resultados

Después de ejecutar los análisis, los resultados estarán en `data/results/`:

```
data/results/
├── clone-log.json                 # Log de repos clonados
├── analysis_summary.json          # Resumen lógico del Analyzer 🧠
├── vulnerabilities_dataset.csv    # Dataset estructurado para el Visualizer
├── sbom-summary.json              # Resumen de SBOMs
├── grype-summary.json             # Resumen de vulnerabilidades
├── codeql-summary.json            # Resumen de análisis estático
├── consolidated-report.json       # Reporte consolidado
├── flask-sbom.json                # SBOM detallado de Flask
├── flask-grype.json               # Vulnerabilidades de Flask
├── flask-codeql.json              # Hallazgos CodeQL de Flask
├── databases/                     # Bases de datos CodeQL
└── exports/                       # CSVs exportados (desde notebook)
```

### 5.1: Ver resultados rápidamente

```bash
# Resumen de clonación
cat data/results/clone-log.json | python -m json.tool

# Resumen de vulnerabilidades (Grype)
cat data/results/grype-summary.json | python -m json.tool

# Resumen del Analyzer
cat data/results/analysis_summary.json | python -m json.tool

# Reporte consolidado
cat data/results/consolidated-report.json | python -m json.tool
```

### 5.2: Extraer vulnerabilidades críticas

```bash
cat data/results/flask-grype.json | python -c "
import json, sys
data = json.load(sys.stdin)
for match in data.get('matches', [])[:10]:
    vuln = match['vulnerability']
    pkg = match['artifact']['name']
    print(f\"{vuln['severity']:10} | {vuln['id']:20} | {pkg}\")
"
```


## 📓 7. Usar los Notebooks Jupyter

### ⭐ Notebook principal: `05_analisis_cuantitativo.ipynb`

Este es el notebook más importante para la **Parte 3 de la actividad**. Contiene:

| Sección | Análisis |
|---------|----------|
| **2. Dependencias (SBOM)** | Total de dependencias, tipos de paquete, distribución por repo, licencias |
| **3. Vulnerabilidades (Grype)** | Severidad, distribución, paquetes más vulnerables, correcciones disponibles |
| **4. Código Fuente (CodeQL)** | Hallazgos por nivel, reglas más frecuentes |
| **5. Resumen Ejecutivo** | Métricas de riesgo consolidadas, ratio vulns/dependencias |
| **6. Export a CSV** | Exporta datos para Excel/Google Sheets |
| **Conclusiones** | Sección para escribir tus conclusiones |

### Cómo usarlo

1. Abre `nbs/05_analisis_cuantitativo.ipynb` en VS Code
2. Selecciona el kernel **"Python (security-analyzer)"**
3. Ejecuta todas las celdas: `Ctrl+Shift+Enter` (Run All)
4. Los resultados se generan automáticamente con gráficos ASCII y tablas
5. Escribe tus conclusiones en la sección final

### Otros notebooks disponibles

| Notebook | Descripción |
|----------|-------------|
| `01_introduccion_vulnerabilidades.ipynb` | Conceptos básicos de vulnerabilidades |
| `02_codeql_analisis.ipynb` | Explorar resultados de CodeQL |
| `03_grype_escaneo.ipynb` | Analizar vulnerabilidades de Grype |
| `04_sbom_generacion.ipynb` | Explorar componentes de SBOMs |
| **`05_analisis_cuantitativo.ipynb`** | **📊 Análisis completo (Parte 3)** |


---

## 🖥️ 8. Usar el Visualizer (Dashboard Interactivo)

El proyecto incluye una aplicación web (frontend) construida para visualizar interactivamente las vulnerabilidades procesadas por el Analyzer.

Asegúrate de haber ejecutado `uv run python main.py analyze` previamente para generar los datos consolidados (`visualizer/public/data.json`).

Para iniciar el Visualizer:

```bash
# 1. Entrar al directorio del frontend
cd visualizer

# 2. Instalar dependencias
npm install

# 3. Levantar el servidor de desarrollo
npm run dev
```
Abre la URL local que aparece en la terminal (usualmente `http://localhost:5173`) en tu navegador para ver los gráficos interactivos y tablas del proyecto.

---

## ⚡ 9. Comandos de Referencia Rápida

### 🏃 Flujo express (4 comandos)

```bash
# 1. Editar config con las URLs/orgs deseadas
nano data/config.json

# 2. Ejecutar todo el pipeline
uv run python main.py all

# 3. Abrir el notebook de análisis
# → Abrir nbs/05_analisis_cuantitativo.ipynb en VS Code

# 4. Ejecutar todas las celdas del notebook
# → Ctrl+Shift+Enter
```

### Tabla de comandos

| Acción | Comando |
|--------|---------|
| 📥 Clonar repos | `uv run python main.py clone` |
| 📦 Generar SBOM | `uv run python main.py sbom` |
| 🔓 Escanear vulnerabilidades | `uv run python main.py grype` |
| 🔍 Análisis estático | `uv run python main.py codeql` |
| 🧠 Ejecutar Analyzer | `uv run python main.py analyze` |
| 📊 Generar reporte | `uv run python main.py report` |
| 🚀 Ejecutar todo | `uv run python main.py all` |
| ❓ Ver ayuda | `uv run python main.py --help` |

### Herramientas directas (sin los scripts Python)

```bash
# Generar SBOM directamente con Syft
syft data/repos/flask -o json --file=salida.json

# Escanear con Grype directamente
grype data/repos/flask -o json --file=vulnerabilidades.json

# Ver versiones instaladas
codeql version && grype version && syft version
```

---

## 🆘 10. Troubleshooting

### El Dev Container no inicia

```powershell
# Verificar que Docker está corriendo
docker ps

# Si no está corriendo, iniciar Docker Desktop
# Luego intentar de nuevo: F1 → "Reopen in Container"
```

### Error: "No se encontraron repositorios"

```bash
# Verificar que config.json tiene repos configurados
cat data/config.json

# Ejecutar clone
uv run python main.py clone

# Verificar que se clonaron
ls data/repos/
```

### Límite de API de GitHub (403)

```bash
# Sin token: 60 requests/hora
# Con token: 5000 requests/hora

# Configurar token:
export GITHUB_TOKEN=tu_token_aqui

# El script de clone lo usará automáticamente
```

### CodeQL tarda demasiado

```bash
# CodeQL puede tardar 5-20 minutos en proyectos grandes
# Si solo necesitas SBOM + Grype, omite CodeQL:
uv run python main.py clone
uv run python main.py sbom
uv run python main.py grype
uv run python main.py report

# Si quieres incluir el Analyzer después de los escaneos:
uv run python main.py analyze

```

### Grype falla al actualizar la base de datos

```bash
# Actualizar manualmente
grype db update

# Si no hay conexión a internet
grype data/repos/flask --db-auto-update=false
```

### Error de espacio en disco

```bash
# Necesitas ~5-10 GB libres
docker system prune -a
```

### Las dependencias de Python fallan

```bash
uv sync
uv run python -c "import click, rich, pandas; print('OK')"
```

### El kernel de Jupyter no aparece

```bash
uv run python -m ipykernel install --user --name security-analyzer --display-name "Python (security-analyzer)"
```

---

## 🔄 Flujo de Trabajo Completo

```
┌──────────────────────────────────────────────────────────────┐
│                 PIPELINE DE ANÁLISIS DE SEGURIDAD            │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Configurar ──→ data/config.json                          │
│     (URLs individuales o nombres de organizaciones)          │
│         │                                                    │
│         ▼                                                    │
│  2. uv run python main.py all                                │
│         │                                                    │
│         ├──→ Clone    → Descarga repos automáticamente       │
│         ├──→ SBOM     → Lista de componentes (Syft)          │
│         ├──→ Grype    → CVEs en dependencias                 │
│         ├──→ CodeQL   → Vulnerabilidades en código fuente    │
│         └──→ Report   → Reporte consolidado JSON             │
│         │                                                    │
│         ▼                                                    │
│  3. Resultados ──→ data/results/*.json                       │
│         │                                                    │
│         ▼                                                    │
│  4. Notebook ──→ nbs/05_analisis_cuantitativo.ipynb           │
│     (Análisis cuantitativo + exportar a CSV)                 │
│         │                                                    │
│         ▼                                                    │
│  5. Conclusiones y entrega                                   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

**Creada para el curso de Ciberseguridad (ICC610) - 2026**
