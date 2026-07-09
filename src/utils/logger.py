"""
Sistema de logging con rotación para ASN.1 Web Decoder
"""

import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import os
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "asn1_decoder",
    log_level: str = "INFO",
    log_dir: str = "logs",
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
    console_output: bool = True
) -> logging.Logger:
    """
    Configura logger con rotación de archivos
    
    Args:
        name: Nombre del logger
        log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directorio para archivos de log
        max_bytes: Tamaño máximo antes de rotar
        backup_count: Número de backups a mantener
        console_output: Si True, output también a consola
    
    Returns:
        Logger configurado
    """
    # Crear directorio de logs si no existe
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Obtener logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Evitar duplicación de handlers
    if logger.handlers:
        return logger
    
    # Formato de log
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler de archivo con rotación por tamaño
    file_handler = RotatingFileHandler(
        log_path / f"{name}.log",
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Handler de archivo para errores (solo ERROR y CRITICAL)
    error_handler = RotatingFileHandler(
        log_path / f"{name}_errors.log",
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    
    # Handler de consola
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.WARNING)  # Solo warnings y arriba a consola
        logger.addHandler(console_handler)
    
    # Agregar handlers
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    
    return logger


def get_audit_logger(log_dir: str = "logs") -> logging.Logger:
    """
    Logger específico para auditoría de seguridad
    """
    audit_logger = logging.getLogger("asn1_audit")
    audit_logger.setLevel(logging.INFO)
    
    if audit_logger.handlers:
        return audit_logger
    
    # Formato especializado para auditoría
    formatter = logging.Formatter(
        'AUDIT | %(asctime)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Archivo de auditoría con rotación por tiempo (diario)
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    time_handler = TimedRotatingFileHandler(
        log_path / "audit.log",
        when='D',
        interval=1,
        backupCount=30,  # Mantener 30 días
        encoding='utf-8'
    )
    time_handler.setFormatter(formatter)
    time_handler.setLevel(logging.INFO)
    
    audit_logger.addHandler(time_handler)
    
    return audit_logger


def log_action(
    action: str,
    user: str = "anonymous",
    details: Optional[str] = None,
    success: bool = True
):
    """
    Registra acción para auditoría
    
    Args:
        action: Tipo de acción (UPLOAD, DECODE, EXPORT, etc.)
        user: Identificador de usuario
        details: Detalles adicionales
        success: Si la acción fue exitosa
    """
    audit_logger = get_audit_logger()
    
    status = "SUCCESS" if success else "FAILED"
    message = f"{action} | User: {user} | Status: {status}"
    if details:
        message += f" | Details: {details}"
    
    if success:
        audit_logger.info(message)
    else:
        audit_logger.warning(message)


def cleanup_old_logs(log_dir: str = "logs", days: int = 30):
    """
    Limpia logs antiguos
    
    Args:
        log_dir: Directorio de logs
        days: Días a mantener
    """
    import time
    from pathlib import Path
    
    log_path = Path(log_dir)
    if not log_path.exists():
        return
    
    cutoff_time = time.time() - (days * 24 * 60 * 60)
    
    for log_file in log_path.glob("*.log"):
        if log_file.stat().st_mtime < cutoff_time:
            try:
                log_file.unlink()
                logging.getLogger("asn1_decoder").info(f"Log eliminado: {log_file}")
            except Exception as e:
                logging.getLogger("asn1_decoder").error(f"Error eliminando log {log_file}: {e}")
