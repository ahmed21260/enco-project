import os
import json
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, initialize_app

# --- MODE FIRESTORE ---
USE_FIRESTORE = os.getenv('ENCO_USE_FIRESTORE', '0') == '1'

if USE_FIRESTORE:
    from firebase_admin import firestore, storage
    if not firebase_admin._apps:
        if os.getenv("FIREBASE_SERVICE_ACCOUNT"):
            cred = credentials.Certificate(json.loads(os.environ["FIREBASE_SERVICE_ACCOUNT"]))
        else:
            cred = credentials.Certificate("serviceAccountKey.json")  # fallback local
        initialize_app(cred, {
            'storageBucket': os.getenv("FIREBASE_STORAGE_BUCKET", "enco-prestarail.appspot.com")
        })
    db = firestore.client()
else:
    print("⚠️  Mode temporaire : Firebase désactivé pour les tests")

# Chemin absolu du dossier bot
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(BASE_DIR, '../positions_log.jsonl')

# --- POSITIONS ---
def save_position(data):
    if USE_FIRESTORE:
        db.collection('positions_operateurs').add(data)
    else:
        print(f"📍 Position sauvegardée (mode test): {data}")
        # Sauvegarde temporaire dans un fichier local
        try:
            with open(os.path.join(BASE_DIR, '../positions_temp.json'), 'a') as f:
                f.write(json.dumps(data) + '\n')
        except:
            pass
        # Log spécial pour dashboard carte
        try:
            # Crée le fichier s'il n'existe pas
            if not os.path.exists(LOG_PATH):
                with open(LOG_PATH, 'w') as f:
                    pass
            with open(LOG_PATH, 'a') as flog:
                flog.write(json.dumps({
                    'operateur_id': data.get('operateur_id'),
                    'nom': data.get('nom'),
                    'timestamp': data.get('timestamp'),
                    'latitude': data.get('latitude'),
                    'longitude': data.get('longitude'),
                    'type': data.get('type')
                }) + '\n')
            print(f"🗺️  Position loggée pour dashboard: {data.get('latitude')}, {data.get('longitude')}")
        except Exception as e:
            print(f"Erreur log position: {e}")

# --- CHECKLISTS ---
def save_checklist(user_id, data):
    if USE_FIRESTORE:
        db.collection('checklists').add({'operateur_id': user_id, **data})
    else:
        print(f"✅ Checklist sauvegardée (mode test): {user_id} - {data}")
        # Sauvegarde temporaire dans un fichier local
        try:
            with open(os.path.join(BASE_DIR, '../checklists_temp.json'), 'a') as f:
                f.write(json.dumps({'operateur_id': user_id, **data}) + '\n')
        except:
            pass

# --- ANOMALIES ---
def save_anomalie(data):
    if USE_FIRESTORE:
        db.collection('anomalies').add(data)
    else:
        print(f"🚨 Anomalie sauvegardée (mode test): {data}")
        try:
            with open(os.path.join(BASE_DIR, '../anomalies_temp.json'), 'a') as f:
                f.write(json.dumps(data) + '\n')
        except:
            pass

# --- HISTORIQUE ---
def get_historique(operateur_id, limit=10):
    if USE_FIRESTORE:
        positions = db.collection('positions_operateurs').where('operateur_id', '==', operateur_id).order_by('timestamp', direction='DESCENDING').limit(limit).stream()
        anomalies = db.collection('anomalies').where('operateur_id', '==', operateur_id).order_by('timestamp', direction='DESCENDING').limit(limit).stream()
        checklists = db.collection('checklists').where('operateur_id', '==', operateur_id).order_by('timestamp', direction='DESCENDING').limit(limit).stream()
        histo = []
        for p in positions:
            d = p.to_dict(); d['type'] = d.get('type', 'prise/fin'); histo.append(d)
        for a in anomalies:
            d = a.to_dict(); d['type'] = 'anomalie'; histo.append(d)
        for c in checklists:
            d = c.to_dict(); d['type'] = 'checklist'; histo.append(d)
        histo.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return histo[:limit]
    else:
        histo = []
        for fname, typ in [("../positions_temp.json", "prise/fin"), ("../anomalies_temp.json", "anomalie"), ("../checklists_temp.json", "checklist")]:
            try:
                with open(os.path.join(BASE_DIR, fname), 'r') as f:
                    for line in f:
                        d = json.loads(line)
                        if d.get('operateur_id') == operateur_id:
                            d['type'] = typ
                            histo.append(d)
            except:
                pass
        histo.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return histo[:limit]

# --- DOCUMENTS ---
def get_documents():
    if USE_FIRESTORE:
        docs = db.collection('documents').stream()
        return [d.to_dict() for d in docs]
    else:
        try:
            with open(os.path.join(BASE_DIR, '../docs_temp.json'), 'r') as f:
                return [json.loads(line) for line in f]
        except:
            return []

def upload_photo_to_storage(local_path, storage_path):
    """Upload une photo locale sur Firebase Storage et retourne l'URL publique ou None en cas d'échec."""
    if USE_FIRESTORE:
        try:
            bucket = storage.bucket()
            blob = bucket.blob(storage_path)
            blob.upload_from_filename(local_path)
            blob.make_public()
            return blob.public_url
        except Exception as e:
            print(f"Erreur upload Firebase Storage : {e}")
            return None
    else:
        print(f"Photo non uploadée (mode test) : {local_path}")
        return None

# Pour une vraie connexion Firebase, décommentez et configurez :
"""
import firebase_admin
from firebase_admin import credentials, firestore

if not firebase_admin._apps:
    cred = credentials.Certificate(os.getenv('FIREBASE_CREDENTIALS', '../firebase/serviceAccountKey.json'))
    firebase_admin.initialize_app(cred)
db = firestore.client()

def save_position(data):
    db.collection('positions_operateurs').add(data)

def save_checklist(user_id, data):
    db.collection('checklists').add({'operateur_id': user_id, **data})
""" 