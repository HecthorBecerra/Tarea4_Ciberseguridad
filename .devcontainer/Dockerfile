# ===== BASE IMAGE =====
FROM mcr.microsoft.com/devcontainers/python:1-3.11-bullseye

# ===== INSTALAR UV PACKAGE MANAGER =====
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# ===== INSTALAR SYFT (SBOM Generator) =====
RUN curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin

# ===== INSTALAR GRYPE (Vulnerability Scanner) =====
RUN curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin

# ===== INSTALAR JAVA 17 + MAVEN (para CodeQL Java/Scala: Spark, Dubbo) =====
RUN rm -f /etc/apt/sources.list.d/yarn.list /etc/apt/sources.list.d/yarn.sources && \
    apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jdk-headless \
    maven \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# ===== INSTALAR NODE.JS (para CodeQL JavaScript: ECharts, Superset) =====
RUN rm -f /etc/apt/sources.list.d/yarn.list /etc/apt/sources.list.d/yarn.sources && \
    apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ===== INSTALAR CODEQL CLI =====
RUN curl -sSfL https://github.com/github/codeql-cli-binaries/releases/download/v2.25.1/codeql-linux64.zip -o /tmp/codeql.zip \
    && unzip -q /tmp/codeql.zip -d /usr/local \
    && chmod +x /usr/local/codeql/codeql \
    && ln -s /usr/local/codeql/codeql /usr/local/bin/codeql \
    && rm /tmp/codeql.zip

# ===== DESCARGAR QUERY PACKS DE CODEQL =====
# python → Airflow, Superset | javascript → ECharts | java → Spark, Dubbo
RUN codeql pack download codeql/python-queries \
    && codeql pack download codeql/javascript-queries \
    && codeql pack download codeql/java-queries \
    || echo "Nota: Algunos packs pueden no estar disponibles offline"

# ===== VERIFICAR INSTALACIONES =====
RUN echo "═══════════════════════════════" \
    && echo "Verificando herramientas:" \
    && echo "CodeQL:" && codeql version \
    && echo "Grype:" && grype version \
    && echo "Syft:" && syft version \
    && echo "Node.js:" && node --version \
    && echo "npm:" && npm --version \
    && echo "Python:" && python --version \
    && echo "Java:" && java -version \
    && echo "Maven:" && mvn --version \
    && echo "═══════════════════════════════"

# ===== CONFIGURAR VARIABLES DE ENTORNO =====
ENV UV_LINK_MODE=copy
ENV UV_COMPILE_BYTECODE=1
ENV PATH="/usr/local/codeql:$PATH"