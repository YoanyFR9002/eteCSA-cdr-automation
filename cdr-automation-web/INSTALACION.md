# 📦 Guía de Instalación - CDR Automation Web

Esta guía paso a paso te permitirá instalar y configurar el proyecto **CDR Automation Web** en tu entorno local o servidor.

---

## 📋 Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:

- ✅ **Python 3.8 o superior**
- ✅ **pip** (gestor de paquetes de Python)
- ✅ **Bash** (entorno Linux/Unix recomendado)
- ✅ **Acceso a PostgreSQL** (para el script original)
- ✅ **Permisos sudo** (para ejecutar operaciones del sistema)

### Verificar instalaciones:

```bash
python3 --version
pip3 --version
bash --version
psql --version
```

---

## 🚀 Paso 1: Extraer el Proyecto

Si descargaste el archivo `.zip`:

```bash
# Descomprimir el archivo
unzip cdr-automation-web.zip

# Entrar al directorio
cd cdr-automation-web
```

Si clonaste desde Git:

```bash
git clone <url-del-repositorio>
cd cdr-automation-web
```

---

## 🔧 Paso 2: Instalar Dependencias de Python

El proyecto utiliza **Flask** para el servidor web.

```bash
# Crear entorno virtual (recomendado)
python3 -m venv venv

# Activar entorno virtual
# En Linux/Mac:
source venv/bin/activate

# En Windows:
# venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

**Verificación:**
```bash
pip list | grep Flask
# Debería mostrar: Flask 3.0.0
```

---

## 🔐 Paso 3: Configurar Permisos del Script

El script bash necesita permisos de ejecución y configuración sudo.

### 3.1 Dar permisos de ejecución:

```bash
chmod +x scripts/reproceso_web.sh
```

### 3.2 Configurar sudo sin contraseña (REQUERIDO):

El script necesita ejecutarse como usuario `etecsa` con privilegios elevados.

1. Ejecuta:
   ```bash
   sudo visudo
   ```

2. Agrega la siguiente línea al final del archivo (reemplaza `$USER` con tu usuario):

   ```bash
   $USER ALL=(ALL) NOPASSWD: /ruta/completa/cdr-automation-web/scripts/reproceso_web.sh
   ```

   **Ejemplo:**
   ```bash
   yoany ALL=(ALL) NOPASSWD: /home/yoany/proyectos/cdr-automation-web/scripts/reproceso_web.sh
   ```

3. Guarda y sale (`Ctrl+X`, luego `Y`, luego `Enter` en nano)

### 3.3 Verificar configuración sudo:

```bash
sudo -n /ruta/completa/scripts/reproceso_web.sh --help
# No debería pedir contraseña
```

---

## ⚙️ Paso 4: Configurar el Entorno (Opcional)

Si necesitas modificar las credenciales de base de datos o rutas:

### Opción A: Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```bash
# .env
DB_HOST=10.90.2.167
DB_PORT=5445
DB_NAME=mgrdb
DB_USER=mmsuper
DB_PASS=mediation
DIRECTORIO_DESTINO=/var/opt/OCC/prueba-capana-error
DESTINO=/var/opt/OCC/UGW_TEST/Capana/
EXPECTED_USER=etecsa
EXPECTED_GROUP=med
```

### Opción B: Editar el Script Directamente

Edita `scripts/reproceso_web.sh` y modifica las variables en la sección **CONFIGURACIÓN GENERAL**.

---

## 📁 Paso 5: Crear Directorios Requeridos

El script necesita ciertos directorios para funcionar:

```bash
# Crear directorios base (ajusta las rutas según tu entorno)
sudo mkdir -p /var/opt/OCC/prueba-capana-error
sudo mkdir -p /var/opt/OCC/prueba-capana-error/LOGS_split
sudo mkdir -p /var/opt/OCC/UGW_TEST/Capana/

# Asignar permisos
sudo chown -R $USER:$USER /var/opt/OCC/prueba-capana-error
sudo chmod 755 /var/opt/OCC/prueba-capana-error
```

---

## 🏃 Paso 6: Iniciar el Servidor Web

### Modo Desarrollo (Recomendado para pruebas):

```bash
# Desde el directorio del proyecto
python app.py
```

Verás algo como:
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://0.0.0.0:5000
Press CTRL+C to quit
```

### Modo Producción:

```bash
# Usando Gunicorn (requiere instalación adicional)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---

## 🌐 Paso 7: Acceder a la Interfaz Web

Abre tu navegador y ve a:

```
http://localhost:5000
```

O si estás en un servidor remoto:

```
http://<IP-del-servidor>:5000
```

---

## ✅ Paso 8: Probar la Aplicación

1. **Verifica la interfaz:**
   - Deberías ver el formulario con campos "Fecha Inicio" y "Fecha Fin"
   - El botón "🚀 Ejecutar Proceso Completo"

2. **Ejecuta una prueba:**
   - Ingresa fechas en formato AAAAMMDD (ej: `20240101`)
   - Haz clic en "Ejecutar Proceso Completo"
   - Observa la consola en tiempo real

3. **Verifica logs:**
   - Los logs se guardan en `/var/opt/OCC/prueba-capana-error/LOGS_split/`
   - También puedes verlos en la sección "📋 Logs Recientes"

---

## 🔍 Solución de Problemas

### ❌ Error: "Permission denied"

**Solución:**
```bash
# Verifica permisos del script
ls -la scripts/reproceso_web.sh

# Si no tiene ejecución:
chmod +x scripts/reproceso_web.sh

# Verifica configuración sudo
sudo -l | grep reproceso_web.sh
```

### ❌ Error: "No module named 'flask'"

**Solución:**
```bash
# Activa el entorno virtual
source venv/bin/activate

# Reinstala dependencias
pip install -r requirements.txt
```

### ❌ Error: "Connection refused" a PostgreSQL

**Solución:**
- Verifica que el servidor PostgreSQL esté corriendo
- Confirma que el host `10.90.2.167` sea accesible desde tu máquina
- Prueba conexión manual:
  ```bash
  PGPASSWORD=mediation psql -h 10.90.2.167 -p 5445 -U mmsuper -d mgrdb -c "SELECT 1;"
  ```

### ❌ Error: "No se puede escribir en LOG_DIR"

**Solución:**
```bash
# Crea el directorio manualmente
sudo mkdir -p /var/opt/OCC/prueba-capana-error/LOGS_split
sudo chown -R $USER:$USER /var/opt/OCC/prueba-capana-error/LOGS_split
```

### ❌ La interfaz no carga en navegadores remotos

**Solución:**
- Asegúrate de que el firewall permite el puerto 5000
- En AWS/Azure/GCP, agrega regla de seguridad para puerto 5000
- Usa `0.0.0.0:5000` en lugar de `localhost:5000`

---

## 📊 Estructura del Proyecto

```
cdr-automation-web/
├── app.py                      # Servidor Flask (Backend)
├── requirements.txt            # Dependencias Python
├── README.md                   # Documentación general
├── INSTALACION.md              # Esta guía
├── scripts/
│   └── reproceso_web.sh       # Script Bash adaptado
├── templates/
│   └── index.html             # Interfaz Web (Frontend)
└── static/                     # Archivos estáticos (CSS, JS, imágenes)
    ├── css/
    ├── js/
    └── images/
```

---

## 🔒 Consideraciones de Seguridad

⚠️ **IMPORTANTE:** Este proyecto ejecuta comandos del sistema con privilegios elevados.

### Para entornos de producción:

1. **Habilita autenticación:**
   - Agrega login con usuario/contraseña
   - Usa Flask-Login o JWT

2. **Usa HTTPS:**
   - Configura un proxy inverso con Nginx
   - Obtén certificado SSL (Let's Encrypt)

3. **Restringe acceso:**
   - Limita IPs permitidas
   - Usa firewall (iptables, ufw)

4. **Audita logs:**
   - Revisa regularmente `/var/opt/OCC/prueba-capana-error/LOGS_split/`
   - Implementa rotación de logs

5. **Minimiza privilegios:**
   - Crea un usuario dedicado para la aplicación
   - Restringe permisos solo a lo necesario

---

## 📞 Soporte

Si encuentras problemas:

1. Revisa los logs de la aplicación:
   ```bash
   tail -f /var/opt/OCC/prueba-capana-error/LOGS_split/capana_processor_*.log
   ```

2. Verifica los logs de Flask en la consola

3. Consulta la documentación del script original

---

## 🎉 ¡Listo!

Has completado la instalación. Ahora puedes:

- ✅ Ejecutar el proceso completo desde la interfaz web
- ✅ Monitorear el progreso en tiempo real
- ✅ Revisar logs históricos
- ✅ Automatizar el reproceso de archivos CDR

**URL de acceso:** http://localhost:5000

---

**Versión de la guía:** 1.0  
**Última actualización:** 2024  
**Autor:** Alexander Alonso Fuentes / Yoany Fuentes Ruiz
