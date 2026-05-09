"""
Motor de decodificación ASN.1/TLV heurístico
Soporta BER, DER, PER auto-detectado
"""

import struct
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ASN1Decoder:
    """Decodificador heurístico de ASN.1 TLV (Tag-Length-Value)"""
    
    # Clases de tags ASN.1
    UNIVERSAL = 0x00
    APPLICATION = 0x40
    CONTEXT = 0x80
    PRIVATE = 0xC0
    
    # Tags universales comunes
    TAG_INTEGER = 0x02
    TAG_BIT_STRING = 0x03
    TAG_OCTET_STRING = 0x04
    TAG_NULL = 0x05
    TAG_OID = 0x06
    TAG_UTF8_STRING = 0x0C
    TAG_SEQUENCE = 0x30
    TAG_SET = 0x31
    TAG_PRINTABLE_STRING = 0x13
    TAG_IA5_STRING = 0x16
    TAG_UTC_TIME = 0x17
    TAG_GENERALIZED_TIME = 0x18
    
    def __init__(self):
        self.decoded_data: List[Dict] = []
        self.errors: List[Dict] = []
        self.stats = {
            "total_size": 0,
            "total_records": 0,
            "total_octets": 0,
            "decode_time_ms": 0
        }
    
    def detect_encoding(self, data: bytes) -> str:
        """Auto-detecta el formato de codificación (BER/DER/PER)"""
        if not data:
            return "UNKNOWN"
        
        # Intentar detectar por el primer tag
        first_byte = data[0]
        tag_class = (first_byte & 0xC0) >> 6
        constructed = (first_byte & 0x20) >> 4
        
        # BER/DER típicamente comienzan con tags construidos o primitivos válidos
        if tag_class in [0, 1, 2, 3]:
            if constructed or first_byte in [0x02, 0x03, 0x04, 0x05, 0x06, 0x0C, 0x13, 0x16, 0x17, 0x18]:
                # Verificar longitud válida
                if len(data) > 1:
                    length_byte = data[1]
                    if length_byte < 0x80:
                        return "BER"  # Longitud definida corta
                    elif length_byte == 0x80:
                        return "BER"  # Longitud indefinida
                    elif length_byte > 0x80 and length_byte <= 0x83:
                        return "DER"  # Longitud definida larga
                return "BER"
        
        # PER usualmente tiene estructura diferente
        return "BER"  # Default a BER como más común en CDRs
    
    def decode_tag(self, data: bytes, offset: int) -> Tuple[int, int, bool]:
        """
        Decodifica un tag ASN.1
        Returns: (tag_value, new_offset, is_constructed)
        """
        if offset >= len(data):
            raise ValueError("Offset fuera de rango al leer tag")
        
        first_byte = data[offset]
        tag_class = (first_byte & 0xC0) >> 6
        is_constructed = bool(first_byte & 0x20)
        tag_number = first_byte & 0x1F
        
        offset += 1
        
        # Tag de múltiples bytes si los 5 bits bajos son 11111
        if tag_number == 0x1F:
            tag_number = 0
            shift = 0
            while offset < len(data):
                byte = data[offset]
                offset += 1
                tag_number = (tag_number << 7) | (byte & 0x7F)
                if not (byte & 0x80):
                    break
        
        full_tag = (tag_class << 6) | (int(is_constructed) << 5) | tag_number
        return full_tag, offset, is_constructed
    
    def decode_length(self, data: bytes, offset: int) -> Tuple[int, int]:
        """
        Decodifica la longitud ASN.1
        Returns: (length_value, new_offset)
        """
        if offset >= len(data):
            raise ValueError("Offset fuera de rango al leer longitud")
        
        first_byte = data[offset]
        offset += 1
        
        if first_byte < 0x80:
            # Longitud corta (1 byte)
            return first_byte, offset
        elif first_byte == 0x80:
            # Longitud indefinida (solo BER)
            return -1, offset
        else:
            # Longitud larga (múltiples bytes)
            num_bytes = first_byte & 0x7F
            if num_bytes > 4:
                raise ValueError(f"Longitud demasiado grande: {num_bytes} bytes")
            
            if offset + num_bytes > len(data):
                raise ValueError("Datos insuficientes para leer longitud")
            
            length = 0
            for i in range(num_bytes):
                length = (length << 8) | data[offset + i]
            
            return length, offset + num_bytes
    
    def decode_value(self, data: bytes, offset: int, length: int, tag: int) -> Tuple[Any, int]:
        """Decodifica el valor según el tag"""
        if length == -1:
            # Longitud indefinida - buscar EOC (End of Contents)
            value_bytes = b""
            start = offset
            while offset < len(data):
                if data[offset:offset+2] == b'\x00\x00':
                    offset += 2
                    break
                value_bytes += bytes([data[offset]])
                offset += 1
            length = len(value_bytes)
        else:
            if offset + length > len(data):
                raise ValueError(f"Datos insuficientes: se necesitan {length} bytes desde offset {offset}")
            value_bytes = data[offset:offset + length]
            offset += length
        
        # Interpretar valor según tag
        value = self._interpret_value(value_bytes, tag)
        return value, offset
    
    def _interpret_value(self, value_bytes: bytes, tag: int) -> Any:
        """Interpreta los bytes del valor según el tipo de tag"""
        tag_number = tag & 0x1F
        
        try:
            if tag_number in [0x02, 0x0A, 0x0B]:  # INTEGER, REAL
                return int.from_bytes(value_bytes, 'big', signed=(value_bytes[0] & 0x80) if value_bytes else False)
            
            elif tag_number in [0x03]:  # BIT STRING
                if value_bytes:
                    unused_bits = value_bytes[0]
                    return {"unused_bits": unused_bits, "data": value_bytes[1:].hex()}
                return {"unused_bits": 0, "data": ""}
            
            elif tag_number in [0x04, 0x09]:  # OCTET STRING
                return value_bytes.hex()
            
            elif tag_number == 0x05:  # NULL
                return None
            
            elif tag_number == 0x06:  # OID
                return self._decode_oid(value_bytes)
            
            elif tag_number in [0x0C, 0x13, 0x14, 0x16, 0x1A, 0x1E]:  # Strings
                try:
                    return value_bytes.decode('utf-8', errors='replace')
                except:
                    return value_bytes.hex()
            
            elif tag_number == 0x17:  # UTCTime
                return self._decode_utc_time(value_bytes)
            
            elif tag_number == 0x18:  # GeneralizedTime
                return self._decode_generalized_time(value_bytes)
            
            elif tag_number in [0x10, 0x11, 0x30, 0x31]:  # SEQUENCE, SET
                return self._parse_nested(value_bytes)
            
            else:
                # Valor desconocido, retornar como hex
                return value_bytes.hex()
                
        except Exception as e:
            logger.warning(f"Error interpretando valor para tag {hex(tag)}: {e}")
            return value_bytes.hex()
    
    def _decode_oid(self, data: bytes) -> str:
        """Decodifica un Object Identifier"""
        if not data:
            return ""
        
        components = []
        first = data[0]
        components.append(first // 40)
        components.append(first % 40)
        
        value = 0
        for byte in data[1:]:
            value = (value << 7) | (byte & 0x7F)
            if not (byte & 0x80):
                components.append(value)
                value = 0
        
        return ".".join(str(c) for c in components)
    
    def _decode_utc_time(self, data: bytes) -> str:
        """Decodifica UTCTime (YYMMDDHHMMSSZ)"""
        try:
            time_str = data.decode('ascii', errors='replace')
            # Formato: YYMMDDHHMMSSZ
            if len(time_str) >= 12:
                year = int(time_str[0:2])
                year = 2000 + year if year < 50 else 1900 + year
                month = int(time_str[2:4])
                day = int(time_str[4:6])
                hour = int(time_str[6:8])
                minute = int(time_str[8:10])
                second = int(time_str[10:12])
                return f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}Z"
        except:
            pass
        return data.decode('ascii', errors='replace')
    
    def _decode_generalized_time(self, data: bytes) -> str:
        """Decodifica GeneralizedTime (YYYYMMDDHHMMSSZ)"""
        try:
            time_str = data.decode('ascii', errors='replace')
            if len(time_str) >= 14:
                return f"{time_str[0:4]}-{time_str[4:6]}-{time_str[6:8]}T{time_str[8:10]}:{time_str[10:12]}:{time_str[12:14]}Z"
        except:
            pass
        return data.decode('ascii', errors='replace')
    
    def _parse_nested(self, data: bytes) -> List[Dict]:
        """Parsea estructura nested (SEQUENCE/SET)"""
        result = []
        offset = 0
        while offset < len(data):
            try:
                item = self._decode_tlv(data, offset)
                if item:
                    result.append(item)
                    offset = item['end_offset']
                else:
                    break
            except Exception as e:
                logger.warning(f"Error parseando nested en offset {offset}: {e}")
                break
        return result
    
    def _decode_tlv(self, data: bytes, offset: int) -> Optional[Dict]:
        """Decodifica una unidad TLV completa"""
        start_offset = offset
        
        try:
            # Decodificar tag
            tag, offset, is_constructed = self.decode_tag(data, offset)
            
            # Decodificar longitud
            length, offset = self.decode_length(data, offset)
            
            # Guardar posición inicial del valor
            value_start = offset
            
            # Decodificar valor
            if is_constructed and length != -1:
                # Es construido - parsear contenido
                value = self._parse_nested(data[offset:offset + length]) if length > 0 else []
                offset += length
            else:
                value, offset = self.decode_value(data, offset, length, tag)
            
            return {
                "tag": f"0x{tag:02X}",
                "tag_decimal": tag,
                "tag_class": ["UNIVERSAL", "APPLICATION", "CONTEXT", "PRIVATE"][(tag >> 6) & 0x03],
                "constructed": is_constructed,
                "length": length if length >= 0 else "indefinite",
                "value": value,
                "hex": data[value_start:value_start + (length if length >= 0 else 0)].hex() if length >= 0 else "",
                "start_offset": start_offset,
                "end_offset": offset,
                "children": [] if is_constructed else None
            }
            
        except Exception as e:
            logger.error(f"Error decodificando TLV en offset {offset}: {e}")
            self.errors.append({
                "offset": offset,
                "error": str(e),
                "hex_context": data[offset:min(offset+16, len(data))].hex()
            })
            return None
    
    def decode(self, data: Union[bytes, str], encoding: str = "hex") -> Dict:
        """
        Decodifica datos ASN.1 completos
        
        Args:
            data: Datos en bytes o string hex
            encoding: "hex" o "bytes"
        
        Returns:
            Diccionario con resultados y estadísticas
        """
        start_time = datetime.now()
        
        # Convertir input a bytes
        if isinstance(data, str):
            if encoding == "hex":
                data = bytes.fromhex(data.replace(" ", "").replace(":", ""))
            else:
                data = data.encode('utf-8')
        
        self.stats["total_size"] = len(data)
        self.stats["total_octets"] = len(data)
        
        # Detectar encoding
        detected = self.detect_encoding(data)
        logger.info(f"Encoding detectado: {detected}")
        
        # Decodificar
        self.decoded_data = []
        self.errors = []
        offset = 0
        
        while offset < len(data):
            try:
                tlv = self._decode_tlv(data, offset)
                if tlv:
                    self.decoded_data.append(tlv)
                    offset = tlv['end_offset']
                    self.stats["total_records"] += 1
                else:
                    # Avanzar para evitar loop infinito
                    offset += 1
            except Exception as e:
                logger.error(f"Error en decode loop: {e}")
                self.errors.append({
                    "offset": offset,
                    "error": str(e),
                    "critical": True
                })
                break
        
        end_time = datetime.now()
        self.stats["decode_time_ms"] = (end_time - start_time).total_seconds() * 1000
        self.stats["encoding_detected"] = detected
        
        return {
            "success": len(self.errors) == 0,
            "data": self.decoded_data,
            "errors": self.errors,
            "stats": self.stats,
            "warnings": [e for e in self.errors if not e.get("critical", False)]
        }
    
    def decode_file(self, filepath: str) -> Dict:
        """Decodifica un archivo binario"""
        with open(filepath, 'rb') as f:
            data = f.read()
        return self.decode(data, encoding="bytes")
    
    def get_stats(self) -> Dict:
        """Retorna estadísticas de la última decodificación"""
        return self.stats.copy()
    
    def clear(self):
        """Limpia datos internos"""
        self.decoded_data = []
        self.errors = []
        self.stats = {
            "total_size": 0,
            "total_records": 0,
            "total_octets": 0,
            "decode_time_ms": 0
        }
