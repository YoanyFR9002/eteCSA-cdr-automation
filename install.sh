#!/usr/bin/env bash
#
# Script de instalación para ASN.1 Web Decoder v3.0
#

set -euo pipefail

# Colores para output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m'

# Variables
readonly PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PYTHON_VERSION="3.11"
readonly VENV_NAME=".venv"

# Función de logging
log() {
    echo -e "${GREEN}[✓]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[!]${NC} $1"
}

error() {
    echo -e "${RED}[✗]${NC} $1" >&2
    exit 1
}

# Verificar prerequisitos
check_prerequisites() {
    log "Verificando prerequisitos..."
    
    command -v python3 >/dev/null 2>&1 || error "Python 3 no encontrado"
    command -v git >/dev/null 2>&1 || warn "Git no encontrado (opcional)"
    
    local py_version
    py_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    [[ "$py_version" == "$PYTHON_VERSION" ]] || warn "Se recomienda Python $PYTHON_VERSION, detectado: $py_version"
}

# Configurar entorno virtual
setup_venv() {
    log "Configurando entorno virtual..."
    cd "$PROJECT_DIR"
    
    if [[ ! -d "$VENV_NAME" ]]; then
        python3 -m venv "$VENV_NAME"
        log "Entorno virtual creado"
    fi
    
    # Activar entorno virtual
    source "$VENV_NAME/bin/activate"
    
    # Actualizar pip
    pip install --upgrade pip setuptools wheel
}

# Instalar dependencias
install_dependencies() {
    log "Instalando dependencias Python..."
    pip install -e .
    
    # Verificar instalación crítica
    python -c "from src.asn1_decoder.decoder import ASN1Decoder; print('✅ Motor ASN.1 importado correctamente')" || error "Fallo en importación del motor"
}

# Configurar variables de entorno
setup_env() {
    log "Configurando variables de entorno..."
    
    if [[ ! -f ".env" ]]; then
        cp .env.example .env
        warn "Archivo .env creado desde plantilla. Edítalo con tus configuraciones."
    fi
}

# Inicializar logs
init_logging() {
    log "Inicializando sistema de logs..."
    python -c "
from src.utils.logger import setup_logger
setup_logger()
print('✅ Sistema de logs inicializado')
"
}

# Mensaje final
show_completion() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✅ Instalación completada!         ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════╝${NC}"
    echo ""
    echo "📍 Directorio del proyecto: $PROJECT_DIR"
    echo "🚀 Para ejecutar: cd $PROJECT_DIR && ./run.sh start-dev"
    echo "🐳 Para producción: docker compose up -d"
    echo ""
}

# Función principal
main() {
    echo -e "${GREEN}🚀 Iniciando instalación de ASN.1 Web Decoder v3.0${NC}"
    echo ""
    
    check_prerequisites
    setup_venv
    install_dependencies
    setup_env
    init_logging
    show_completion
}

# Ejecutar si es el script principal
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
