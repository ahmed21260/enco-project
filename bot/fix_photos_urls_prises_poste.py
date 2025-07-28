import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv
load_dotenv()

# Initialisation Firebase Admin
CRED_PATH = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'serviceAccountKey_railway.txt')
BUCKET = os.environ.get('FIREBASE_STORAGE_BUCKET', 'enco-prestarail.firebasestorage.app')
if not os.path.exists(CRED_PATH):
    raise FileNotFoundError(f"Fichier de credentials Firebase introuvable: {CRED_PATH}")
if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.Certificate(CRED_PATH), {'storageBucket': BUCKET})
db = firestore.client()

def main():
    prises_ref = db.collection('prises_poste')
    photos_ref = db.collection('photos')
    docs = list(prises_ref.stream())
    total = len(docs)
    updated = 0
    not_found = 0
    for doc in docs:
        data = doc.to_dict()
        file_ids = data.get('photos_file_ids', [])
        if not file_ids:
            continue
        urls = []
        for file_id in file_ids:
            # Cherche la photo correspondante
            query = photos_ref.where('photo_file_id', '==', file_id).limit(1).stream()
            url = None
            for photo_doc in query:
                photo_data = photo_doc.to_dict()
                url = photo_data.get('photoURL')
                break
            if not url:
                not_found += 1
            urls.append(url)
        # Met à jour seulement si différent
        if data.get('photos_urls') != urls:
            prises_ref.document(doc.id).update({'photos_urls': urls})
            updated += 1
    print(f"Traitement terminé. {updated} documents mis à jour sur {total}.")
    print(f"Photos non trouvées (file_id sans URL): {not_found}")

if __name__ == '__main__':
    main() 