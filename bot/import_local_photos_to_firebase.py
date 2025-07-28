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

LOCAL_SYNC_DIR = os.path.join(os.path.dirname(__file__), 'bot', 'photos', 'sync')

def make_storage_url(blob_path):
    return f"https://firebasestorage.googleapis.com/v0/b/{BUCKET}/o/{blob_path.replace('/', '%2F')}?alt=media"

def import_photos():
    total_uploaded = 0
    for user_id in os.listdir(LOCAL_SYNC_DIR):
        user_dir = os.path.join(LOCAL_SYNC_DIR, user_id)
        if not os.path.isdir(user_dir):
            continue
        for fname in os.listdir(user_dir):
            fpath = os.path.join(user_dir, fname)
            if not os.path.isfile(fpath):
                continue
            # Upload dans Storage
            storage_path = f"sync/{user_id}/{fname}"
            blob = bucket.blob(storage_path)
            blob.upload_from_filename(fpath)
            blob.make_public()
            url = make_storage_url(storage_path)
            # Crée le doc Firestore
            photo_doc = {
                "photo_file_id": fname,
                "url": url,
                "timestamp": datetime.fromtimestamp(os.path.getmtime(fpath)).isoformat(),
                "type": "sync_import",
                "operatorId": user_id,
                "local_path": fpath
            }
            db.collection('photos').add(photo_doc)
            print(f"✅ Uploadé et référencé : {storage_path}")
            total_uploaded += 1
    print(f"\n🎯 Total : {total_uploaded} photos importées dans Firebase Storage et Firestore.")

if __name__ == '__main__':
    import_photos() 