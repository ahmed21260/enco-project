import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv()
CRED_PATH = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'serviceAccountKey_railway.txt')
if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.Certificate(CRED_PATH))
db = firestore.client()

def sync_photos_to_prises_poste():
    print('Synchronisation des photos pour prises_poste...')
    updated = 0
    for doc in db.collection('prises_poste').stream():
        data = doc.to_dict()
        operatorId = str(data.get('operatorId'))
        # Cherche toutes les photos de ce user
        photos = db.collection('photos').where('operatorId', '==', operatorId).stream()
        urls = [p.to_dict().get('url') for p in photos if p.to_dict().get('url')]
        if urls:
            db.collection('prises_poste').document(doc.id).update({'photos_urls': urls})
            updated += 1
    print(f'✅ {updated} prises_poste mises à jour.')

def sync_photos_to_anomalies():
    print('Synchronisation des photos pour anomalies...')
    updated = 0
    for doc in db.collection('anomalies').stream():
        data = doc.to_dict()
        operatorId = str(data.get('operatorId'))
        # Cherche la photo la plus récente de ce user (ou adapte la logique si tu as un mapping précis)
        photos = list(db.collection('photos').where('operatorId', '==', operatorId).stream())
        if photos:
            # Prend la plus récente
            photo_url = sorted([p.to_dict().get('url') for p in photos if p.to_dict().get('url')], reverse=True)[0]
            db.collection('anomalies').document(doc.id).update({'photoURL': photo_url})
            updated += 1
    print(f'✅ {updated} anomalies mises à jour.')

if __name__ == '__main__':
    sync_photos_to_prises_poste()
    sync_photos_to_anomalies()
    print('🎯 Synchronisation terminée. Vérifie le dashboard !') 