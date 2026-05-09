#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CDR Automation Web - Backend Flask
Permite ejecutar el script de reproceso CDR desde una interfaz web
"""

import os
import subprocess
import threading
import queue
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response

app = Flask(__name__)

# Configuración
SCRIPT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts', 'reproceso_web.sh')
LOG_DIR = '/var/opt/OCC/prueba-capana-error/LOGS_split'

# Cola para almacenar el estado de los procesos en ejecución
running_processes = {}

def validate_date(date_str):
    """Valida que la fecha tenga formato YYYYMMDD"""
    if not date_str:
        return True  # Permitir None para usar valor por defecto
    try:
        if len(date_str) != 8 or not date_str.isdigit():
            return False
        # Validar que sea una fecha real
        year = int(date_str[0:4])
        month = int(date_str[4:6])
        day = int(date_str[6:8])
        if month < 1 or month > 12:
            return False
        if day < 1 or day > 31:
            return False
        return True
    except (ValueError, IndexError):
        return False

def run_script(fecha_inicio, fecha_fin, process_id):
    """Ejecuta el script bash y captura la salida en tiempo real"""
    try:
        # Construir comando
        cmd = ['sudo', 'bash', SCRIPT_PATH]
        if fecha_inicio:
            cmd.append(fecha_inicio)
        if fecha_fin and fecha_fin != fecha_inicio:
            cmd.append(fecha_fin)
        
        # Iniciar proceso
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Almacenar referencia al proceso
        running_processes[process_id] = {
            'process': process,
            'start_time': datetime.now(),
            'status': 'running'
        }
        
        # Leer salida línea por línea
        output_lines = []
        for line in process.stdout:
            output_lines.append(line)
            # Pequeña pausa para permitir streaming
            thread_id = threading.current_thread().name
            if f"output_{process_id}" in running_processes:
                running_processes[f"output_{process_id}"].put(line)
        
        # Esperar a que termine
        process.wait()
        
        # Actualizar estado
        running_processes[process_id]['status'] = 'completed'
        running_processes[process_id]['end_time'] = datetime.now()
        running_processes[process_id]['return_code'] = process.returncode
        
        return {
            'success': process.returncode == 0,
            'return_code': process.returncode,
            'output': ''.join(output_lines),
            'duration': str(running_processes[process_id]['end_time'] - running_processes[process_id]['start_time'])
        }
        
    except Exception as e:
        running_processes[process_id]['status'] = 'error'
        return {
            'success': False,
            'error': str(e),
            'output': f"Error ejecutando script: {str(e)}"
        }
    finally:
        # Limpiar cola de output si existe
        if f"output_{process_id}" in running_processes:
            running_processes[f"output_{process_id}"].put(None)

@app.route('/')
def index():
    """Página principal con el formulario"""
    return render_template('index.html')

@app.route('/api/execute', methods=['POST'])
def execute():
    """Endpoint para iniciar la ejecución del script"""
    data = request.get_json()
    
    fecha_inicio = data.get('fecha_inicio', '').strip()
    fecha_fin = data.get('fecha_fin', '').strip()
    
    # Validar fechas
    if not validate_date(fecha_inicio):
        return jsonify({
            'success': False,
            'error': f'Formato de fecha inicio inválido: {fecha_inicio}. Use AAAAMMDD'
        }), 400
    
    if not validate_date(fecha_fin):
        return jsonify({
            'success': False,
            'error': f'Formato de fecha fin inválido: {fecha_fin}. Use AAAAMMDD'
        }), 400
    
    # Generar ID único para el proceso
    process_id = f"proc_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    
    # Iniciar hilo para ejecutar el script
    thread = threading.Thread(
        target=run_script,
        args=(fecha_inicio, fecha_fin, process_id),
        name=f"worker_{process_id}"
    )
    
    # Crear cola para output en tiempo real
    running_processes[f"output_{process_id}"] = queue.Queue()
    
    thread.start()
    
    return jsonify({
        'success': True,
        'process_id': process_id,
        'message': f'Proceso iniciado. Fechas: {fecha_inicio or "ayer"} -> {fecha_fin or fecha_inicio}'
    })

@app.route('/api/status/<process_id>')
def status(process_id):
    """Obtener estado del proceso"""
    if process_id not in running_processes:
        return jsonify({
            'success': False,
            'error': 'Proceso no encontrado'
        }), 404
    
    proc_info = running_processes[process_id]
    
    response = {
        'process_id': process_id,
        'status': proc_info['status'],
        'start_time': proc_info['start_time'].isoformat() if 'start_time' in proc_info else None
    }
    
    if proc_info['status'] != 'running':
        response['end_time'] = proc_info.get('end_time', '').isoformat() if proc_info.get('end_time') else None
        response['return_code'] = proc_info.get('return_code')
    
    return jsonify(response)

@app.route('/api/output/<process_id>')
def output_stream(process_id):
    """Stream de output en tiempo real"""
    def generate():
        output_queue = running_processes.get(f"output_{process_id}")
        if not output_queue:
            yield "data: Error: Cola de output no encontrada\n\n"
            return
        
        while True:
            try:
                line = output_queue.get(timeout=1)
                if line is None:
                    break
                # Escapar datos para SSE
                escaped_line = line.replace('\n', '\\n').replace('\r', '')
                yield f"data: {escaped_line}\n\n"
            except queue.Empty:
                # Verificar si el proceso terminó
                if process_id in running_processes and running_processes[process_id]['status'] != 'running':
                    break
                continue
            except Exception as e:
                yield f"data: Error reading output: {str(e)}\n\n"
                break
        
        yield "data: [END]\n\n"
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )

@app.route('/api/logs')
def get_logs():
    """Obtener lista de logs recientes"""
    try:
        if not os.path.exists(LOG_DIR):
            return jsonify({'logs': [], 'message': 'Directorio de logs no existe'})
        
        log_files = []
        for f in sorted(os.listdir(LOG_DIR), reverse=True)[:10]:  # Últimos 10 logs
            if f.endswith('.log') or f.endswith('.log.gz'):
                filepath = os.path.join(LOG_DIR, f)
                stat = os.stat(filepath)
                log_files.append({
                    'name': f,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        return jsonify({'logs': log_files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs/<filename>')
def view_log(filename):
    """Ver contenido de un log específico"""
    try:
        filepath = os.path.join(LOG_DIR, filename)
        if not os.path.exists(filepath) or not os.path.isfile(filepath):
            return jsonify({'error': 'Log no encontrado'}), 404
        
        # Prevenir path traversal
        if not filepath.startswith(LOG_DIR):
            return jsonify({'error': 'Acceso denegado'}), 403
        
        if filename.endswith('.gz'):
            import gzip
            with gzip.open(filepath, 'rt', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        else:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        
        return jsonify({'content': content, 'filename': filename})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("CDR Automation Web Server")
    print("=" * 60)
    print(f"Script path: {SCRIPT_PATH}")
    print(f"Log directory: {LOG_DIR}")
    print("=" * 60)
    print("Iniciando servidor en http://0.0.0.0:5000")
    print("Presione Ctrl+C para detener")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
