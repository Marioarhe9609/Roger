#!/bin/bash
# Roger - Quick Deploy to Cloud Run
set -e

PROJECT_ID="roger-496113"
REGION="us-central1"
SERVICE_NAME="roger-bot"

echo "🚀 Deploying Roger to Cloud Run..."

gcloud run deploy ${SERVICE_NAME} \
    --source . \
    --region ${REGION} \
    --platform managed \
    --allow-unauthenticated \
    --memory 512Mi \
    --timeout 120 \
    --min-instances 0 \
    --max-instances 3 \
    --set-env-vars "GCP_PROJECT_ID=${PROJECT_ID},GCP_REGION=${REGION},TELEGRAM_TOKEN=$(gcloud secrets versions access latest --secret=telegram-token)"

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format='value(status.url)')
echo -e "\n✅ Deployed at: ${SERVICE_URL}"

# Set webhook
echo -e "\n🔗 Setting Telegram webhook..."
curl -s "${SERVICE_URL}/set-webhook?url=${SERVICE_URL}"

echo -e "\n🎉 Roger is live!"
