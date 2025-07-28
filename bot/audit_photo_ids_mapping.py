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

report = {
    'photos_file_ids_prises_poste': [],
    'photo_file_id_photos': [],
    'photo_file_id_anomalies': [],
    'in_prises_not_in_photos': [],
    'in_photos_not_in_prises': [],
    'in_anomalies_not_in_photos': [],
    'in_photos_not_in_anomalies': []
}

def audit_photo_ids():
    # 1. Tous les photos_file_ids de prises_poste
    ids_prises = set()
    for doc in db.collection('prises_poste').stream():
        data = doc.to_dict()
        for fid in data.get('photos_file_ids', []):
            ids_prises.add(fid)
    report['photos_file_ids_prises_poste'] = sorted(list(ids_prises))

    # 2. Tous les photo_file_id de photos
    ids_photos = set()
    for doc in db.collection('photos').stream():
        data = doc.to_dict()
        fid = data.get('photo_file_id')
        if fid:
            ids_photos.add(fid)
    report['photo_file_id_photos'] = sorted(list(ids_photos))

    # 3. Tous les photo_file_id de anomalies
    ids_anomalies = set()
    for doc in db.collection('anomalies').stream():
        data = doc.to_dict()
        fid = data.get('photo_file_id')
        if fid:
            ids_anomalies.add(fid)
    report['photo_file_id_anomalies'] = sorted(list(ids_anomalies))

    # 4. Différences
    report['in_prises_not_in_photos'] = sorted(list(ids_prises - ids_photos))
    report['in_photos_not_in_prises'] = sorted(list(ids_photos - ids_prises))
    report['in_anomalies_not_in_photos'] = sorted(list(ids_anomalies - ids_photos))
    report['in_photos_not_in_anomalies'] = sorted(list(ids_photos - ids_anomalies))

    with open('audit_photo_ids_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print('\n=== Rapport généré : audit_photo_ids_report.json ===')
    print(f"\nPhotos_file_ids dans prises_poste mais pas dans photos : {len(report['in_prises_not_in_photos'])}")
    print(f"Photos_file_id dans photos mais pas dans prises_poste : {len(report['in_photos_not_in_prises'])}")
    print(f"Photo_file_id dans anomalies mais pas dans photos : {len(report['in_anomalies_not_in_photos'])}")
    print(f"Photo_file_id dans photos mais pas dans anomalies : {len(report['in_photos_not_in_anomalies'])}")

if __name__ == '__main__':
    audit_photo_ids() 