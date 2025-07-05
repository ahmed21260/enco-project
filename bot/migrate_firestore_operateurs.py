import firebase_admin
from firebase_admin import credentials, firestore
import os

# Initialisation Firebase
if not firebase_admin._apps:
    cred_path = os.getenv('FIREBASE_CREDENTIALS', 'firebase_credentials.json')
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
db = firestore.client()

COLL = 'operateurs'
corrections = 0

def migrate_operateurs():
    global corrections
    docs = db.collection(COLL).stream()
    for doc in docs:
        data = doc.to_dict()
        telegram_id = str(data.get('telegram_id') or data.get('operateur_id'))
        if not telegram_id:
            print(f"Aucun telegram_id pour doc {doc.id}, ignoré.")
            continue
        # Si l'ID du doc n'est pas le telegram_id, on migre
        if doc.id != telegram_id:
            db.collection(COLL).document(telegram_id).set(data)
            db.collection(COLL).document(doc.id).delete()
            corrections += 1
            print(f"Migré doc {doc.id} -> {telegram_id}")
        else:
            # S'assurer que le champ telegram_id est bien présent
            if data.get('telegram_id') != telegram_id:
                db.collection(COLL).document(doc.id).update({'telegram_id': telegram_id})
                corrections += 1
                print(f"Corrigé champ telegram_id pour {doc.id}")
    print(f"Migration terminée. {corrections} documents opérateurs corrigés/migrés.")

if __name__ == '__main__':
    print("Ce script va migrer les opérateurs Firestore (ID = telegram_id, champ telegram_id correct, etc.)")
    confirm = input("Continuer ? (oui/non) : ")
    if confirm.lower() == 'oui':
        migrate_operateurs()
    else:
        print("Abandon.") 