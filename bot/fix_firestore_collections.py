import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import json
from collections import defaultdict

load_dotenv()
FIREBASE_SERVICE_ACCOUNT = os.getenv('FIREBASE_SERVICE_ACCOUNT')
if FIREBASE_SERVICE_ACCOUNT and FIREBASE_SERVICE_ACCOUNT.strip().startswith('{'):
    cred = credentials.Certificate(json.loads(FIREBASE_SERVICE_ACCOUNT))
else:
    cred = credentials.Certificate('serviceAccountKey_railway.txt')
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

REPORT = defaultdict(list)

# 1. Corriger les operatorId manquants dans photos/anomalies/prises_poste si déductible

def fix_operatorId_missing():
    print('Correction des operatorId manquants...')
    # Prises de poste
    for doc in db.collection('prises_poste').stream():
        data = doc.to_dict()
        if not data.get('operatorId') and data.get('operateur_id'):
            db.collection('prises_poste').document(doc.id).update({'operatorId': str(data['operateur_id'])})
            REPORT['prises_poste'].append({'id': doc.id, 'fix': 'operatorId ajouté depuis operateur_id'})
    # Photos
    for doc in db.collection('photos').stream():
        data = doc.to_dict()
        if not data.get('operatorId') and data.get('operateur_id'):
            db.collection('photos').document(doc.id).update({'operatorId': str(data['operateur_id'])})
            REPORT['photos'].append({'id': doc.id, 'fix': 'operatorId ajouté depuis operateur_id'})
    # Anomalies
    for doc in db.collection('anomalies').stream():
        data = doc.to_dict()
        if not data.get('operatorId') and data.get('operateur_id'):
            db.collection('anomalies').document(doc.id).update({'operatorId': str(data['operateur_id'])})
            REPORT['anomalies'].append({'id': doc.id, 'fix': 'operatorId ajouté depuis operateur_id'})

# 2. Supprimer les doublons sur ['operatorId', 'timestamp'] dans anomalies

def remove_anomalies_duplicates():
    print('Suppression des doublons anomalies...')
    seen = set()
    to_delete = []
    for doc in db.collection('anomalies').stream():
        data = doc.to_dict()
        key = (str(data.get('operatorId')), data.get('timestamp'))
        if key in seen:
            to_delete.append(doc.id)
        else:
            seen.add(key)
    for doc_id in to_delete:
        db.collection('anomalies').document(doc_id).delete()
        REPORT['anomalies'].append({'id': doc_id, 'fix': 'Doublon supprimé'})

# 3. Met à jour photos_urls dans prises_poste avec les bonnes URLs si possible

def fix_photos_urls():
    print('Correction des photos_urls dans prises_poste...')
    # Indexer les photos par operatorId
    photos = list(db.collection('photos').stream())
    photos_by_op = defaultdict(list)
    for ph in photos:
        data = ph.to_dict()
        opid = str(data.get('operatorId'))
        url = data.get('url')
        if opid and url:
            photos_by_op[opid].append(url)
    # Mettre à jour prises_poste
    for doc in db.collection('prises_poste').stream():
        data = doc.to_dict()
        opid = str(data.get('operatorId'))
        urls = photos_by_op.get(opid, [])
        if urls:
            db.collection('prises_poste').document(doc.id).update({'photos_urls': urls})
            REPORT['prises_poste'].append({'id': doc.id, 'fix': f'photos_urls mis à jour ({len(urls)} urls)'})

# 4. Générer un rapport

def main():
    fix_operatorId_missing()
    remove_anomalies_duplicates()
    fix_photos_urls()
    with open('fix_firestore_report.json', 'w', encoding='utf-8') as f:
        json.dump(REPORT, f, indent=2, ensure_ascii=False)
    print('\n=== Rapport de correction généré : fix_firestore_report.json ===')

if __name__ == '__main__':
    main() 