import os
from dotenv import load_dotenv
load_dotenv()
import firebase_admin
from firebase_admin import credentials, firestore
from telegram import Bot
import asyncio

# Config
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN manquant dans les variables d'environnement !")
CRED_PATH = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'firebase_credential.json')
BUCKET = os.environ.get('FIREBASE_STORAGE_BUCKET', 'enco-prestarail.firebasestorage.app')
if not os.path.exists(CRED_PATH):
    raise FileNotFoundError(f"Fichier de credentials Firebase introuvable: {CRED_PATH}")
if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.Certificate(CRED_PATH), {'storageBucket': BUCKET})
db = firestore.client()
from utils.firestore import upload_photo_to_storage

from telegram import Bot
from telegram.constants import ChatAction
from telegram.request import HTTPXRequest

bot = Bot(token=BOT_TOKEN, request=HTTPXRequest())

async def migrate_anomalies():
    anomalies_ref = db.collection('anomalies')
    docs = list(anomalies_ref.stream())
    updated = 0
    skipped = 0
    for doc in docs:
        data = doc.to_dict()
        file_id = data.get('photo_file_id')
        if not file_id or data.get('photoURL'):
            skipped += 1
            continue
        user_id = data.get('operateur_id') or data.get('operatorId') or 'unknown'
        # Télécharger la photo depuis Telegram
        try:
            file = await bot.get_file(file_id)
            local_dir = f"bot/photos/{user_id}"
            os.makedirs(local_dir, exist_ok=True)
            file_name = f"{user_id}_anomalie_{data.get('timestamp','')}.jpg"
            file_path = f"{local_dir}/{file_name}"
            await file.download_to_drive(file_path)
            storage_path = f"anomalies/{user_id}/{file_name}"
            photo_url = upload_photo_to_storage(file_path, storage_path)
            if photo_url:
                anomalies_ref.document(doc.id).update({'photoURL': photo_url})
                updated += 1
                print(f"✅ Anomalie {doc.id} mise à jour avec photoURL")
            else:
                print(f"❌ Upload Storage échoué pour {doc.id}")
        except Exception as e:
            print(f"❌ Erreur pour {doc.id}: {e}")
            continue
    print(f"Terminé. {updated} anomalies mises à jour, {skipped} ignorées (déjà OK ou sans photo_file_id)")

if __name__ == "__main__":
    asyncio.run(migrate_anomalies()) 