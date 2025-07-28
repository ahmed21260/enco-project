import os
import firebase_admin
from firebase_admin import credentials, firestore, storage
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
CRED_PATH = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'serviceAccountKey_railway.txt')
BUCKET = os.environ.get('FIREBASE_STORAGE_BUCKET', 'enco-prestarail.firebasestorage.app')
if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.Certificate(CRED_PATH), {'storageBucket': BUCKET})
db = firestore.client()
bucket = storage.bucket()

def make_storage_url(blob_path):
    return f"https://firebasestorage.googleapis.com/v0/b/{BUCKET}/o/{blob_path.replace('/', '%2F')}?alt=media"

def migrate_collection_photos():
    total_created = 0
    # 1. Prises de poste
    print("Migration des photos de prises_poste...")
    for doc in db.collection('prises_poste').stream():
        data = doc.to_dict()
        operatorId = data.get('operatorId')
        chantier = data.get('chantier', '')
        machine = data.get('machine', '')
        photos = data.get('photos_file_ids', [])
        ts = data.get('timestamp') or datetime.now().isoformat()
        for idx, file_id in enumerate(photos):
            # On suppose le chemin Storage
            prefix = f"prises_poste/{operatorId}/"
            # Cherche le fichier dans le bucket
            blobs = list(bucket.list_blobs(prefix=prefix))
            found = False
            for blob in blobs:
                if file_id in blob.name:
                    url = make_storage_url(blob.name)
                    found = True
                    break
            if not found:
                print(f"[WARN] Photo {file_id} non trouvée dans Storage pour prise de poste {doc.id}")
                continue
            # Vérifie si déjà présent dans photos
            query = db.collection('photos').where('photo_file_id', '==', file_id).limit(1).stream()
            if any(query):
                continue
            photo_doc = {
                "photo_file_id": file_id,
                "url": url,
                "timestamp": ts,
                "type": "prise_de_poste",
                "operatorId": operatorId,
                "chantier": chantier,
                "machine": machine,
            }
            db.collection('photos').add(photo_doc)
            total_created += 1
    # 2. Anomalies
    print("Migration des photos d'anomalies...")
    for doc in db.collection('anomalies').stream():
        data = doc.to_dict()
        operatorId = data.get('operatorId')
        machine = data.get('machine', '')
        file_id = data.get('photo_file_id')
        ts = data.get('timestamp') or datetime.now().isoformat()
        if not file_id:
            continue
        prefix = f"anomalies/{operatorId}/"
        blobs = list(bucket.list_blobs(prefix=prefix))
        found = False
        for blob in blobs:
            if file_id in blob.name:
                url = make_storage_url(blob.name)
                found = True
                break
        if not found:
            print(f"[WARN] Photo {file_id} non trouvée dans Storage pour anomalie {doc.id}")
            continue
        query = db.collection('photos').where('photo_file_id', '==', file_id).limit(1).stream()
        if any(query):
            continue
        photo_doc = {
            "photo_file_id": file_id,
            "url": url,
            "timestamp": ts,
            "type": "anomalie",
            "operatorId": operatorId,
            "machine": machine,
        }
        db.collection('photos').add(photo_doc)
        total_created += 1
    print(f"\n✅ Migration terminée. {total_created} documents ajoutés dans 'photos'.")

if __name__ == '__main__':
    migrate_collection_photos() 