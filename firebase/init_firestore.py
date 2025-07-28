import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("firebase/serviceAccountKey_railway.txt")
firebase_admin.initialize_app(cred)
db = firestore.client()

print("Connexion Firestore OK") 