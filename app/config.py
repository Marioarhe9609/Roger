"""
Configuration module for Roger chatbot.
Centralizes all environment variables and GCP settings.
"""
import os


# GCP Settings
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "roger-496113")
GCP_REGION = os.environ.get("GCP_REGION", "us-central1")

# Telegram Settings
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")

# Firestore Collections
COLLECTION_DATOS_MAESTROS = "datos_maestros"
COLLECTION_DICCIONARIO = "diccionario_datos"
COLLECTION_FLUJOS = "flujos_informacion"
COLLECTION_METADATA = "metadata"

# Cloud Storage
GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME", f"{GCP_PROJECT_ID}-roger-assets")

# Vertex AI
VERTEX_MODEL = os.environ.get("VERTEX_MODEL", "gemini-2.0-flash-001")
VERTEX_LOCATION = os.environ.get("VERTEX_LOCATION", GCP_REGION)

# App Settings
PORT = int(os.environ.get("PORT", 8080))
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
