import os
import sys
import firebase_admin
from firebase_admin import credentials, firestore

# Récupère le chemin de la clé de service depuis l'environnement ou par défaut
CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS', '../firebase/serviceAccountKey.json')

if not os.path.exists(CREDENTIALS_PATH):
    print(f"❌ ERREUR : Fichier de clé de service introuvable à {CREDENTIALS_PATH}")
    sys.exit(1)

# Initialise Firebase Admin
if not firebase_admin._apps:
    cred = credentials.Certificate(CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# 1. Ajout d'un opérateur
db.collection("operateurs").add({
    "nom": "Dupont",
    "poste": "Conducteur",
    "photo": "https://via.placeholder.com/100x100.png?text=Dupont",
    "dernierPoste": "2024-07-01 08:00",
    "nbPrises": 12,
    "telegram_id": 123456789,
    "prises": [
        {
            "date": "2024-07-01 08:00",
            "machine": "CAT 323 M",
            "photo": "https://via.placeholder.com/100x100.png?text=Dupont"
        }
    ]
})

# 2. Ajout d'un bon d'attachement
db.collection("bons_attachement").add({
    "chantier": "Chantier A",
    "date": "2024-07-01",
    "operateur": "Dupont",
    "statut": "Validé",
    "details": "Bon n°123",
    "photo": "https://via.placeholder.com/100x100.png?text=Bon"
})

# 3. Ajout d'une anomalie
db.collection("anomalies").add({
    "operateur_id": "1",
    "nom": "Dupont",
    "description": "Fuite hydraulique",
    "timestamp": "2024-07-01T10:15:00Z",
    "photoUrl": "https://via.placeholder.com/100x100.png?text=Anomalie",
    "latitude": 48.8566,
    "longitude": 2.3522,
    "machine": "CAT 323 M"
})

# 4. Ajout d'une checklist
db.collection("checklists").add({
    "operateur_id": "1",
    "nom": "Dupont",
    "timestamp": "2024-07-01T08:05:00Z",
    "chantier": "Chantier A",
    "questions": {
        "casque": True,
        "gilet": True,
        "signalisation": True
    }
})

print("✅ Données de test injectées dans Firestore !") 