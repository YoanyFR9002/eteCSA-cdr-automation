"""
Módulo de exportación multi-formato
Soporta: TXT, JSON, CSV, PCAPNG (simulado)
"""

import json
import csv
import io
from typing import Dict, List, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Exporter:
    """Exportador de datos decodificados a múltiples formatos"""
    
    def __init__(self, decoded_data: Dict):
        self.decoded_data = decoded_data
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def to_txt(self, include_hex: bool = True, indent: int = 2) -> str:
        """Exporta a formato texto legible"""
        output = io.StringIO()
        
        output.write("=" * 80 + "\n")
        output.write("ASN.1 WEB DECODER v3.0 - Reporte de Decodificación\n")
        output.write("=" * 80 + "\n")
        output.write(f"Fecha: {datetime.now().isoformat()}\n")
        output.write(f"Encoding detectado: {self.decoded_data.get('stats', {}).get('encoding_detected', 'N/A')}\n")
        output.write("\n")
        
        # Estadísticas
        stats = self.decoded_data.get('stats', {})
        output.write("-" * 40 + "\n")
        output.write("ESTADÍSTICAS\n")
        output.write("-" * 40 + "\n")
        output.write(f"Tamaño total: {stats.get('total_size', 0)} bytes\n")
        output.write(f"Registros: {stats.get('total_records', 0)}\n")
        output.write(f"Tiempo de decodificación: {stats.get('decode_time_ms', 0):.2f} ms\n")
        output.write("\n")
        
        # Errores
        errors = self.decoded_data.get('errors', [])
        if errors:
            output.write("-" * 40 + "\n")
            output.write("ERRORES ENCONTRADOS\n")
            output.write("-" * 40 + "\n")
            for i, error in enumerate(errors, 1):
                output.write(f"{i}. Offset {error.get('offset', 'N/A')}: {error.get('error', 'Unknown')}\n")
                if error.get('hex_context'):
                    output.write(f"   Contexto hex: {error['hex_context']}\n")
            output.write("\n")
        
        # Datos decodificados
        output.write("-" * 40 + "\n")
        output.write("DATOS DECODIFICADOS\n")
        output.write("-" * 40 + "\n")
        
        data = self.decoded_data.get('data', [])
        self._write_tree_txt(output, data, indent, include_hex)
        
        output.write("\n" + "=" * 80 + "\n")
        output.write("FIN DEL REPORTE\n")
        output.write("=" * 80 + "\n")
        
        return output.getvalue()
    
    def _write_tree_txt(self, output: io.StringIO, items: List[Dict], indent: int, include_hex: bool, level: int = 0):
        """Escribe árbol de datos en formato texto"""
        prefix = "  " * level
        
        for item in items:
            tag = item.get('tag', 'N/A')
            tag_class = item.get('tag_class', 'N/A')
            length = item.get('length', 'N/A')
            value = item.get('value', '')
            constructed = item.get('constructed', False)
            
            output.write(f"{prefix}[{tag}] ({tag_class})")
            if isinstance(length, int):
                output.write(f" Len={length}")
            else:
                output.write(f" Len={length}")
            
            if constructed:
                output.write(" [CONSTRUIDO]\n")
                children = item.get('children', []) or item.get('value', [])
                if children and isinstance(children, list):
                    self._write_tree_txt(output, children, indent, include_hex, level + 1)
            else:
                output.write(f": {value}\n")
                if include_hex and item.get('hex'):
                    output.write(f"{prefix}  Hex: {item['hex']}\n")
    
    def to_json(self, pretty: bool = True) -> str:
        """Exporta a JSON"""
        if pretty:
            return json.dumps(self.decoded_data, indent=2, default=str)
        return json.dumps(self.decoded_data, default=str)
    
    def to_csv(self, include_nested: bool = False) -> str:
        """Exporta a CSV plano"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'Level', 'Tag', 'Tag_Class', 'Tag_Decimal', 
            'Length', 'Value', 'Hex', 'Offset_Start', 'Offset_End'
        ])
        
        data = self.decoded_data.get('data', [])
        self._write_csv_rows(writer, data, 0, include_nested)
        
        return output.getvalue()
    
    def _write_csv_rows(self, writer: csv.writer, items: List[Dict], level: int, include_nested: bool):
        """Escribe filas CSV"""
        for item in items:
            row = [
                level,
                item.get('tag', ''),
                item.get('tag_class', ''),
                item.get('tag_decimal', ''),
                item.get('length', ''),
                str(item.get('value', '')),
                item.get('hex', ''),
                item.get('start_offset', ''),
                item.get('end_offset', '')
            ]
            writer.writerow(row)
            
            # Incluir nested si se solicita
            if include_nested and item.get('constructed'):
                children = item.get('children', []) or item.get('value', [])
                if children and isinstance(children, list):
                    self._write_csv_rows(writer, children, level + 1, include_nested)
    
    def to_pcapng(self) -> bytes:
        """
        Exporta a PCAPNG (simulado)
        Nota: Implementación básica para compatibilidad
        """
        # PCAPNG Section Header Block
        section_header = bytes([
            0x0A, 0x0D, 0x0D, 0x0A,  # Block Type
            0x1C, 0x00, 0x00, 0x00,  # Block Length
            0x1A, 0x2B, 0x3C, 0x4D,  # Byte Order Magic
            0x01, 0x00,              # Major Version
            0x00, 0x00,              # Minor Version
            0xFF, 0xFF, 0xFF, 0xFF,  # Section Length (unspecified)
            0x00, 0x00, 0x00, 0x00,  # Options (none)
            0x1C, 0x00, 0x00, 0x00   # Block Length (repeat)
        ])
        
        # Interface Description Block
        interface_block = bytes([
            0x01, 0x00, 0x00, 0x00,  # Block Type
            0x14, 0x00, 0x00, 0x00,  # Block Length
            0x01, 0x00,              # LinkType (Ethernet)
            0x00, 0x00,              # Reserved
            0x65, 0x00, 0x00, 0x00,  # Snaplen
            0x00, 0x00, 0x00, 0x00,  # Options
            0x14, 0x00, 0x00, 0x00   # Block Length (repeat)
        ])
        
        # Enhanced Packet Block con datos ASN.1
        data_bytes = self._get_raw_data()
        packet_length = len(data_bytes)
        enhanced_packet = (
            bytes([
                0x06, 0x00, 0x00, 0x00,  # Block Type
                0x00, 0x00, 0x00, 0x00,  # Block Length (se calculará)
                0x00, 0x00, 0x00, 0x00,  # Interface ID
                0x00, 0x00, 0x00, 0x00,  # Timestamp high
                0x00, 0x00, 0x00, 0x00,  # Timestamp low
                packet_length & 0xFFFFFFFF,  # Captured Length
                packet_length & 0xFFFFFFFF,  # Original Length
            ]) +
            data_bytes +
            bytes([0x00] * ((4 - (packet_length % 4)) % 4)) +  # Padding
            bytes([0x00, 0x00, 0x00, 0x00])  # Options
        )
        
        # Calcular longitud del bloque
        block_length = len(enhanced_packet)
        enhanced_packet = (
            enhanced_packet[:4] +
            block_length.to_bytes(4, 'little') +
            enhanced_packet[8:-4] +
            block_length.to_bytes(4, 'little')
        )
        
        return section_header + interface_block + enhanced_packet
    
    def _get_raw_data(self) -> bytes:
        """Obtiene datos raw del payload decodificado"""
        # Intentar reconstruir datos desde el valor decodificado
        data = self.decoded_data.get('data', [])
        raw = b""
        
        for item in data:
            hex_value = item.get('hex', '')
            if hex_value:
                try:
                    raw += bytes.fromhex(hex_value)
                except:
                    pass
        
        return raw if raw else b"\x00" * 16  # Dummy data si no hay hex
    
    def export(self, format: str = "txt", **kwargs) -> str:
        """
        Exporta al formato especificado
        
        Args:
            format: "txt", "json", "csv", "pcapng"
            **kwargs: Argumentos específicos del formato
        
        Returns:
            String con los datos exportados (bytes para pcapng)
        """
        exporters = {
            "txt": self.to_txt,
            "json": self.to_json,
            "csv": self.to_csv,
            "pcapng": self.to_pcapng
        }
        
        if format not in exporters:
            raise ValueError(f"Formato no soportado: {format}. Use: {list(exporters.keys())}")
        
        logger.info(f"Exportando a formato {format}")
        return exporters[format](**kwargs)
    
    def save_to_file(self, filepath: str, format: str = "txt", **kwargs):
        """Guarda exportación a archivo"""
        content = self.export(format, **kwargs)
        
        mode = 'wb' if format == 'pcapng' else 'w'
        with open(filepath, mode) as f:
            f.write(content)
        
        logger.info(f"Archivo guardado: {filepath}")
        return filepath
