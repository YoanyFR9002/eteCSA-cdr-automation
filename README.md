# 🚀 ASN.1 Web Decoder v3.0 - Enterprise Edition

Decodificador web profesional de ASN.1/TLV para CDRs de telecomunicaciones.

## ✨ Características Principales

| Funcionalidad | Descripción |
|--------------|-------------|
| 🔍 **Búsqueda Inteligente** | Filtra por etiqueta, hex o contenido en tiempo real |
| 📊 **Estadísticas CDR** | Panel con tamaño, registros, octetos y tiempo |
| 🎨 **Mapa de Calor de Errores** | Resalta campos con errores en rojo intenso |
| 📥 **Exportación Multi-Formato** | `.txt`, `.json`, `.csv`, `.pcapng` (simulado) |
| 🧩 **Soporte Híbrido** | Auto-detect BER/DER/PER + esquemas JSON personalizados |
| 🛡️ **Seguridad y Logs** | Auditoría completa con rotación de logs |
| 📱 **UI Responsiva** | Modo oscuro, Split View Hex vs Decodificado |

## 📋 Requisitos

- Python 3.9+
- pip o poetry
- Docker (opcional, para producción)

## ⚡ Instalación Rápida

### Opción 1: Script automático (Recomendado)

```bash
./install.sh
./run.sh start-dev
```

### Opción 2: Manual

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
flask run --debug
```

### Opción 3: Docker

```bash
docker compose up -d
```

## 🌐 Uso

1. Acceder a `http://localhost:5000`
2. Cargar datos hex o archivo binario
3. Presionar "Decodificar"
4. Explorar resultados en vista dividida
5. Buscar y exportar

## 🔌 API Endpoints

- `GET /api/health` - Health check
- `POST /api/decode` - Decodifica datos ASN.1
- `POST /api/export` - Exporta a formato especificado
- `POST /api/validate` - Valida contra esquema

## 📝 Licencia

MIT License

## 👨‍💻 Autor

Alexander Alonso Fuentes  
Email: yoany.fuentes@etecsa.cu
