import firebase_admin
from firebase_admin import credentials, firestore
import os

# Initialisation Firebase
if not firebase_admin._apps:
    cred_path = os.getenv('FIREBASE_CREDENTIALS', 'firebase_credentials.json')
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
db = firestore.client()

COLLECTIONS = [
    'photos',
    'operateurs',
    'prises_poste',
    'anomalies',
    'urgences',
    'bons_attachement',
    'checklists',
]

summary = {}

def harmonise_photos():
    corrections = 0
    docs = db.collection('photos').stream()
    for doc in docs:
        data = doc.to_dict()
        update = {}
        if 'urlPhoto' in data and not data.get('url'):
            update['url'] = data['urlPhoto']
        op_id = data.get('operateur_id') or data.get('operatorId') or data.get('telegram_id')
        if op_id and data.get('operateur_id') != op_id:
            update['operateur_id'] = op_id
        if update:
            db.collection('photos').document(doc.id).update(update)
            corrections += 1
    summary['photos'] = corrections

def harmonise_operateurs():
    corrections = 0
    docs = db.collection('operateurs').stream()
    for doc in docs:
        data = doc.to_dict()
        telegram_id = str(data.get('telegram_id') or data.get('operateur_id'))
        if not telegram_id:
            continue
        if doc.id != telegram_id:
            db.collection('operateurs').document(telegram_id).set(data)
            db.collection('operateurs').document(doc.id).delete()
            corrections += 1
        else:
            if data.get('telegram_id') != telegram_id:
                db.collection('operateurs').document(doc.id).update({'telegram_id': telegram_id})
                corrections += 1
    summary['operateurs'] = corrections

def harmonise_generique(coll):
    corrections = 0
    docs = db.collection(coll).stream()
    for doc in docs:
        data = doc.to_dict()
        update = {}
        op_id = data.get('operateur_id') or data.get('operatorId') or data.get('telegram_id')
        if op_id and data.get('operateur_id') != op_id:
            update['operateur_id'] = op_id
        # Harmoniser d'autres champs si besoin (ex: urlPhoto → url)
        if coll in ['anomalies', 'urgences', 'bons_attachement', 'prises_poste']:
            if 'urlPhoto' in data and not data.get('url'):
                update['url'] = data['urlPhoto']
        if update:
            db.collection(coll).document(doc.id).update(update)
            corrections += 1
    summary[coll] = corrections

def main():
    print("Ce script va harmoniser TOUTES les collections Firestore métier (photos, operateurs, prises_poste, etc.)")
    confirm = input("Continuer ? (oui/non) : ")
    if confirm.lower() != 'oui':
        print("Abandon.")
        return
    harmonise_photos()
    harmonise_operateurs()
    for coll in COLLECTIONS:
        if coll not in ['photos', 'operateurs']:
            harmonise_generique(coll)
    print("\n--- Rapport de migration ---")
    for k, v in summary.items():
        print(f"{k} : {v} documents corrigés")
    print("Migration terminée.")

if __name__ == '__main__':
    main() 