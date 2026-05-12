# Roger 🏛️

**Chatbot de Arquitectura Empresarial y Gobierno del Dato — IDEAM**

Bot de Telegram que permite consultar la base de conocimiento de arquitectura empresarial del IDEAM, incluyendo datos maestros, diccionario de datos, y flujos de información.

## Arquitectura

- **Runtime**: Google Cloud Run (Python/Flask)
- **Base de Conocimiento**: Cloud Firestore
- **IA**: Vertex AI (Gemini 2.0 Flash)
- **Imágenes**: Cloud Storage
- **Interfaz**: Telegram Bot API

## Comandos

| Comando | Descripción |
|---------|-------------|
| `/start` | Bienvenida |
| `/help` | Ayuda |
| `/tablas` | Lista datos maestros OSPA |
| `/diccionario <tabla>` | Variables de una tabla |
| `/flujos` | Flujos de información |
| `/buscar <término>` | Búsqueda global |
| Texto libre | Respuesta con IA (RAG) |

## Despliegue

```bash
# 1. Configurar proyecto GCP
gcloud config set project roger-496113

# 2. Habilitar APIs
gcloud services enable run.googleapis.com firestore.googleapis.com aiplatform.googleapis.com storage.googleapis.com secretmanager.googleapis.com

# 3. Ingestar datos
python -m scripts.ingest_data
python -m scripts.upload_images

# 4. Desplegar
gcloud run deploy roger-bot --source . --region us-central1 --allow-unauthenticated --set-env-vars "TELEGRAM_TOKEN=<token>,GCP_PROJECT_ID=roger-496113"

# 5. Configurar webhook
curl "<CLOUD_RUN_URL>/set-webhook?url=<CLOUD_RUN_URL>"
```

## Estructura

```
Roger/
├── app/
│   ├── __init__.py
│   ├── main.py              # Flask server + webhook
│   ├── config.py             # Configuration
│   ├── bot_handler.py        # Telegram command handlers
│   ├── knowledge_service.py  # Firestore queries
│   ├── ai_service.py         # Vertex AI (Gemini)
│   └── prompts/
│       └── system_prompt.py  # IDEAM-specific system prompt
├── scripts/
│   ├── ingest_data.py        # Excel → Firestore ETL
│   └── upload_images.py      # Images → Cloud Storage
├── infra/
│   ├── setup.sh              # GCP infrastructure setup
│   └── deploy.sh             # Quick redeploy
├── Dockerfile
├── requirements.txt
└── README.md
```

## Datos

- **8 tablas** de datos maestros (OSPA)
- **110+ variables** en diccionario de datos
- **6 flujos** de información (ArchiMate)
- **7 imágenes** de diagramas de flujo
