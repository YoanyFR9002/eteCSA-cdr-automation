#!/usr/bin/env bash
#
# Script de ejecución para ASN.1 Web Decoder v3.0
#

set -euo pipefail

readonly PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly VENV="$PROJECT_DIR/.venv"
readonly LOG_FILE="$PROJECT_DIR/logs/decoder.log"
readonly PID_FILE="$PROJECT_DIR/logs/decoder.pid"

# Cargar variables de entorno
if [[ -f "$PROJECT_DIR/.env" ]]; then
    source "$PROJECT_DIR/.env"
fi

# Activar entorno virtual
activate_venv() {
    if [[ -d "$VENV" ]]; then
        source "$VENV/bin/activate"
    fi
}

# Iniciar servidor (modo desarrollo)
start_dev() {
    activate_venv
    cd "$PROJECT_DIR"
    
    log "🔧 Iniciando en modo desarrollo..."
    export FLASK_ENV=development
    export FLASK_DEBUG=1
    
    flask run --host=0.0.0.0 --port=5000 --reload
}

# Iniciar servidor (modo producción con Gunicorn)
start_prod() {
    activate_venv
    cd "$PROJECT_DIR"
    
    log "🚀 Iniciando en modo producción con Gunicorn..."
    
    gunicorn \
        --bind "${BIND_ADDRESS:-0.0.0.0}:${PORT:-5000}" \
        --workers "${WORKERS:-4}" \
        --timeout "${TIMEOUT:-120}" \
        --access-logfile "$LOG_FILE" \
        --error-logfile "$LOG_FILE" \
        --pid "$PID_FILE" \
        src.api.routes:app
}

# Detener servidor
stop_server() {
    if [[ -f "$PID_FILE" ]]; then
        local pid
        pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            log "🛑 Deteniendo proceso $pid..."
            kill "$pid"
            rm -f "$PID_FILE"
        fi
    else
        pkill -f "gunicorn.*src.api.routes:app" 2>/dev/null || true
    fi
    log "✅ Servidor detenido"
}

# Verificar estado
check_status() {
    if [[ -f "$PID_FILE" ]]; then
        local pid
        pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            echo "✅ Servidor ejecutándose (PID: $pid)"
            return 0
        fi
    fi
    echo "❌ Servidor no está ejecutándose"
    return 1
}

# Logging helper
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Menú de ayuda
show_help() {
    cat << EOF
Uso: $0 [comando]

Comandos disponibles:
    start       - Iniciar servidor (auto-detecta modo)
    start-dev   - Iniciar en modo desarrollo (Flask debug)
    start-prod  - Iniciar en modo producción (Gunicorn)
    stop        - Detener servidor
    status      - Verificar estado del servidor
    restart     - Reiniciar servidor
    help        - Mostrar esta ayuda

Variables de entorno opcionales:
    PORT        - Puerto del servidor (default: 5000)
    BIND_ADDRESS- Dirección de bind (default: 0.0.0.0)
    WORKERS     - Número de workers Gunicorn (default: 4)
    TIMEOUT     - Timeout en segundos (default: 120)

Ejemplos:
    $0 start-dev
    PORT=8080 WORKERS=2 $0 start-prod
EOF
}

# Función principal
main() {
    local command="${1:-help}"
    
    case "$command" in
        start)
            if [[ "${FLASK_ENV:-production}" == "development" ]]; then
                start_dev
            else
                start_prod
            fi
            ;;
        start-dev)
            start_dev
            ;;
        start-prod)
            start_prod
            ;;
        stop)
            stop_server
            ;;
        status)
            check_status
            ;;
        restart)
            stop_server
            sleep 2
            if [[ "${FLASK_ENV:-production}" == "development" ]]; then
                start_dev
            else
                start_prod
            fi
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            error "Comando desconocido: $command"
            show_help
            exit 1
            ;;
    esac
}

# Ejecutar
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
