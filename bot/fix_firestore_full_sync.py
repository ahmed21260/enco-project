import os
import sys
import firebase_admin
from firebase_admin import credentials, firestore, storage
from google.cloud.exceptions import NotFound
from dotenv import load_dotenv
from telegram import Bot
import asyncio
import logging
from datetime import datetime

# Chargement des variables d'environnement
load_dotenv()
CRED_PATH = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'serviceAccountKey_railway.txt')
BUCKET = os.environ.get('FIREBASE_STORAGE_BUCKET', 'enco-prestarail.appspot.com')
BOT_TOKEN = os.environ.get('BOT_TOKEN')

if not BOT_TOKEN:
    print("[ERREUR] BOT_TOKEN manquant dans l'environnement.")
    sys.exit(1)

if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.Certificate(CRED_PATH), {'storageBucket': BUCKET})

db = firestore.client()
bucket = storage.bucket()
bot = Bot(token=BOT_TOKEN)

# Utilitaires

def upload_photo_to_storage(local_path, storage_path):
    blob = bucket.blob(storage_path)
    blob.upload_from_filename(local_path)
    blob.make_public()
    return blob.public_url

async def download_telegram_photo(file_id, local_path):
    file = await bot.get_file(file_id)
    await file.download_to_drive(local_path)

async def sync_all():
    # 1. Synchronisation des prises de poste
    print("[SYNC] Prises de poste...")
    prises_ref = db.collection('prises_poste')
    prises = list(prises_ref.stream())
    fix_count = 0
    for doc in prises:
        data = doc.to_dict()
        doc_id = doc.id
        photos_file_ids = data.get('photos_file_ids', [])
        photos_urls = data.get('photos_urls', [])
        if not isinstance(photos_urls, list):
            photos_urls = []
        updated = False
        new_urls = []
        for file_id in photos_file_ids:
            # Cherche dans photos par file_id exact
            photos = db.collection('photos').where('photo_file_id', '==', file_id).limit(1).stream()
            url = None
            for p in photos:
                p_data = p.to_dict()
                url = p_data.get('photoURL') or p_data.get('url')
                break
            # Si pas trouvé, tente download/upload
            if not url:
                try:
                    local_path = f"temp_photo_{doc_id}_{file_id}.jpg"
                    await download_telegram_photo(file_id, local_path)
                    storage_path = f"prises_poste/{data.get('operatorId','unknown')}/{doc_id}_{file_id}.jpg"
                    url = upload_photo_to_storage(local_path, storage_path)
                    # Crée le doc dans photos avec le bon operatorId
                    if url:
                        db.collection('photos').add({
                            'photo_file_id': file_id,
                            'photoURL': url,
                            'operatorId': data.get('operatorId'),
                            'timestamp': data.get('timestamp'),
                            'type': 'prise_de_poste',
                        })
                    os.remove(local_path)
                    updated = True
                    print(f"[OK] Photo prise de poste {doc_id} file_id {file_id} => {url}")
                except Exception as e:
                    url = None
                    print(f"[ERR] Impossible d'uploader photo prise de poste {doc_id} file_id {file_id}: {e}")
            new_urls.append(url)
        if new_urls != photos_urls:
            prises_ref.document(doc_id).update({'photos_urls': new_urls})
            fix_count += 1
    print(f"[SYNC] Prises de poste corrigées: {fix_count}")

    # 2. Synchronisation des anomalies
    print("[SYNC] Anomalies...")
    ano_ref = db.collection('anomalies')
    anomalies = list(ano_ref.stream())
    fix_count = 0
    for doc in anomalies:
        data = doc.to_dict()
        doc_id = doc.id
        file_id = data.get('photo_file_id')
        photo_url = data.get('photoURL')
        if file_id and not photo_url:
            # Cherche dans photos par file_id exact
            photos = db.collection('photos').where('photo_file_id', '==', file_id).limit(1).stream()
            url = None
            for p in photos:
                p_data = p.to_dict()
                url = p_data.get('photoURL') or p_data.get('url')
                break
            if not url:
                try:
                    local_path = f"temp_anomalie_{doc_id}.jpg"
                    await download_telegram_photo(file_id, local_path)
                    storage_path = f"anomalies/{data.get('operatorId','unknown')}/{doc_id}.jpg"
                    url = upload_photo_to_storage(local_path, storage_path)
                    # Crée le doc dans photos avec le bon operatorId
                    if url:
                        db.collection('photos').add({
                            'photo_file_id': file_id,
                            'photoURL': url,
                            'operatorId': data.get('operatorId'),
                            'timestamp': data.get('timestamp'),
                            'type': 'anomalie',
                        })
                    os.remove(local_path)
                    fix_count += 1
                    print(f"[OK] Anomalie {doc_id} => {url}")
                except Exception as e:
                    print(f"[ERR] Impossible d'uploader photo anomalie {doc_id}: {e}")
            else:
                ano_ref.document(doc.id).update({'photoURL': url})
    print(f"[SYNC] Anomalies corrigées: {fix_count}")

    # 3. Synchronisation des urgences (optionnel)
    print("[SYNC] Urgences...")
    urg_ref = db.collection('urgences')
    urgences = list(urg_ref.stream())
    fix_count = 0
    for doc in urgences:
        data = doc.to_dict()
        doc_id = doc.id
        file_id = data.get('photo_file_id')
        photo_url = data.get('photoURL')
        if file_id and not photo_url:
            # Cherche dans photos par file_id exact
            photos = db.collection('photos').where('photo_file_id', '==', file_id).limit(1).stream()
            url = None
            for p in photos:
                p_data = p.to_dict()
                url = p_data.get('photoURL') or p_data.get('url')
                break
            if not url:
                try:
                    local_path = f"temp_urgence_{doc_id}.jpg"
                    await download_telegram_photo(file_id, local_path)
                    storage_path = f"urgences/{data.get('operatorId','unknown')}/{doc_id}.jpg"
                    url = upload_photo_to_storage(local_path, storage_path)
                    # Crée le doc dans photos avec le bon operatorId
                    if url:
                        db.collection('photos').add({
                            'photo_file_id': file_id,
                            'photoURL': url,
                            'operatorId': data.get('operatorId'),
                            'timestamp': data.get('timestamp'),
                            'type': 'urgence',
                        })
                    os.remove(local_path)
                    fix_count += 1
                    print(f"[OK] Urgence {doc_id} => {url}")
                except Exception as e:
                    print(f"[ERR] Impossible d'uploader photo urgence {doc_id}: {e}")
            else:
                urg_ref.document(doc.id).update({'photoURL': url})
    print(f"[SYNC] Urgences corrigées: {fix_count}")

    # 4. Synchronisation des photos de fin de poste dans positions_log
    print("[SYNC] Fin de poste (positions_log)...")
    fin_ref = db.collection('positions_log')
    fin_docs = list(fin_ref.where('type', '==', 'fin_de_poste').stream())
    fix_count = 0
    for doc in fin_docs:
        data = doc.to_dict()
        doc_id = doc.id
        file_id = data.get('photo_file_id')
        photo_url = data.get('photoURL')
        if file_id and not photo_url:
            # Cherche dans photos par file_id exact
            photos = db.collection('photos').where('photo_file_id', '==', file_id).limit(1).stream()
            url = None
            for p in photos:
                p_data = p.to_dict()
                url = p_data.get('photoURL') or p_data.get('url')
                break
            if not url:
                try:
                    local_path = f"temp_fin_{doc_id}.jpg"
                    await download_telegram_photo(file_id, local_path)
                    storage_path = f"fin_de_poste/{data.get('operatorId','unknown')}/{doc_id}.jpg"
                    url = upload_photo_to_storage(local_path, storage_path)
                    # Crée le doc dans photos avec le bon operatorId
                    if url:
                        db.collection('photos').add({
                            'photo_file_id': file_id,
                            'photoURL': url,
                            'operatorId': data.get('operatorId'),
                            'timestamp': data.get('timestamp'),
                            'type': 'fin_de_poste',
                        })
                    os.remove(local_path)
                    fix_count += 1
                    print(f"[OK] Fin de poste {doc_id} => {url}")
                except Exception as e:
                    print(f"[ERR] Impossible d'uploader photo fin_de_poste {doc_id}: {e}")
            else:
                fin_ref.document(doc.id).update({'photoURL': url})
    print(f"[SYNC] Fin de poste corrigées: {fix_count}")

    # 4. Correction des timestamps (optionnel)
    # À compléter selon besoin

    print("[SYNC] Terminé. Toutes les collections sont synchronisées.")

    # 5. Suppression des doublons dans la collection photos
    print("[CLEANUP] Suppression des doublons dans la collection photos...")
    seen = {}
    to_delete = []
    for doc in db.collection('photos').stream():
        data = doc.to_dict()
        key = (data.get('photo_file_id'), data.get('operatorId'))
        if key in seen:
            to_delete.append(doc.id)
        else:
            seen[key] = doc.id
    for doc_id in to_delete:
        db.collection('photos').document(doc_id).delete()
        print(f"  🗑️ Doublon supprimé : {doc_id}")
    print(f"[CLEANUP] {len(to_delete)} doublons supprimés dans photos.")

if __name__ == "__main__":
    asyncio.run(sync_all()) 