#!/bin/bash
# ============================================================================
# SCRIPT: reproceso_web.sh (Versión adaptada para Web)
# VERSIÓN: 1.0
# ENTORNO: Ericsson EMM v20 | RHEL 7.9 | PostgreSQL 10+
# ============================================================================
set -uo pipefail

# ========================================
# CONFIGURACIÓN GENERAL
# ========================================
DB_HOST="10.90.2.167"
DB_PORT="5445"
DB_NAME="mgrdb"
DB_USER="mmsuper"
DB_PASS="mediation"

DIRECTORIO_DESTINO="/var/opt/OCC/prueba-capana-error"
DESTINO="/var/opt/OCC/UGW_TEST/Capana/"
LOG_DIR="/var/opt/OCC/prueba-capana-error/LOGS_split"

EXPECTED_USER="etecsa"
EXPECTED_GROUP="med"
umask 0022

MAX_LOG_SIZE_MB=2048
MAX_LOG_FILES=7
LOG_RETENTION_DAYS=30

# Colores seguros para RHEL 7.9 (se desactivan en modo web si no hay TTY)
if tput colors &>/dev/null && [[ -t 1 ]]; then
    RED='\033[0;31m'; GREEN='\033[0;32m'
    YELLOW='\033[1;33m'; BLUE='\033[0;34m'
    NC='\033[0m'
else
    RED=''; GREEN=''; YELLOW=''; BLUE=''; NC=''
fi

# Íconos ASCII
CHECK="[OK]"; CROSS="[ERR]"; WAIT="[...]"; SEARCH="[~]"
DB_ICON="[DB]"; PY="[PY]"; MV="[MV]"; LOG="[LOG]"; EXIT="[X]"; STAR="[*]"

FECHA_INICIO="${1:-}"
FECHA_FIN="${2:-$FECHA_INICIO}"
ARCHIVOS_COPIADOS=0
ARCHIVOS_ERROR=0

# ========================================
# LOGGING
# ========================================
mkdir -p "$LOG_DIR" 2>/dev/null || true
LOG_FILE="${LOG_DIR}/capana_processor_web_$(date +%Y%m%d_%H%M%S).log"
touch "$LOG_FILE" 2>/dev/null || { echo "ERROR: No se puede escribir en $LOG_DIR"; exit 1; }
chmod 640 "$LOG_FILE" 2>/dev/null || true

get_timestamp() { date +"%Y-%m-%d %H:%M:%S"; }

log_message() {
    local level="$1" message="$2"
    echo "[$(get_timestamp)] [$level] $message" | tee -a "$LOG_FILE"
}

# ========================================
# PROGRESO Y SPINNER
# ========================================
show_progress() {
    local current="$1" total="$2" label="${3:-Procesando}"
    [[ "$total" -eq 0 ]] && total=1
    local percent=$(( current * 100 / total ))
    local filled=$(( percent / 2 ))
    local empty=$(( 50 - filled ))
    printf "\r[%s%s] %s %3d%% (%d/%d)" \
        "$(printf '%*s' "$filled" | tr ' ' '#')" \
        "$(printf '%*s' "$empty" | tr ' ' '-')" \
        "$label" "$percent" "$current" "$total"
    [[ $current -ge $total ]] && printf "\n"
}

show_spinner() {
    local pid=$1 msg="${2:-Procesando}"
    local spin='|/-\\'
    local i=0
    while kill -0 "$pid" 2>/dev/null; do
        local idx=$(( i % ${#spin} ))
        printf "\r%s%s%s %s" "${YELLOW}" "${spin:$idx:1}" "${NC}" "$msg"
        ((i++)) || true
        sleep 0.1
    done
    printf "\r%s%s%s %s completado\n" "${GREEN}" "${CHECK}" "${NC}" "$msg"
}

# ========================================
# ROTACIÓN DE LOGS
# ========================================
rotate_log_by_size() {
    local max_bytes=$((MAX_LOG_SIZE_MB * 1024 * 1024))
    if [[ -f "$LOG_FILE" ]]; then
        local size; size=$(stat -c%s "$LOG_FILE" 2>/dev/null | tr -d '[:space:]')
        size=${size:-0}
        if (( size >= max_bytes )); then
            local ts; ts=$(date +%Y%m%d_%H%M%S)
            mv "$LOG_FILE" "${LOG_FILE}.${ts}" && gzip "${LOG_FILE}.${ts}" 2>/dev/null || true
            touch "$LOG_FILE" && chmod 640 "$LOG_FILE"
        fi
    fi
}
cleanup_old_logs() { find "$LOG_DIR" -name "*.log.*.gz" -type f -mtime +$LOG_RETENTION_DAYS -delete 2>/dev/null || true; }
limit_log_files() {
    local count; count=$(ls -1 "$LOG_DIR"/*.log.*.gz 2>/dev/null | wc -l | tr -d '[:space:]')
    count=${count:-0}
    if (( count > MAX_LOG_FILES )); then
        local to_del=$((count - MAX_LOG_FILES))
        ls -1t "$LOG_DIR"/*.log.*.gz 2>/dev/null | tail -n "$to_del" | xargs -r rm -f 2>/dev/null || true
    fi
}
perform_log_rotation() { rotate_log_by_size; cleanup_old_logs; limit_log_files; }

ensure_dir() {
    local dir="$1"
    [[ -d "$dir" ]] || mkdir -p "$dir" 2>/dev/null || { log_message "ERROR" "No se pudo crear $dir"; return 1; }
    chmod 755 "$dir" 2>/dev/null || true
    chown "${EXPECTED_USER}:${EXPECTED_GROUP}" "$dir" 2>/dev/null || true
}

# ========================================
# FUNCIÓN: Rango de fechas
# ========================================
get_date_range() {
    local start="$1" end="$2"
    local current="$start"
    while [[ "$current" < "$end" || "$current" == "$end" ]]; do
        echo "$current"
        current=$(date -d "$current + 1 day" +%Y%m%d 2>/dev/null) || break
        [[ -z "$current" ]] && break
    done
}

# ========================================
# FUNCIÓN 1: RECUPERAR ARCHIVOS POR FECHA
# ========================================
recuperar_archivos_db() {
    echo ""
    echo "+--------------------------------------------+"
    echo "|  ${DB_ICON} RECUPERAR ARCHIVOS POR RANGO DE FECHA |"
    echo "+--------------------------------------------+"
    
    # Validar fechas
    if [[ -z "$FECHA_INICIO" ]]; then
        FECHA_INICIO=$(date -d "yesterday" +%Y%m%d)
        echo "${WAIT} Usando fecha por defecto (ayer): $FECHA_INICIO"
    fi
    
    if [[ -z "$FECHA_FIN" ]]; then
        FECHA_FIN="$FECHA_INICIO"
    fi
    
    if [[ ! "$FECHA_INICIO" =~ ^[0-9]{8}$ ]]; then
        echo "${CROSS} Formato invalido FECHA_INICIO. Use AAAAMMDD"
        return 1
    fi
    
    if [[ ! "$FECHA_FIN" =~ ^[0-9]{8}$ ]]; then
        echo "${CROSS} Formato invalido FECHA_FIN. Use AAAAMMDD"
        return 1
    fi
    
    echo "${CHECK} Rango: $FECHA_INICIO -> $FECHA_FIN"
    
    local IDS_COMPLETOS=(52713 52714 52716 52717 52756 52757 52758 52759 56109 56127 56128 56129 56133 56135 56136 56137 56141 56143 56146 78548 78549 78550 78551 78552 78553 78554 78555 78556 52757 52758 52759)
    local IDS_SQL=$(printf "'%%%s%%'," "${IDS_COMPLETOS[@]}" | sed 's/,$//')
    local ARRAY_SQL="ARRAY[$IDS_SQL]"
    
    local TEMP_RESULTS=$(mktemp)
    local TEMP_NAMES=$(mktemp)
    trap "rm -f '$TEMP_RESULTS' '$TEMP_NAMES'" EXIT
    
    log_message "INFO" "Ejecutando consulta SQL para rango: $FECHA_INICIO - $FECHA_FIN"
    echo "${WAIT} Consultando base de datos..."
    
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -A -c "
    SELECT TRIM(SUBSTRING(alarm_source_address FROM 'File: (.*)')) ||
    CASE
      WHEN alarm_source_address LIKE '%52713%' THEN ':52713' WHEN alarm_source_address LIKE '%52714%' THEN ':52714'
      WHEN alarm_source_address LIKE '%52716%' THEN ':52716' WHEN alarm_source_address LIKE '%52717%' THEN ':52717'
      WHEN alarm_source_address LIKE '%52756%' THEN ':52756' WHEN alarm_source_address LIKE '%52757%' THEN ':52757'
      WHEN alarm_source_address LIKE '%52758%' THEN ':52758' WHEN alarm_source_address LIKE '%52759%' THEN ':52759'
      WHEN alarm_source_address LIKE '%56109%' THEN ':56109' WHEN alarm_source_address LIKE '%56127%' THEN ':56127'
      WHEN alarm_source_address LIKE '%56128%' THEN ':56128' WHEN alarm_source_address LIKE '%56129%' THEN ':56129'
      WHEN alarm_source_address LIKE '%56133%' THEN ':56133' WHEN alarm_source_address LIKE '%56135%' THEN ':56135'
      WHEN alarm_source_address LIKE '%56136%' THEN ':56136' WHEN alarm_source_address LIKE '%56137%' THEN ':56137'
      WHEN alarm_source_address LIKE '%56141%' THEN ':56141' WHEN alarm_source_address LIKE '%56143%' THEN ':56143'
      WHEN alarm_source_address LIKE '%56146%' THEN ':56146' WHEN alarm_source_address LIKE '%78548%' THEN ':78548'
      WHEN alarm_source_address LIKE '%78549%' THEN ':78549' WHEN alarm_source_address LIKE '%78550%' THEN ':78550'
      WHEN alarm_source_address LIKE '%78551%' THEN ':78551' WHEN alarm_source_address LIKE '%78552%' THEN ':78552'
      WHEN alarm_source_address LIKE '%78553%' THEN ':78553' WHEN alarm_source_address LIKE '%78554%' THEN ':78554'
      WHEN alarm_source_address LIKE '%78555%' THEN ':52755' WHEN alarm_source_address LIKE '%78556%' THEN ':78556'
      WHEN alarm_source_address LIKE '%78557%' THEN ':78557' WHEN alarm_source_address LIKE '%78558%' THEN ':78558'
      WHEN alarm_source_address LIKE '%78559%' THEN ':78559' ELSE ''
    END
    FROM mm_alarmlog WHERE alarm_source_address LIKE ANY ($ARRAY_SQL) AND alarm_id = '303';" > "$TEMP_RESULTS" 2>/dev/null &
    
    local sql_pid=$!
    show_spinner "$sql_pid" "Consulta SQL"
    
    if [[ ! -s "$TEMP_RESULTS" ]]; then
        log_message "WARN" "Sin resultados en la BD."
        echo "${YELLOW}[!] No se encontraron registros.${NC}"
        return 1
    fi
    
    local total_reg; total_reg=$(wc -l < "$TEMP_RESULTS" | tr -d '[:space:]')
    log_message "INFO" "Registros SQL encontrados: $total_reg"
    echo "${CHECK} Encontrados: $total_reg registros"
    
    awk -F':' '{print $1}' "$TEMP_RESULTS" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | sort -u > "$TEMP_NAMES"
    
    ARCHIVOS_COPIADOS=0
    ARCHIVOS_ERROR=0
    local total_encontrados=$(wc -l < "$TEMP_NAMES" | tr -d '[:space:]')
    local proceso_actual=0
    
    echo "${SEARCH} Buscando archivos en rango de fechas..."
    
    for fecha_busqueda in $(get_date_range "$FECHA_INICIO" "$FECHA_FIN"); do
        log_message "INFO" "Buscando en fecha: $fecha_busqueda"
        local RUTAS=(
          "/var/opt/cubacel/archive/ugsn/$fecha_busqueda"
          "/var/opt/cubacel/archive/cgsn/$fecha_busqueda"
          "/var/opt/cubacel/archive/n_core_UGW/$fecha_busqueda"
        )
        
        for ruta in "${RUTAS[@]}"; do
            [[ -d "$ruta" ]] || continue
            mapfile -t carpetas < <(find "$ruta" -mindepth 1 -maxdepth 1 -type d \( -iname "*LTE*" -o -iname "*APR8*" \) 2>/dev/null)
            [[ ${#carpetas[@]} -eq 0 ]] && continue
            
            for carpeta in "${carpetas[@]}"; do
                while IFS= read -r fname; do
                    [[ -z "$fname" ]] && continue
                    ((proceso_actual++)) || true
                    show_progress "$proceso_actual" "$total_encontrados" "Copiando"
                    
                    local full="${carpeta}/${fname}"
                    [[ -f "$full" ]] || continue
                    if cp -p "$full" "${DIRECTORIO_DESTINO}/" 2>/dev/null; then
                        ((ARCHIVOS_COPIADOS++)) || true
                    else
                        ((ARCHIVOS_ERROR++)) || true
                        log_message "WARN" "Fallo copiando: $fname"
                    fi
                done < <(find "$carpeta" -maxdepth 1 -type f \( -name "APR8*" -o -name "*:*" \) -printf "%f\n" 2>/dev/null | grep -F -f "$TEMP_NAMES" 2>/dev/null)
            done
        done
    done
    printf "\n"
    
    log_message "INFO" "Copia finalizada: Copiados=$ARCHIVOS_COPIADOS | Errores=$ARCHIVOS_ERROR"
    echo "${CHECK} Copiados: $ARCHIVOS_COPIADOS | Errores: $ARCHIVOS_ERROR"
    return 0
}

# ========================================
# FUNCIÓN 2: PYTHON
# ========================================
ejecutar_python() {
    echo ""
    echo "+--------------------------------------------+"
    echo "|  ${PY} EJECUTAR SCRIPT PYTHON               |"
    echo "+--------------------------------------------+"
    
    local PYTHON_SCRIPT="${DIRECTORIO_DESTINO}/roaming_fixer2.7.py"
    [[ ! -f "$PYTHON_SCRIPT" ]] && { echo "${CROSS} No se encontro: $PYTHON_SCRIPT"; return 1; }
    
    cd "$DIRECTORIO_DESTINO" || return 1
    
    echo "${YELLOW}[~] Preparando archivos...${NC}"
    for f in *; do
        [[ -f "$f" && ( "$f" == *APR8* || "$f" == *:* ) && "$f" != *.gz ]] && mv -- "$f" "${f}.gz" 2>/dev/null
    done
    
    echo "${YELLOW}[~] Descomprimiendo...${NC}"
    gzip -d *.gz 2>/dev/null || true
    local archivos_listos; archivos_listos=$(ls -1 2>/dev/null | wc -l | tr -d '[:space:]')
    echo "${CHECK} Archivos listos: $archivos_listos"
    
    chmod 755 "$PYTHON_SCRIPT" 2>/dev/null || true
    echo "${YELLOW}[~] Ejecutando Python...${NC}"
    if sudo -u "$EXPECTED_USER" python "$PYTHON_SCRIPT" >> "$LOG_FILE" 2>&1; then
        echo "${CHECK} Python ejecutado OK"
    else
        python "$PYTHON_SCRIPT" >> "$LOG_FILE" 2>&1 || { echo "${CROSS} Python fallo"; return 1; }
    fi
    return 0
}

# ========================================
# FUNCIÓN 3: MOVER Y PERMISOS
# ========================================
mover_y_permisos() {
    echo ""
    echo "+--------------------------------------------+"
    echo "|  ${MV} MOVER ARCHIVOS Y AJUSTAR PERMISOS    |"
    echo "+--------------------------------------------+"
    
    echo "${YELLOW}[~] Moviendo APR8* a $DESTINO...${NC}"
    [[ -d "${DIRECTORIO_DESTINO}/out/" ]] && mv -t "$DESTINO" "${DIRECTORIO_DESTINO}/out/APR8"* 2>/dev/null || true
    
    if [[ -d "$DESTINO" ]]; then
        cd "$DESTINO" || return 1
        for f in APR8*; do
            [[ -f "$f" ]] || continue
            chmod 644 "$f" 2>/dev/null || true
            chown "${EXPECTED_USER}:${EXPECTED_GROUP}" "$f" 2>/dev/null || true
        done
        local total; total=$(ls APR8* 2>/dev/null | wc -l | tr -d '[:space:]')
        echo "${CHECK} Permisos aplicados a $total archivos"
    fi
    return 0
}

# ========================================
# MAIN (Modo Web - Sin menú interactivo)
# ========================================
main() {
    for d in "$LOG_DIR" "$DIRECTORIO_DESTINO" "$DESTINO"; do ensure_dir "$d" || exit 1; done
    log_message "INFO" "=== Inicio ejecución WEB ==="
    
    echo "=============================================="
    echo " INICIANDO PROCESO AUTOMATIZADO"
    echo " Fechas: $FECHA_INICIO -> $FECHA_FIN"
    echo "=============================================="
    
    recuperar_archivos_db
    if [[ $? -ne 0 ]]; then
        echo "${CROSS} Error en la fase de recuperación de archivos"
        exit 1
    fi
    
    ejecutar_python
    if [[ $? -ne 0 ]]; then
        echo "${CROSS} Error en la fase de procesamiento Python"
        exit 1
    fi
    
    mover_y_permisos
    if [[ $? -ne 0 ]]; then
        echo "${CROSS} Error en la fase de movimiento de archivos"
        exit 1
    fi
    
    perform_log_rotation
    echo ""
    echo "=============================================="
    echo " PROCESO COMPLETADO EXITOSAMENTE"
    echo "=============================================="
    log_message "INFO" "=== Fin ejecución WEB ==="
    exit 0
}

main
