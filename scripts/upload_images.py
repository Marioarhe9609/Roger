"""
Upload flow diagram images to Google Cloud Storage.
Run this once after creating the GCS bucket.

Usage:
    python -m scripts.upload_images
"""
import os
from google.cloud import storage

GCP_PROJECT_ID = "roger-496113"
BUCKET_NAME = f"{GCP_PROJECT_ID}-roger-assets"
BASE_PATH = os.environ.get(
    "DATA_PATH",
    r"C:\Users\ASUS\Documents\Ideam\Arquitectura\Mapa_Informacion_Institucional",
)

# Map images to their flow descriptions
IMAGE_FILES = [
    "img_0_2_4.png",
    "img_0_3_3.png",
    "img_0_5_3.png",
    "img_0_6_3.png",
    "img_0_7_3.png",
    "img_0_8_3.png",
    "img_0_9_3.png",
]


def upload_images():
    """Upload all flow diagram images to GCS."""
    print(f"📦 Uploading images to gs://{BUCKET_NAME}/\n")

    client = storage.Client(project=GCP_PROJECT_ID)
    bucket = client.bucket(BUCKET_NAME)

    for filename in IMAGE_FILES:
        filepath = os.path.join(BASE_PATH, filename)
        if not os.path.exists(filepath):
            print(f"  ⚠️ File not found: {filename}")
            continue

        blob = bucket.blob(f"flujos/{filename}")
        blob.upload_from_filename(filepath, content_type="image/png")

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/flujos/{filename}"
        print(f"  ✅ {filename} → gs://{BUCKET_NAME}/flujos/{filename}")
        print(f"     Public URL: {public_url}")

    print(f"\n✅ Upload complete!")


def update_firestore_urls():
    """Update Firestore flow documents with image URLs."""
    from google.cloud import firestore

    print("\n🔄 Updating Firestore with image URLs...")

    db = firestore.Client(project=GCP_PROJECT_ID)
    client = storage.Client(project=GCP_PROJECT_ID)
    bucket = client.bucket(BUCKET_NAME)

    flows = db.collection("flujos_informacion").stream()
    for doc in flows:
        data = doc.to_dict()
        imagen = data.get("imagen", "")
        if imagen:
            blob = bucket.blob(f"flujos/{imagen}")
            if blob.exists():
                url = blob.public_url
                db.collection("flujos_informacion").document(doc.id).update({
                    "imagen_url": url,
                })
                print(f"  ✅ {doc.id} → {url}")

    print("✅ Firestore URLs updated!")


if __name__ == "__main__":
    upload_images()
    update_firestore_urls()
