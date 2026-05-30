# 🌍 Quinela Mundial FIFA 2026

Sistema completo para predicciones del Mundial de Fútbol FIFA 2026. Incluye frontend HTML y backend Node.js con envío de predicciones por email en ZIP encriptado.

## 📁 Estructura del Proyecto

```
quinela-mundial-2026/
├── frontend/
│   └── index.html          ← Aplicación web de predicciones
├── backend/
│   ├── server.js           ← Servidor Node.js
│   ├── package.json        ← Dependencias
│   └── .env                ← Variables de entorno (configurar)
└── README.md               ← Este archivo
```

## 🚀 Instalación y Configuración

### 1. Instalar Node.js
Si no lo tienes instalado, descarga desde: https://nodejs.org

### 2. Configurar el Backend

```bash
cd quinela-mundial-2026/backend
npm install
```

### 3. Configurar Variables de Entorno

Edita `backend/.env` con tus credenciales:

```env
PORT=3000
EMAIL_SERVICE=gmail
EMAIL_USER=tu_email@gmail.com
EMAIL_PASS=tu_contraseña_de_aplicacion
RECIPIENTS=yoany.fuentes@etecsa.cu,jorge.diaz@etecsa.cu
DEFAULT_ZIP_PASSWORD=Ok12345*
```

> ⚠️ **Para Gmail**: Usa una "Contraseña de aplicación" desde https://myaccount.google.com/apppasswords

### 4. Iniciar el Servidor

```bash
cd backend
npm start
```

Verás:
```
✅ Servidor Quinela corriendo en http://localhost:3000
📧 Emails configurados para: yoany.fuentes@etecsa.cu, jorge.diaz@etecsa.cu
```

### 5. Abrir el Frontend

Opciones:
- **Opción A**: Abre `frontend/index.html` directamente en tu navegador
- **Opción B**: Accede a http://localhost:3000 desde tu navegador (el backend sirve el frontend)

## 📋 Características

### Frontend
- ✅ Interfaz moderna y responsive
- ✅ 12 grupos con 6 equipos cada uno
- ✅ Predicción de clasificados (1°, 2°, 3°)
- ✅ Fase eliminatoria completa (Octavos, Cuartos, Semifinal, Final)
- ✅ Premios individuales (Goleador, Asistidor, Balón de Oro)
- ✅ Guardado local automático
- ✅ Conexión al backend para envío por email

### Backend
- ✅ API REST con Express
- ✅ Creación de ZIP encriptado con AES-256
- ✅ Envío de emails con Nodemailer
- ✅ Generación de archivo TXT con formato legible
- ✅ CORS habilitado para conexiones cruzadas

## 🔧 Endpoints de la API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/submit` | Envía predicción y recibe ZIP encriptado por email |
| POST | `/api/ranking` | Procesa datos de ranking (opcional) |
| GET | `/` | Sirve el frontend HTML |

## 📦 Formato del ZIP

El archivo ZIP contiene:
- `NombreUsuario_Quinela2026.txt` - Predicciones en formato legible
- Encriptado con contraseña: `Ok12345*` (configurable)

## 🛠️ Desarrollo

### Modo desarrollo (con auto-reload):
```bash
cd backend
npm run dev
```

### Cambiar puerto:
Edita `.env` y modifica `PORT=3000`

## 🚀 Despliegue en Producción

### Render/Railway
1. Conecta tu repositorio GitHub
2. Detecta automáticamente Node.js
3. Comando de inicio: `npm start`
4. Configura variables de entorno en la plataforma

### Docker
```bash
docker build -t quinela-mundial-2026 .
docker run -p 3000:3000 --env-file backend/.env quinela-mundial-2026
```

### VPS con PM2
```bash
npm install -g pm2
pm2 start backend/server.js --name quinela
pm2 save
pm2 startup
```

## 👨‍💻 Autor

**Ing. Yoany Fuentes Ruíz**

## 📄 Licencia

MIT

---

¡Disfruta prediciendo el Mundial 2026! ⚽🏆
