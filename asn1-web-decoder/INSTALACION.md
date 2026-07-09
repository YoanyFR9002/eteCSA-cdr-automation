# 📘 Guía de Instalación - ASN.1 Web Decoder

## 📋 Descripción del Proyecto

**ASN.1 Web Decoder** es una aplicación web que permite decodificar archivos CDR binarios utilizando dos modos:

1. **Modo Estructurado ASN.1**: Utiliza una estructura ASN.1 definida (archivo JSON) para interpretar los datos.
2. **Modo Heurístico TLV**: En ausencia de estructura ASN.1, separa automáticamente los campos por etiquetas (Tag-Length-Value).

### Características Principales
- ✅ Interfaz web moderna con tema oscuro (escala de azules)
- ✅ Indicadores visuales de errores en rojo
- ✅ Decodificación en tiempo real con streaming de salida
- ✅ Sistema completo de registro de logs
- ✅ Visualización de resultados en tabla, JSON y hex dump
- ✅ Soporte para múltiples formatos de archivo binario

---

## 📁 Estructura del Proyecto

```
asn1-web-decoder/
├── app.py                      # Servidor Flask backend
├── requirements.txt            # Dependencias Python
├── README.md                   # Este archivo
├── core/
│   └── asn1_decoder.py        # Motor de decodificación ASN.1/TLV
├── templates/
│   └── index.html             # Interfaz web frontend
├── static/                     # Archivos estáticos (CSS, JS)
├── logs/                       # Directorio de logs (auto-generado)
└── uploads/                    # Archivos subidos (auto-generado)
```

---

## 🚀 Instalación Paso a Paso

### Requisitos Previos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Navegador web moderno (Chrome, Firefox, Edge)

### Paso 1: Extraer el Archivo Comprimido

```bash
# Descomprimir el archivo
tar -xzf asn1-web-decoder.tar.gz
cd asn1-web-decoder
```

### Paso 2: Crear Entorno Virtual (Recomendado)

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Linux/Mac:
source venv/bin/activate

# En Windows:
venv\Scripts\activate
```

### Paso 3: Instalar Dependencias

```bash
pip install -r requirements.txt
```

**Salida esperada:**
```
Collecting Flask==3.0.0
  Downloading flask-3.0.0-py3-none-any.whl
Collecting Werkzeug==3.0.1
  Downloading werkzeug-3.0.1-py3-none-any.whl
Successfully installed Flask-3.0.0 Werkzeug-3.0.1
```

### Paso 4: Verificar Estructura de Directorios

Asegúrate de que todos los archivos estén presentes:

```bash
ls -la
# Deberías ver: app.py, requirements.txt, core/, templates/, etc.

ls core/
# Deberías ver: asn1_decoder.py

ls templates/
# Deberías ver: index.html
```

### Paso 5: Iniciar la Aplicación

```bash
python app.py
```

**Salida esperada:**
```
============================================================
🚀 INICIANDO ASN1 WEB DECODER v1.0
============================================================
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://0.0.0.0:5000
```

### Paso 6: Acceder a la Aplicación Web

Abre tu navegador y ve a:
```
http://localhost:5000
```

---

## 💻 Cómo Usar la Aplicación

### Modo 1: Decodificación Heurística (Sin ASN.1)

1. Haz clic en **"Seleccionar archivo"** y elige tu archivo CDR binario (.bin, .dat, etc.)
2. Deja desmarcada la opción **"Usar estructura ASN.1 personalizada"**
3. Haz clic en **"Iniciar Decodificación"**
4. Observa el progreso en la consola en tiempo real
5. Visualiza los resultados en las pestañas: **Tabla**, **JSON**, o **Hex Dump**

### Modo 2: Decodificación con Estructura ASN.1

1. Selecciona tu archivo CDR binario
2. Marca la casilla **"Usar estructura ASN.1 personalizada"**
3. Aparecerá un nuevo campo: selecciona tu archivo JSON con la estructura ASN.1
4. Haz clic en **"Iniciar Decodificación"**
5. Revisa los resultados decodificados según la estructura proporcionada

### Formato de Archivo de Estructura ASN.1 (JSON)

```json
{
  "name": "Mi_Estructura_CDR",
  "version": "1.0",
  "fields": [
    {"tag": "0x02", "name": "IMSI", "type": "INTEGER"},
    {"tag": "0x04", "name": "MSISDN", "type": "OCTET_STRING"}
  ]
}
```

---

## 📊 Visualización de Logs

### Ver Logs desde la Interfaz Web
- La sección **"Registro de Logs"** muestra todos los archivos de log generados
- Haz clic en cualquier log para ver su contenido en la consola principal

### Ubicación de Logs en el Sistema
```
asn1-web-decoder/logs/asn1_decoder.log
```

### Comandos Útiles para Logs

```bash
# Ver últimas 50 líneas del log
tail -f logs/asn1_decoder.log

# Buscar errores en el log
grep "ERROR" logs/asn1_decoder.log

# Ver tamaño del log
ls -lh logs/
```

---

## 🔧 Configuración Avanzada

### Cambiar Puerto del Servidor

Edita `app.py` y modifica la última línea:
```python
app.run(host='0.0.0.0', port=8080, debug=True, threaded=True)
```

### Ejecutar en Producción (Sin Debug)

```bash
# Exportar variables de entorno
export FLASK_ENV=production

# Ejecutar sin debug
python app.py
```

### Usar Gunicorn (Producción)

```bash
# Instalar gunicorn
pip install gunicorn

# Ejecutar con gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---

## 🛠️ Solución de Problemas

### Error: "ModuleNotFoundError: No module named 'flask'"
```bash
# Asegúrate de estar en el directorio correcto y haber activado el venv
pip install -r requirements.txt
```

### Error: "Port 5000 already in use"
```bash
# Matar proceso usando el puerto 5000
lsof -ti:5000 | xargs kill -9

# O cambiar el puerto en app.py
```

### Error: "Permission denied" al escribir logs
```bash
# Dar permisos al directorio logs
chmod 755 logs/
```

### La interfaz no carga correctamente
```bash
# Limpiar caché del navegador (Ctrl+F5)
# Verificar que todos los archivos estén presentes
ls templates/index.html
```

### Decodificación falla con archivos grandes
- El modo heurístico puede tener dificultades con archivos >100MB
- Considera dividir el archivo o usar el modo estructurado con ASN.1

---

## 📝 Ejemplos de Uso

### Ejemplo 1: Decodificar CDR de Prueba

```bash
# Crear archivo binario de prueba (Python)
python3 -c "
data = bytes([0x02, 0x01, 0x05, 0x04, 0x03, 0x31, 0x32, 0x33])
with open('test_cdr.bin', 'wb') as f:
    f.write(data)
print('Archivo test_cdr.bin creado')
"

# Subir test_cdr.bin desde la interfaz web
```

### Ejemplo 2: Ver Logs en Tiempo Real

```bash
# En una terminal aparte
tail -f logs/asn1_decoder.log
```

### Ejemplo 3: Exportar Resultados

Después de decodificar:
1. Ve a la pestaña **JSON**
2. Copia el contenido
3. Guárdalo como `.json` para análisis posterior

---

## 🔐 Seguridad

### Recomendaciones para Producción

1. **No ejecutar con `debug=True`** en producción
2. **Usar HTTPS** con certificado SSL
3. **Implementar autenticación** de usuarios
4. **Limitar tamaño de archivos** subidos
5. **Configurar firewall** para permitir solo IPs autorizadas

### Ejemplo con Autenticación Básica

```python
from flask_httpauth import HTTPBasicAuth

auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    if username == "admin" and password == "tu_password_seguro":
        return True
    return False

@app.route('/')
@auth.login_required
def index():
    return render_template('index.html')
```

---

## 📞 Soporte

### Archivos de Log para Debugging
- `logs/asn1_decoder.log` - Log principal de la aplicación
- Consola del servidor - Errores de runtime

### Información para Reportar Bugs
Al reportar un problema, incluye:
1. Versión de Python (`python --version`)
2. Sistema operativo
3. Tamaño del archivo CDR
4. Captura de pantalla del error
5. Fragmento relevante del log

---

## 🎯 Próximas Mejoras (Roadmap)

- [ ] Soporte para esquemas ASN.1 completos (.asn files)
- [ ] Exportación de resultados a CSV/Excel
- [ ] Vista Hex Dump mejorada con edición
- [ ] Comparación de múltiples CDRs
- [ ] API REST completa para integración
- [ ] Autenticación de usuarios
- [ ] Base de datos para historial de decodificaciones

---

## 📄 Licencia

Este proyecto es de uso interno para análisis de CDRs telecom.

---

## 👨‍💻 Créditos

Desarrollado para análisis de CDRs en entornos Ericsson EMM | RHEL 7.9+

**Versión:** 1.0  
**Fecha:** 2024  
**Tecnologías:** Python 3, Flask, HTML5, CSS3, JavaScript
