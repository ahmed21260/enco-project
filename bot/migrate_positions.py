import firebase_admin
from firebase_admin import credentials, firestore

# Remplace par le chemin de ta clé service account ou adapte pour Railway
cred = credentials.Certificate("serviceAccountKey_railway.txt")
firebase_admin.initialize_app(cred)

db = firestore.client()

# Source et cible
SOURCE_COLLECTION = "positions_log"
TARGET_COLLECTION = "positions_operateurs"

docs = db.collection(SOURCE_COLLECTION).stream()

for doc in docs:
    data = doc.to_dict()
    operateur_id = data.get("operateur_id") or data.get("operatorId")
    if not operateur_id:
        continue
    # Forcer l'ID en string
    doc_id = str(operateur_id)
    db.collection(TARGET_COLLECTION).document(doc_id).set({
        "operateur_id": doc_id,
        "nom": str(data.get("nom", "")),
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "type": str(data.get("type", "")),
        "timestamp": str(data.get("timestamp")),
    })
    print(f"Opérateur {doc_id} migré.")

print("Migration terminée.") 