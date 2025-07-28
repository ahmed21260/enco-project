import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import json

load_dotenv()
FIREBASE_SERVICE_ACCOUNT = os.getenv('FIREBASE_SERVICE_ACCOUNT')
if FIREBASE_SERVICE_ACCOUNT and FIREBASE_SERVICE_ACCOUNT.strip().startswith('{'):
    cred = credentials.Certificate(json.loads(FIREBASE_SERVICE_ACCOUNT))
else:
    cred = credentials.Certificate('serviceAccountKey_railway.txt')
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

REPORT = []

def fix_photos_urls_exact():
    print('Correction précise des photos_urls dans prises_poste...')
    photos_ref = db.collection('photos')
    updated = 0
    for doc in db.collection('prises_poste').stream():
        data = doc.to_dict()
        file_ids = data.get('photos_file_ids', [])
        urls = []
        for file_id in file_ids:
            # Cherche la photo correspondante
            query = photos_ref.where('photo_file_id', '==', file_id).limit(1).stream()
            url = None
            for photo_doc in query:
                photo_data = photo_doc.to_dict()
                url = photo_data.get('url')
                break
            urls.append(url)
        # Met à jour seulement si différent
        if data.get('photos_urls') != urls:
            db.collection('prises_poste').document(doc.id).update({'photos_urls': urls})
            REPORT.append({'collection': 'prises_poste', 'id': doc.id, 'fix': f'photos_urls mis à jour (mapping exact, {len(urls)} urls)'})
            updated += 1
    print(f'✅ {updated} prises_poste corrigées.')

    print('Correction précise des photoURL dans anomalies...')
    updated_anom = 0
    for doc in db.collection('anomalies').stream():
        data = doc.to_dict()
        file_id = data.get('photo_file_id')
        url = None
        if file_id:
            query = photos_ref.where('photo_file_id', '==', file_id).limit(1).stream()
            for photo_doc in query:
                photo_data = photo_doc.to_dict()
                url = photo_data.get('url')
                break
        # Met à jour seulement si différent
        if url and data.get('photoURL') != url:
            db.collection('anomalies').document(doc.id).update({'photoURL': url})
            REPORT.append({'collection': 'anomalies', 'id': doc.id, 'fix': 'photoURL mis à jour'})
            updated_anom += 1
    print(f'✅ {updated_anom} anomalies corrigées.')

    with open('fix_photos_urls_exact_report.json', 'w', encoding='utf-8') as f:
        json.dump(REPORT, f, indent=2, ensure_ascii=False)
    print('\n=== Rapport généré : fix_photos_urls_exact_report.json ===')

if __name__ == '__main__':
    fix_photos_urls_exact() 