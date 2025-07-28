import os
from dotenv import load_dotenv
load_dotenv()
import firebase_admin
from firebase_admin import credentials, firestore
from telegram import Bot
import asyncio

# --- Sécurité credentials ---
CRED_PATH = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'serviceAccountKey_railway.txt')
BUCKET = os.environ.get('FIREBASE_STORAGE_BUCKET', 'enco-prestarail.firebasestorage.app')
if not os.path.exists(CRED_PATH):
    raise FileNotFoundError(f"Fichier de credentials Firebase introuvable: {CRED_PATH}")
try:
    if not firebase_admin._apps:
        firebase_admin.initialize_app(
            credentials.Certificate(CRED_PATH),
            {'storageBucket': BUCKET}
        )
except Exception as e:
    print(f"❌ Erreur d'initialisation Firebase : {e}")
    exit(1)
db = firestore.client()

# --- Telegram Bot pour download file_id si besoin ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    print("❌ BOT_TOKEN manquant, impossible de synchroniser les photos Telegram.")
    bot = None
else:
    from telegram.request import HTTPXRequest
    bot = Bot(token=BOT_TOKEN, request=HTTPXRequest())
from utils.firestore import upload_photo_to_storage

# --- Collections et champs critiques ---
COLLECTIONS = {
    'prises_poste': {'file_ids': 'photos_file_ids', 'urls': 'photos_urls'},
    'anomalies': {'file_id': 'photo_file_id', 'url': 'photoURL'},
    'photos': {'file_id': 'photo_file_id', 'url': 'photoURL'},
    'urgences': {'file_id': 'photo_file_id', 'url': 'photoURL'},
    'bons_attachement': {'file_id': 'file_id', 'url': 'urlDocument'},
    'positions_log': {'file_id': 'photo_file_id', 'url': 'photoURL', 'type_filter': 'fin_de_poste'},
}

async def sync_and_check():
    rapport = []
    for coll, fields in COLLECTIONS.items():
        print(f"\n=== Analyse de la collection {coll} ===")
        ref = db.collection(coll)
        
        # Traitement spécial pour positions_log avec filtrage par type
        if coll == 'positions_log' and 'type_filter' in fields:
            docs = list(ref.where('type', '==', fields['type_filter']).stream())
            print(f"  📋 Filtrage sur type: {fields['type_filter']}")
        else:
            docs = list(ref.stream())
            
        ok, ko, fixed = 0, 0, 0
        for doc in docs:
            data = doc.to_dict()
            update = {}
            # Prises de poste : tableau d'IDs et d'URLs
            if coll == 'prises_poste':
                file_ids = data.get(fields['file_ids'], [])
                urls = data.get(fields['urls'], [])
                if file_ids and (not urls or len(urls) != len(file_ids)):
                    new_urls = []
                    for file_id in file_ids:
                        # Cherche dans photos par file_id exact
                        photos = db.collection('photos').where('photo_file_id', '==', file_id).limit(1).stream()
                        url = None
                        for p in photos:
                            p_data = p.to_dict()
                            url = p_data.get('photoURL') or p_data.get('url')
                            break
                        # Si pas trouvé, tente download/upload
                        if not url and bot:
                            try:
                                file = await bot.get_file(file_id)
                                local_dir = f"bot/photos/sync/{doc.id}"
                                os.makedirs(local_dir, exist_ok=True)
                                file_name = f"{doc.id}_prise_{file_id}.jpg"
                                file_path = f"{local_dir}/{file_name}"
                                await file.download_to_drive(file_path)
                                storage_path = f"prises_poste/{doc.id}/{file_name}"
                                url = upload_photo_to_storage(file_path, storage_path)
                                # Crée le doc dans photos avec le bon operatorId
                                if url:
                                    db.collection('photos').add({
                                        'photo_file_id': file_id,
                                        'photoURL': url,
                                        'operatorId': data.get('operatorId'),
                                        'timestamp': data.get('timestamp'),
                                        'type': 'prise_de_poste',
                                    })
                            except Exception as e:
                                print(f"  ❌ Erreur download/upload prise {doc.id} : {e}")
                        new_urls.append(url)
                    update[fields['urls']] = new_urls
                    ref.document(doc.id).update(update)
                    fixed += 1
                if file_ids and urls and len(urls) == len(file_ids) and all(urls):
                    ok += 1
                else:
                    ko += 1
            else:
                file_id = data.get(fields.get('file_id'))
                url = data.get(fields.get('url'))
                if file_id and not url and bot:
                    try:
                        file = await bot.get_file(file_id)
                        local_dir = f"bot/photos/sync/{coll}/{doc.id}"
                        os.makedirs(local_dir, exist_ok=True)
                        file_name = f"{doc.id}_{file_id}.jpg"
                        file_path = f"{local_dir}/{file_name}"
                        await file.download_to_drive(file_path)
                        storage_path = f"{coll}/{doc.id}/{file_name}"
                        url = upload_photo_to_storage(file_path, storage_path)
                        if url:
                            ref.document(doc.id).update({fields['url']: url})
                            fixed += 1
                    except Exception as e:
                        print(f"  ❌ Erreur download/upload {coll} {doc.id} : {e}")
                if file_id and url:
                    ok += 1
                elif file_id:
                    ko += 1
        rapport.append(f"{coll}: {ok} OK, {fixed} corrigés, {ko} KO")
    print("\n=== RAPPORT FINAL SYNCHRO FIREBASE ===")
    for line in rapport:
        print(line)
    print("\nSynchronisation terminée.")

if __name__ == "__main__":
    asyncio.run(sync_and_check()) 