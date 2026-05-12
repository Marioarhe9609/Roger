#!/bin/bash
# Roger - GCP Infrastructure Setup
# Run this script once to set up the GCP environment

set -e

PROJECT_ID="roger-496113"
REGION="us-central1"
BUCKET_NAME="${PROJECT_ID}-roger-assets"

echo "🚀 Setting up GCP infrastructure for Roger..."
echo "   Project: ${PROJECT_ID}"
echo "   Region: ${REGION}"

# 1. Set project
echo -e "\n1️⃣ Setting project..."
gcloud config set project ${PROJECT_ID}

# 2. Enable APIs
echo -e "\n2️⃣ Enabling APIs..."
gcloud services enable \
    run.googleapis.com \
    firestore.googleapis.com \
    aiplatform.googleapis.com \
    storage.googleapis.com \
    secretmanager.googleapis.com \
    cloudbuild.googleapis.com

# 3. Create Firestore database (Native mode)
echo -e "\n3️⃣ Creating Firestore database..."
gcloud firestore databases create \
    --location=${REGION} \
    --type=firestore-native \
    2>/dev/null || echo "   Firestore database already exists"

# 4. Create Cloud Storage bucket
echo -e "\n4️⃣ Creating Cloud Storage bucket..."
gsutil mb -l ${REGION} gs://${BUCKET_NAME}/ 2>/dev/null || echo "   Bucket already exists"
gsutil iam ch allUsers:objectViewer gs://${BUCKET_NAME}/

# 5. Store Telegram token in Secret Manager
echo -e "\n5️⃣ Setting up Secret Manager..."
echo "   To store your Telegram token, run:"
echo "   echo -n 'YOUR_TOKEN' | gcloud secrets create telegram-token --data-file=- --replication-policy=automatic"

echo -e "\n✅ Infrastructure setup complete!"
echo "   Next steps:"
echo "   1. Run: python -m scripts.ingest_data"
echo "   2. Run: python -m scripts.upload_images"
echo "   3. Run: ./infra/deploy.sh"
