FROM python:3.11-slim-bookworm

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de dependencias
COPY pyproject.toml requirements.txt ./

# Instalar dependencias Python
RUN pip install --upgrade pip && \
    pip install -e .[dev]

# Copiar código fuente
COPY src/ ./src/
COPY templates/ ./templates/
COPY static/ ./static/

# Crear directorios necesarios
RUN mkdir -p logs uploads exports && \
    chown -R nobody:nogroup /app

# Usuario no root por seguridad
USER nobody

# Puerto de la aplicación
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/health')" || exit 1

# Comando de inicio con Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "src.api.routes:app"]
