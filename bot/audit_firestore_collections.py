import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import json
from collections import Counter, defaultdict

load_dotenv()
# Correction auto : charge le credentials depuis la variable si c'est du JSON, sinon depuis le fichier
FIREBASE_SERVICE_ACCOUNT = os.getenv('FIREBASE_SERVICE_ACCOUNT')
if FIREBASE_SERVICE_ACCOUNT and FIREBASE_SERVICE_ACCOUNT.strip().startswith('{'):
    cred = credentials.Certificate(json.loads(FIREBASE_SERVICE_ACCOUNT))
else:
    cred = credentials.Certificate('serviceAccountKey_railway.txt')
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

REPORT = defaultdict(list)

def check_collection(collection, key_fields, url_fields=None):
    print(f'\n--- Audit de la collection {collection} ---')
    docs = list(db.collection(collection).stream())
    ids = set()
    key_counter = Counter()
    url_fields = url_fields or []
    for doc in docs:
        data = doc.to_dict()
        doc_id = doc.id
        # Doublons sur les clés
        key = tuple(data.get(f) for f in key_fields)
        key_counter[key] += 1
        # Champs critiques manquants
        for f in key_fields:
            if not data.get(f):
                REPORT[collection].append({'id': doc_id, 'error': f'Champ manquant: {f}'})
        # URLs invalides
        for uf in url_fields:
            url = data.get(uf)
            if url is not None and (not isinstance(url, str) or not url.startswith('http')):
                REPORT[collection].append({'id': doc_id, 'error': f'URL invalide: {uf}={url}'})
    # Doublons
    for k, count in key_counter.items():
        if count > 1:
            REPORT[collection].append({'key': k, 'error': f'Doublon sur {key_fields}: {count} occurrences'})
    print(f"Total documents: {len(docs)}")
    print(f"Erreurs/doublons détectés: {len(REPORT[collection])}")
    for err in REPORT[collection]:
        print(err)

def audit_photos_vs_prises():
    print('\n--- Audit mapping photos <-> prises_poste ---')
    prises = list(db.collection('prises_poste').stream())
    photos = list(db.collection('photos').stream())
    prises_by_op = defaultdict(list)
    for p in prises:
        data = p.to_dict()
        opid = str(data.get('operatorId'))
        prises_by_op[opid].append(p.id)
    photos_by_op = defaultdict(list)
    for ph in photos:
        data = ph.to_dict()
        opid = str(data.get('operatorId'))
        photos_by_op[opid].append(ph.id)
    # Prises sans photo
    for opid, prise_ids in prises_by_op.items():
        if not photos_by_op.get(opid):
            for pid in prise_ids:
                REPORT['prises_poste'].append({'id': pid, 'error': 'Aucune photo liée à cet opérateur'})
    # Photos orphelines
    for opid, photo_ids in photos_by_op.items():
        if not prises_by_op.get(opid):
            for phid in photo_ids:
                REPORT['photos'].append({'id': phid, 'error': 'Photo orpheline (aucune prise_poste liée à cet opérateur)'})

def main():
    check_collection('prises_poste', key_fields=['operatorId', 'timestamp'], url_fields=['photos_urls'])
    check_collection('photos', key_fields=['photo_file_id', 'operatorId'], url_fields=['url'])
    check_collection('anomalies', key_fields=['operatorId', 'timestamp'], url_fields=['photoURL'])
    audit_photos_vs_prises()
    # Rapport final
    with open('audit_firestore_report.json', 'w', encoding='utf-8') as f:
        json.dump(REPORT, f, indent=2, ensure_ascii=False)
    print('\n=== Rapport d\'audit généré : audit_firestore_report.json ===')

if __name__ == '__main__':
    main() 