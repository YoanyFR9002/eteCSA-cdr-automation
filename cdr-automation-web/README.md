# CDR Automation Web - Sistema de Reproceso Capana

Aplicación web para ejecutar el script de reproceso CDR de Ericsson EMM de forma interactiva y segura.

## 📁 Estructura del Proyecto

```
cdr-automation-web/
├── app.py                      # Servidor Flask backend
├── requirements.txt            # Dependencias Python
├── README.md                   # Este archivo
├── scripts/
│   └── reproceso_web.sh       # Script bash adaptado para web
└── templates/
    └── index.html             # Interfaz web frontend
```

## ⚙️ Requisitos Previos

1. **Python 3.6+** instalado
2. **PostgreSQL client** (`psql`) configurado y accesible
3. **Permisos sudo** para ejecutar el script como usuario `etecsa`
4. **Directorios existentes**:
   - `/var/opt/OCC/prueba-capana-error`
   - `/var/opt/OCC/UGW_TEST/Capana/`
   - `/var/opt/cubacel/archive/ugsn/`
   - `/var/opt/cubacel/archive/cgsn/`
   - `/var/opt/cubacel/archive/n_core_UGW/`

## 🚀 Instalación Rápida

### 1. Instalar dependencias Python

```bash
cd /workspace/cdr-automation-web
pip install -r requirements.txt
```

### 2. Configurar permisos sudo

Editar el archivo sudoers para permitir la ejecución del script sin password:

```bash
sudo visudo
```

Agregar la siguiente línea (reemplazar `$USER` con el usuario del servidor web):

```
$USER ALL=(ALL) NOPASSWD: /workspace/cdr-automation-web/scripts/reproceso_web.sh
$USER ALL=(etecsa) NOPASSWD: /usr/bin/python
```

### 3. Dar permisos de ejecución al script

```bash
chmod +x /workspace/cdr-automation-web/scripts/reproceso_web.sh
```

### 4. Crear directorios necesarios (si no existen)

```bash
sudo mkdir -p /var/opt/OCC/prueba-capana-error/LOGS_split
sudo mkdir -p /var/opt/OCC/UGW_TEST/Capana
sudo chown -R $USER:med /var/opt/OCC/prueba-capana-error
sudo chown -R $USER:med /var/opt/OCC/UGW_TEST/Capana
```

## ▶️ Ejecución

### Iniciar el servidor web:

```bash
cd /workspace/cdr-automation-web
python app.py
```

El servidor se iniciará en: **http://0.0.0.0:5000**

### Acceder a la interfaz:

Abrir un navegador web e ingresar a: `http://localhost:5000` o `http://<IP_DEL_SERVIDOR>:5000`

## 🎯 Funcionalidades

### Interfaz Web
- ✅ Formulario para seleccionar rango de fechas (formato AAAAMMDD)
- ✅ Consola en tiempo real con salida del script
- ✅ Barra de progreso animada
- ✅ Indicadores de estado (En ejecución, Completado, Error)
- ✅ Lista de logs recientes con vista previa
- ✅ Diseño responsive y moderno

### Backend
- ✅ Validación de fechas
- ✅ Ejecución asíncrona del script bash
- ✅ Streaming de output en tiempo real (Server-Sent Events)
- ✅ Gestión de múltiples procesos simultáneos
- ✅ Rotación automática de logs
- ✅ API RESTful para integración

## 🔧 Configuración

### Parámetros del Script (editar `scripts/reproceso_web.sh`)

```bash
# Base de datos
DB_HOST="10.90.2.167"
DB_PORT="5445"
DB_NAME="mgrdb"
DB_USER="mmsuper"
DB_PASS="mediation"

# Directorios
DIRECTORIO_DESTINO="/var/opt/OCC/prueba-capana-error"
DESTINO="/var/opt/OCC/UGW_TEST/Capana/"
LOG_DIR="/var/opt/OCC/prueba-capana-error/LOGS_split"

# Usuario y grupo esperados
EXPECTED_USER="etecsa"
EXPECTED_GROUP="med"
```

### Parámetros del Servidor (editar `app.py`)

```python
# Puerto del servidor
app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
```

## 📊 API Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Interfaz web principal |
| POST | `/api/execute` | Iniciar proceso de reproceso |
| GET | `/api/status/<process_id>` | Obtener estado del proceso |
| GET | `/api/output/<process_id>` | Stream de output en tiempo real |
| GET | `/api/logs` | Listar logs recientes |
| GET | `/api/logs/<filename>` | Ver contenido de un log |

### Ejemplo de uso de la API

```bash
# Iniciar proceso
curl -X POST http://localhost:5000/api/execute \
  -H "Content-Type: application/json" \
  -d '{"fecha_inicio": "20240115", "fecha_fin": "20240116"}'

# Verificar estado
curl http://localhost:5000/api/status/proc_20240115_120000_123456
```

## 🔐 Consideraciones de Seguridad

1. **Autenticación**: Esta versión no incluye autenticación. Para producción, agregar:
   - Login con usuario/contraseña
   - Tokens de sesión
   - HTTPS obligatorio

2. **Firewall**: Restringir acceso al puerto 5000 solo a IPs autorizadas

3. **Logs**: Los logs contienen información sensible. Asegurar permisos adecuados:
   ```bash
   chmod 750 /var/opt/OCC/prueba-capana-error/LOGS_split
   chmod 640 /var/opt/OCC/prueba-capana-error/LOGS_split/*.log
   ```

## 🛠️ Solución de Problemas

### El script no se ejecuta
- Verificar permisos sudo: `sudo -l`
- Verificar que `psql` esté instalado y accesible
- Verificar conectividad a la base de datos

### Error de conexión a la BD
- Verificar credenciales en `reproceso_web.sh`
- Verificar firewall y acceso a puerto 5445
- Probar conexión manual: `psql -h 10.90.2.167 -p 5445 -U mmsuper -d mgrdb`

### La interfaz web no carga
- Verificar que Flask esté instalado: `pip list | grep Flask`
- Verificar que el puerto 5000 no esté en uso: `netstat -tlnp | grep 5000`
- Revisar logs de error en la consola

## 📝 Notas Importantes

- El script original fue adaptado para recibir parámetros por línea de comandos
- Los colores ANSI se desactivan automáticamente cuando no hay TTY
- El proceso se ejecuta en segundo plano para no bloquear la interfaz
- Los logs se rotan automáticamente cada 2GB o después de 30 días

## 📄 Licencia

Uso interno exclusivo - ETECSA

---

**Versión**: 1.0  
**Fecha**: 2024  
**Autor**: Sistema generado automáticamente
