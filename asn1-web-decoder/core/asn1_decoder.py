#!/usr/bin/env python3
# ============================================================================
# SCRIPT: asn1_decoder.py
# VERSIÓN: 1.0
# DESCRIPCIÓN: Motor de decodificación ASN.1 y TLV heurístico para CDRs
# ENTORNO: Python 3.8+ | Web Flask
# ============================================================================

import struct
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

# Configuración de Logs
logger = logging.getLogger(__name__)

class ASN1DecodeError(Exception):
    """Excepción personalizada para errores de decodificación"""
    pass

class ASN1Decoder:
    """
    Decodificador híbrido: Soporta estructuras ASN.1 definidas y 
    modo heurístico TLV (Tag-Length-Value) cuando no hay esquema.
    """
    
    # Clases ASN.1
    CLASS_UNIVERSAL = 0
    CLASS_APPLICATION = 1
    CLASS_CONTEXT = 2
    CLASS_PRIVATE = 3
    
    # Tipos Universales Comunes
    UNIVERSAL_TYPES = {
        0: 'RESERVED', 1: 'BOOLEAN', 2: 'INTEGER', 3: 'BIT_STRING',
        4: 'OCTET_STRING', 5: 'NULL', 6: 'OBJECT_IDENTIFIER', 7: 'ObjectDescriptor',
        8: 'EXTERNAL', 9: 'REAL', 10: 'ENUMERATED', 11: 'EMBEDDED_PDV',
        12: 'UTF8String', 13: 'RELATIVE_OID', 14: 'SEQUENCE', 15: 'SET',
        16: 'NumericString', 17: 'PrintableString', 18: 'T61String', 19: 'VideotexString',
        20: 'IA5String', 21: 'UTCTime', 22: 'GeneralizedTime', 23: 'GraphicString',
        24: 'VisibleString', 25: 'GeneralString', 26: 'UniversalString',
        28: 'BMPString'
    }
    
    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self.offset = 0
        self.data = b''
        
    def decode_file(self, file_path: str, asn1_structure: Optional[Dict] = None) -> Dict:
        """
        Decodifica un archivo binario.
        Si asn1_structure es None, usa modo heurístico TLV.
        """
        logger.info(f"Iniciando decodificación de: {file_path}")
        logger.info(f"Modo: {'ESTRUCTURADO' if asn1_structure else 'HEURÍSTICO (TLV)'}")
        
        try:
            with open(file_path, 'rb') as f:
                self.data = f.read()
            
            if len(self.data) == 0:
                raise ASN1DecodeError("El archivo está vacío")
                
            self.offset = 0
            
            if asn1_structure:
                result = self._decode_structured(asn1_structure)
            else:
                result = self._decode_heuristic()
                
            logger.info(f"Decodificación completada. Tamaño: {len(self.data)} bytes")
            return result
            
        except FileNotFoundError:
            logger.error(f"Archivo no encontrado: {file_path}")
            raise
        except Exception as e:
            logger.error(f"Error crítico en decodificación: {str(e)}")
            raise ASN1DecodeError(f"Fallo en decodificación: {str(e)}")

    def _decode_tag(self) -> Tuple[int, int, int]:
        """Decodifica la etiqueta (Tag): retorna (clase, construido, tipo)"""
        if self.offset >= len(self.data):
            raise ASN1DecodeError("Fin de datos inesperado al leer Tag")
            
        first_byte = self.data[self.offset]
        self.offset += 1
        
        tag_class = (first_byte >> 6) & 0x03
        is_constructed = bool((first_byte >> 5) & 0x01)
        tag_number = first_byte & 0x1F
        
        # Tags largos (>30)
        if tag_number == 0x1F:
            tag_number = 0
            while True:
                if self.offset >= len(self.data):
                    raise ASN1DecodeError("Fin de datos en Tag largo")
                next_byte = self.data[self.offset]
                self.offset += 1
                tag_number = (tag_number << 7) | (next_byte & 0x7F)
                if not (next_byte & 0x80):
                    break
                    
        return tag_class, is_constructed, tag_number

    def _decode_length(self) -> int:
        """Decodifica la longitud (Length)"""
        if self.offset >= len(self.data):
            raise ASN1DecodeError("Fin de datos inesperado al leer Length")
            
        first_byte = self.data[self.offset]
        self.offset += 1
        
        if first_byte < 0x80:
            return first_byte
        elif first_byte == 0x80:
            raise ASN1DecodeError("Longitud indefinida no soportada")
        else:
            num_bytes = first_byte & 0x7F
            if num_bytes > 4:
                raise ASN1DecodeError(f"Longitud demasiado grande: {num_bytes} bytes")
                
            length = 0
            for _ in range(num_bytes):
                if self.offset >= len(self.data):
                    raise ASN1DecodeError("Fin de datos leyendo longitud")
                length = (length << 8) | self.data[self.offset]
                self.offset += 1
            return length

    def _decode_value(self, length: int, tag_type: int, is_constructed: bool) -> Any:
        """Decodifica el valor (Value) según el tipo"""
        if self.offset + length > len(self.data):
            raise ASN1DecodeError("Datos insuficientes para el valor")
            
        value_data = self.data[self.offset:self.offset + length]
        self.offset += length
        
        if is_constructed:
            # Es una estructura anidada, recursividad básica
            nested = []
            temp_decoder = ASN1Decoder()
            temp_decoder.data = value_data
            temp_decoder.offset = 0
            while temp_decoder.offset < len(value_data):
                try:
                    nested.append(temp_decoder._decode_item())
                except:
                    break
            return nested
        
        # Tipos primitivos
        if tag_type in [1, 2, 10]:  # BOOLEAN, INTEGER, ENUMERATED
            try:
                val = int.from_bytes(value_data, byteorder='big', signed=True)
                return val
            except:
                return value_data.hex()
        elif tag_type in [3]:  # BIT STRING
            return {'bits': len(value_data)*8, 'hex': value_data.hex()}
        elif tag_type in [4, 12, 16, 17, 20, 24]:  # OCTET STRING, Strings varios
            try:
                return value_data.decode('utf-8', errors='replace')
            except:
                return value_data.hex()
        elif tag_type == 5:  # NULL
            return None
        elif tag_type == 6:  # OID
            return self._decode_oid(value_data)
        elif tag_type in [21, 22]:  # Time
            return value_data.decode('ascii', errors='replace')
        else:
            return value_data.hex()

    def _decode_oid(self, data: bytes) -> str:
        """Decodifica un Object Identifier"""
        if len(data) == 0:
            return ""
        first = data[0]
        oid = [first // 40, first % 40]
        value = 0
        for byte in data[1:]:
            value = (value << 7) | (byte & 0x7F)
            if not (byte & 0x80):
                oid.append(value)
                value = 0
        return ".".join(map(str, oid))

    def _decode_item(self) -> Dict:
        """Decodifica un item TLV completo"""
        start_offset = self.offset
        tag_class, is_constructed, tag_number = self._decode_tag()
        length = self._decode_length()
        value = self._decode_value(length, tag_number, is_constructed)
        
        type_name = self.UNIVERSAL_TYPES.get(tag_number, f'TAG_{tag_number}')
        if tag_class != self.CLASS_UNIVERSAL:
            type_name = f"[CLASS_{tag_class}]_{type_name}"
            
        return {
            'offset': start_offset,
            'tag': f"0x{tag_number:02X}",
            'type': type_name,
            'constructed': is_constructed,
            'length': length,
            'value': value
        }

    def _decode_heuristic(self) -> List[Dict]:
        """
        Modo Heurístico: Recorre el binario intentando identificar patrones TLV
        sin necesidad de esquema ASN.1 previo.
        """
        results = []
        self.offset = 0
        
        logger.info("Iniciando análisis heurístico TLV...")
        
        while self.offset < len(self.data):
            try:
                item = self._decode_item()
                results.append(item)
                logger.debug(f"Tag encontrado: {item['tag']} ({item['type']}) Len: {item['length']}")
            except ASN1DecodeError as e:
                logger.warning(f"Fin de secuencia válida en offset {self.offset}: {e}")
                # Intentar sincronizar buscando siguiente tag válido
                self.offset += 1
                # Si fallan muchos seguidos, romper
                if self.offset + 10 > len(self.data):
                    break
            except Exception as e:
                logger.error(f"Error inesperado en offset {self.offset}: {e}")
                break
                
        return results

    def _decode_structured(self, structure: Dict) -> Dict:
        """
        Decodificación basada en una estructura ASN.1 definida (JSON Schema).
        """
        # Implementación simplificada para demo
        # En producción, esto parsearía un schema completo
        logger.info("Usando estructura definida (Simulación)")
        result = {
            'structure_used': structure.get('name', 'Desconocido'),
            'fields': self._decode_heuristic() # Fallback a heurístico por ahora
        }
        return result
