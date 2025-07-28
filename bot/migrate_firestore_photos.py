import firebase_admin
from firebase_admin import credentials, firestore
import os
BUCKET = os.environ.get('FIREBASE_STORAGE_BUCKET', 'enco-prestarail.firebasestorage.app')
# Initialisation Firebase
if not firebase_admin._apps:
    cred_path = os.getenv('FIREBASE_CREDENTIALS', 'firebase_credentials.json')
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred, {'storageBucket': BUCKET})
db = firestore.client()

# Mapping manuel possible si besoin (ex: { 'operatorId': 'operateur_id' })
ID_MAPPING = {}

COLL = 'photos'
corrections = 0

def migrate_photos():
    global corrections
    docs = db.collection(COLL).stream()
    for doc in docs:
        data = doc.to_dict()
        update = {}
        # Copier urlPhoto -> url si url absent
        if 'urlPhoto' in data and not data.get('url'):
            update['url'] = data['urlPhoto']
        # Harmoniser operateur_id
        op_id = data.get('operateur_id') or data.get('operatorId') or data.get('telegram_id')
        if not op_id and 'operatorId' in data:
            op_id = ID_MAPPING.get(data['operatorId'], data['operatorId'])
        if op_id and data.get('operateur_id') != op_id:
            update['operateur_id'] = op_id
        # Harmoniser autres champs si besoin (priseId, type...)
        # ...
        if update:
            db.collection(COLL).document(doc.id).update(update)
            corrections += 1
            print(f"Corrigé doc {doc.id} : {update}")
    print(f"Migration terminée. {corrections} documents corrigés.")

if __name__ == '__main__':
    print("Ce script va migrer les anciennes photos Firestore (ajout champ url, harmonisation operateur_id, etc.)")
    confirm = input("Continuer ? (oui/non) : ")
    if confirm.lower() == 'oui':
        migrate_photos()
    else:
        print("Abandon.") 