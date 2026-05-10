"""
Validador de esquemas ASN.1 personalizados
Soporta validación contra esquemas JSON
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SchemaValidator:
    """Validador de datos decodificados contra esquemas personalizados"""
    
    def __init__(self, schema: Optional[Dict] = None):
        self.schema = schema or {}
        self.validation_errors: List[Dict] = []
        self.validation_warnings: List[Dict] = []
    
    def load_schema(self, schema_path: str) -> bool:
        """Carga esquema desde archivo JSON"""
        try:
            with open(schema_path, 'r') as f:
                self.schema = json.load(f)
            logger.info(f"Esquema cargado: {schema_path}")
            return True
        except Exception as e:
            logger.error(f"Error cargando esquema: {e}")
            return False
    
    def load_schema_from_dict(self, schema_dict: Dict):
        """Carga esquema desde diccionario"""
        self.schema = schema_dict
    
    def validate(self, decoded_data: Dict) -> Dict:
        """
        Valida datos decodificados contra el esquema
        
        Returns:
            Diccionario con resultado de validación
        """
        self.validation_errors = []
        self.validation_warnings = []
        
        if not self.schema:
            logger.warning("No hay esquema cargado para validar")
            return {
                "valid": True,
                "errors": [],
                "warnings": [],
                "message": "Sin esquema - validación omitida"
            }
        
        data = decoded_data.get('data', [])
        self._validate_items(data, self.schema, path="root")
        
        return {
            "valid": len(self.validation_errors) == 0,
            "errors": self.validation_errors,
            "warnings": self.validation_warnings,
            "validated_at": datetime.now().isoformat(),
            "schema_version": self.schema.get('version', 'unknown')
        }
    
    def _validate_items(self, items: List[Dict], schema: Dict, path: str):
        """Valida lista de items contra esquema"""
        expected_fields = schema.get('fields', {})
        required_tags = schema.get('required', [])
        
        # Verificar tags requeridos
        found_tags = {item.get('tag'): item for item in items}
        
        for req_tag in required_tags:
            if req_tag not in found_tags:
                self.validation_errors.append({
                    "type": "missing_required",
                    "path": path,
                    "tag": req_tag,
                    "message": f"Tag requerido {req_tag} no encontrado en {path}"
                })
        
        # Validar cada campo
        for item in items:
            tag = item.get('tag')
            item_path = f"{path}.{tag}"
            
            if tag in expected_fields:
                field_schema = expected_fields[tag]
                self._validate_field(item, field_schema, item_path)
            
            # Validar hijos recursivamente
            if item.get('constructed'):
                children = item.get('children', []) or item.get('value', [])
                if children and isinstance(children, list):
                    child_schema = field_schema.get('children', {}) if tag in expected_fields else {}
                    self._validate_items(children, child_schema, item_path)
    
    def _validate_field(self, item: Dict, field_schema: Dict, path: str):
        """Valida un campo individual"""
        value = item.get('value')
        tag_class = item.get('tag_class')
        length = item.get('length')
        
        # Validar tipo
        expected_type = field_schema.get('type')
        if expected_type:
            if not self._check_type(value, expected_type):
                self.validation_errors.append({
                    "type": "type_mismatch",
                    "path": path,
                    "expected": expected_type,
                    "actual": type(value).__name__,
                    "message": f"Tipo incorrecto en {path}: esperado {expected_type}"
                })
        
        # Validar longitud mínima/máxima
        min_length = field_schema.get('min_length')
        max_length = field_schema.get('max_length')
        
        if isinstance(length, int):
            if min_length is not None and length < min_length:
                self.validation_errors.append({
                    "type": "length_too_short",
                    "path": path,
                    "expected_min": min_length,
                    "actual": length,
                    "message": f"Longitud muy corta en {path}: {length} < {min_length}"
                })
            
            if max_length is not None and length > max_length:
                self.validation_warnings.append({
                    "type": "length_exceeded",
                    "path": path,
                    "expected_max": max_length,
                    "actual": length,
                    "message": f"Longitud excedida en {path}: {length} > {max_length}"
                })
        
        # Validar valores permitidos (enum)
        allowed_values = field_schema.get('allowed_values', [])
        if allowed_values and value not in allowed_values:
            self.validation_errors.append({
                "type": "invalid_value",
                "path": path,
                "value": value,
                "allowed": allowed_values,
                "message": f"Valor no permitido en {path}: {value}"
            })
        
        # Validar patrón regex si está definido
        pattern = field_schema.get('pattern')
        if pattern:
            import re
            if not re.match(pattern, str(value)):
                self.validation_errors.append({
                    "type": "pattern_mismatch",
                    "path": path,
                    "pattern": pattern,
                    "value": str(value),
                    "message": f"Valor no coincide con patrón en {path}"
                })
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Verifica si el valor coincide con el tipo esperado"""
        type_map = {
            'integer': (int,),
            'string': (str,),
            'boolean': (bool,),
            'null': (type(None),),
            'array': (list,),
            'object': (dict,),
            'hex_string': (str,),  # Hex string
            'oid': (str,),  # Object Identifier
            'timestamp': (str,),  # ISO timestamp
        }
        
        expected_types = type_map.get(expected_type.lower())
        if not expected_types:
            return True  # Tipo desconocido, asumir válido
        
        return isinstance(value, expected_types)
    
    def validate_cdr_fields(self, decoded_data: Dict) -> Dict:
        """
        Validación específica para campos CDR de telecomunicaciones
        """
        errors = []
        warnings = []
        
        data = decoded_data.get('data', [])
        
        # Buscar campos comunes en CDRs
        found_fields = {}
        for item in data:
            tag = item.get('tag')
            value = item.get('value')
            found_fields[tag] = value
        
        # Validaciones específicas CDR
        # Ejemplo: verificar que haya timestamp
        timestamp_tags = ['0x17', '0x18']  # UTCTime, GeneralizedTime
        has_timestamp = any(tag in found_fields for tag in timestamp_tags)
        
        if not has_timestamp:
            warnings.append({
                "type": "cdr_missing_timestamp",
                "message": "CDR sin campo de timestamp detectado"
            })
        
        # Ejemplo: verificar que haya identificación de llamada
        call_id_tags = ['0x04', '0x30']  # OCTET STRING, SEQUENCE
        has_call_id = any(tag in found_fields for tag in call_id_tags)
        
        if not has_call_id:
            warnings.append({
                "type": "cdr_missing_call_id",
                "message": "CDR sin identificación de llamada detectada"
            })
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "cdr_validated": True
        }
    
    def get_summary(self) -> Dict:
        """Retorna resumen de validación"""
        return {
            "total_errors": len(self.validation_errors),
            "total_warnings": len(self.validation_warnings),
            "is_valid": len(self.validation_errors) == 0,
            "error_types": list(set(e.get('type', 'unknown') for e in self.validation_errors)),
            "warning_types": list(set(w.get('type', 'unknown') for w in self.validation_warnings))
        }
    
    def clear(self):
        """Limpia resultados de validación"""
        self.validation_errors = []
        self.validation_warnings = []
