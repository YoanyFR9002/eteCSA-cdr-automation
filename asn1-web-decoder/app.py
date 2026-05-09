from flask import Flask, render_template, request, jsonify, Response, send_from_directory
import os
import json
import logging
import threading
import queue
from datetime import datetime
from core.asn1_decoder import ASN1Decoder, ASN1DecodeError

app = Flask(__name__)

# Configuración de directorios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
LOG_FOLDER = os.path.join(BASE_DIR, 'logs')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(LOG_FOLDER, exist_ok=True)

# Configuración de Logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_FOLDER, 'asn1_decoder.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Almacenamiento temporal de resultados (en memoria para demo)
# En producción usar Redis o DB
active_sessions = {}

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/api/decode', methods=['POST'])
def decode_cdr():
    """Endpoint principal de decodificación"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No se proporcionó archivo'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nombre de archivo vacío'}), 400
            
        # Obtener parámetros
        use_asn1 = request.form.get('use_asn1', 'false') == 'true'
        asn1_structure = None
        
        if use_asn1 and 'asn1_file' in request.files:
            asn1_file = request.files['asn1_file']
            if asn1_file.filename != '':
                try:
                    content = asn1_file.read().decode('utf-8')
                    asn1_structure = json.loads(content)
                    logger.info(f"Estructura ASN.1 cargada: {asn1_structure.get('name', 'Sin nombre')}")
                except json.JSONDecodeError as e:
                    return jsonify({'error': f'JSON ASN.1 inválido: {str(e)}'}), 400
        
        # Guardar archivo temporalmente
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{file.filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        logger.info(f"Archivo recibido: {filename} ({len(file.read())} bytes)")
        
        # Crear sesión de decodificación
        session_id = f"session_{timestamp}"
        active_sessions[session_id] = {
            'status': 'processing',
            'result': None,
            'error': None,
            'output': []
        }
        
        # Ejecutar en hilo separado
        thread = threading.Thread(
            target=process_decoding,
            args=(session_id, filepath, asn1_structure)
        )
        thread.start()
        
        return jsonify({
            'session_id': session_id,
            'message': 'Decodificación iniciada',
            'filename': filename
        })
        
    except Exception as e:
        logger.error(f"Error en decode_cdr: {str(e)}")
        return jsonify({'error': str(e)}), 500

def process_decoding(session_id: str, filepath: str, asn1_structure: dict):
    """Proceso de decodificación en segundo plano"""
    try:
        session = active_sessions[session_id]
        session['output'].append(f"[{datetime.now().strftime('%H:%M:%S')}] Iniciando decodificación...")
        
        decoder = ASN1Decoder()
        result = decoder.decode_file(filepath, asn1_structure)
        
        session['result'] = result
        session['status'] = 'completed'
        session['output'].append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Decodificación completada exitosamente")
        session['output'].append(f"[{datetime.now().strftime('%H:%M:%S')}] Campos encontrados: {len(result) if isinstance(result, list) else 'N/A'}")
        
        logger.info(f"Sesión {session_id} completada")
        
    except ASN1DecodeError as e:
        session = active_sessions[session_id]
        session['error'] = str(e)
        session['status'] = 'error'
        session['output'].append(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error de decodificación: {str(e)}")
        logger.error(f"Error ASN.1 en sesión {session_id}: {e}")
        
    except Exception as e:
        session = active_sessions[session_id]
        session['error'] = str(e)
        session['status'] = 'error'
        session['output'].append(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error crítico: {str(e)}")
        logger.error(f"Error crítico en sesión {session_id}: {e}")

@app.route('/api/status/<session_id>')
def get_status(session_id: str):
    """Obtener estado de la decodificación"""
    if session_id not in active_sessions:
        return jsonify({'error': 'Sesión no encontrada'}), 404
        
    session = active_sessions[session_id]
    return jsonify({
        'status': session['status'],
        'result': session['result'],
        'error': session['error'],
        'output': session['output']
    })

@app.route('/api/stream/<session_id>')
def stream_output(session_id: str):
    """Server-Sent Events para output en tiempo real"""
    def generate():
        if session_id not in active_sessions:
            yield f"data: {json.dumps({'error': 'Sesión no encontrada'})}\n\n"
            return
            
        session = active_sessions[session_id]
        last_len = 0
        
        while True:
            if len(session['output']) > last_len:
                new_lines = session['output'][last_len:]
                last_len = len(session['output'])
                for line in new_lines:
                    yield f"data: {json.dumps({'line': line})}\n\n"
            
            if session['status'] in ['completed', 'error']:
                yield f"data: {json.dumps({'done': True, 'status': session['status']})}\n\n"
                break
                
            # Limpiar sesiones antiguas después de 5 minutos
            # (implementación simplificada)
            import time
            time.sleep(0.5)
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/logs')
def get_logs():
    """Obtener lista de logs recientes"""
    try:
        log_files = sorted(
            [f for f in os.listdir(LOG_FOLDER) if f.endswith('.log')],
            reverse=True
        )[:10]
        
        logs = []
        for lf in log_files:
            filepath = os.path.join(LOG_FOLDER, lf)
            stats = os.stat(filepath)
            logs.append({
                'filename': lf,
                'size': stats.st_size,
                'modified': datetime.fromtimestamp(stats.st_mtime).isoformat()
            })
            
        return jsonify(logs)
    except Exception as e:
        logger.error(f"Error leyendo logs: {e}")
        return jsonify([]), 500

@app.route('/api/logs/<filename>')
def view_log(filename: str):
    """Ver contenido de un log específico"""
    try:
        filepath = os.path.join(LOG_FOLDER, filename)
        if not os.path.exists(filepath) or not filename.endswith('.log'):
            return jsonify({'error': 'Log no encontrado'}), 404
            
        with open(filepath, 'r') as f:
            content = f.read()
            
        return Response(content, mimetype='text/plain')
    except Exception as e:
        logger.error(f"Error leyendo log {filename}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Servir archivos estáticos"""
    return send_from_directory('static', filename)

if __name__ == '__main__':
    logger.info("="*60)
    logger.info("🚀 INICIANDO ASN1 WEB DECODER v1.0")
    logger.info("="*60)
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
