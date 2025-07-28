import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore as fs

# Chemin absolu depuis la racine du projet
KEY_PATH = os.path.join(os.path.dirname(__file__), '..', 'serviceAccountKey_railway.txt')
if not os.path.exists(KEY_PATH):
    raise FileNotFoundError(f"Clé Firebase introuvable à {KEY_PATH}")
cred = credentials.Certificate(KEY_PATH)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = fs.client()

# Création des collections principales avec un exemple de document pour chaque
collections_with_examples = {
    "operateurs": {
        "operatorId": "OP123",
        "nom": "Ahmed Chaira",
        "poste": "Pelle rail-route",
        "chantier": "Lille TGV",
        "heure": "2025-07-03T06:45:00Z",
        "status": "En poste",
        "timestamp": fs.SERVER_TIMESTAMP,
        "telegramUserId": 123456789
    },
    "prises_poste": {
        "id": "PRISE456",
        "operatorId": "OP123",
        "heure": "2025-07-03T06:45:00Z",
        "chantier": "Lille TGV",
        "poste": "Pelle rail-route",
        "status": "En poste",
        "timestamp": fs.SERVER_TIMESTAMP
    },
    "photos": {
        "operatorId": "OP123",
        "priseId": "PRISE456",
        "urlPhoto": "https://firebase.storage...",
        "timestamp": fs.SERVER_TIMESTAMP,
        "chantier": "Lille TGV",
        "type": "prise_de_poste"
    },
    "bons_attachement": {
        "operatorId": "OP123",
        "priseId": "PRISE456",
        "date": "2025-07-03T07:30:00Z",
        "urlDocument": "https://firebase.storage...",
        "type": "Bon de travail",
        "status": "Validé automatiquement",
        "chantier": "Lille TGV"
    }
}

for col, example in collections_with_examples.items():
    db.collection(col).add(example)

print("Collections et exemples créés selon la nouvelle structure !")