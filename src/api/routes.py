"""
API Flask para ASN.1 Web Decoder
Endpoints principales
"""

from flask import Blueprint, request, jsonify, send_file, render_template, current_app
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
import logging

from src.asn1_decoder import ASN1Decoder, Exporter, SchemaValidator
from src.utils.logger import setup_logger, log_action
from src.utils.config import Config

# Crear blueprint
api = Blueprint('api', __name__, url_prefix='/api')
logger = setup_logger()


@api.route('/health')
def health_check():
    """Endpoint de salud para healthchecks"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "3.0.0"
    })


@api.route('/decode', methods=['POST'])
def decode():
    """
    Decodifica datos ASN.1
    
    Accepts:
        - hex_data: string hex en form data o JSON
        - file: archivo binario
    
    Returns:
        JSON con datos decodificados
    """
    try:
        decoder = ASN1Decoder()
        
        # Verificar si viene archivo
        if 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                return jsonify({"error": "No se seleccionó archivo"}), 400
            
            filename = secure_filename(file.filename)
            file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            
            # Leer datos del archivo
            file_data = file.read()
            
            # Si es archivo hex, convertir
            if file_extension == 'hex' or file_extension == 'txt':
                hex_string = file_data.decode('utf-8').strip()
                result = decoder.decode(hex_string, encoding="hex")
            else:
                result = decoder.decode(file_data, encoding="bytes")
            
            log_action("DECODE_FILE", details=f"File: {filename}, Size: {len(file_data)} bytes")
        
        # Verificar si viene JSON con hex_data
        elif request.is_json:
            data = request.get_json()
            hex_data = data.get('hex_data', '')
            
            if not hex_data:
                return jsonify({"error": "hex_data requerido en JSON"}), 400
            
            result = decoder.decode(hex_data, encoding="hex")
            log_action("DECODE_HEX", details=f"Size: {len(hex_data)} chars")
        
        # Verificar form data
        elif 'hex_data' in request.form:
            hex_data = request.form['hex_data']
            result = decoder.decode(hex_data, encoding="hex")
            log_action("DECODE_FORM", details=f"Size: {len(hex_data)} chars")
        
        else:
            return jsonify({"error": "Datos no válidos. Use 'file' o 'hex_data'"}), 400
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error en decode: {e}")
        log_action("DECODE_ERROR", details=str(e), success=False)
        return jsonify({"error": str(e)}), 500


@api.route('/export', methods=['POST'])
def export():
    """
    Exporta datos decodificados a formato especificado
    
    Request JSON:
        - decoded_data: datos decodificados
        - format: "txt", "json", "csv", "pcapng"
    
    Returns:
        Archivo para descarga
    """
    try:
        data = request.get_json()
        
        decoded_data = data.get('decoded_data')
        export_format = data.get('format', 'txt').lower()
        
        if not decoded_data:
            return jsonify({"error": "decoded_data requerido"}), 400
        
        if export_format not in ['txt', 'json', 'csv', 'pcapng']:
            return jsonify({"error": f"Formato no soportado: {export_format}"}), 400
        
        # Crear exporter y exportar
        exporter = Exporter(decoded_data)
        content = exporter.export(export_format)
        
        # Generar nombre de archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"asn1_export_{timestamp}.{export_format}"
        
        # Guardar temporalmente
        filepath = os.path.join(current_app.config['EXPORT_FOLDER'], filename)
        
        mode = 'wb' if export_format == 'pcapng' else 'w'
        with open(filepath, mode) as f:
            f.write(content)
        
        log_action("EXPORT", details=f"Format: {export_format}, File: {filename}")
        
        # Enviar archivo
        return send_file(
            filepath,
            mimetype='application/octet-stream' if export_format == 'pcapng' else 'text/plain',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        logger.error(f"Error en export: {e}")
        log_action("EXPORT_ERROR", details=str(e), success=False)
        return jsonify({"error": str(e)}), 500


@api.route('/validate', methods=['POST'])
def validate():
    """
    Valida datos decodificados contra esquema
    
    Request JSON:
        - decoded_data: datos decodificados
        - schema: esquema JSON (opcional)
    
    Returns:
        Resultado de validación
    """
    try:
        data = request.get_json()
        
        decoded_data = data.get('decoded_data')
        schema = data.get('schema')
        
        if not decoded_data:
            return jsonify({"error": "decoded_data requerido"}), 400
        
        validator = SchemaValidator()
        
        # Cargar esquema si se proporciona
        if schema:
            validator.load_schema_from_dict(schema)
        
        # Validar
        result = validator.validate(decoded_data)
        
        # Validación específica CDR
        cdr_result = validator.validate_cdr_fields(decoded_data)
        result['cdr_validation'] = cdr_result
        
        log_action("VALIDATE", details=f"Valid: {result['valid']}")
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error en validate: {e}")
        log_action("VALIDATE_ERROR", details=str(e), success=False)
        return jsonify({"error": str(e)}), 500


@api.route('/stats', methods=['GET'])
def get_stats():
    """Retorna estadísticas de uso (placeholder)"""
    return jsonify({
        "total_decodes": 0,
        "total_exports": 0,
        "average_decode_time_ms": 0,
        "uptime": "N/A"
    })


@api.route('/upload', methods=['POST'])
def upload_file():
    """
    Sube archivo para procesamiento posterior
    
    Returns:
        ID de archivo subido
    """
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Generar ID único
        file_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        # Guardar archivo
        save_filename = f"{file_id}.{extension}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], save_filename)
        file.save(filepath)
        
        log_action("UPLOAD", details=f"File: {filename}, ID: {file_id}")
        
        return jsonify({
            "file_id": file_id,
            "filename": filename,
            "size": os.path.getsize(filepath),
            "path": save_filename
        })
    
    except Exception as e:
        logger.error(f"Error en upload: {e}")
        log_action("UPLOAD_ERROR", details=str(e), success=False)
        return jsonify({"error": str(e)}), 500


# Crear app Flask principal
def create_app(config_class=Config):
    """Factory function para crear aplicación Flask"""
    from flask import Flask
    
    app = Flask(__name__)
    
    # Cargar configuración
    config = config_class()
    config.init_app(app)
    
    # Registrar blueprints
    app.register_blueprint(api)
    
    # Ruta principal
    @app.route('/')
    def index():
        """Sirve la página principal"""
        return render_template('index.html')
    
    return app


# Instancia de app para Gunicorn
app = create_app()


if __name__ == '__main__':
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
