from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from utils.firestore import save_anomalie, upload_photo_to_storage
import os
from PIL import Image
from firebase_admin import storage

DESCRIPTION, PHOTO, GEOLOC = range(3)

# type: ignore
async def start_anomalie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚨 Merci de décrire l'anomalie rencontrée.")
    return DESCRIPTION

async def receive_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['anomalie'] = {'description': update.message.text}
    await update.message.reply_text("📷 Vous pouvez envoyer une photo (ou tapez 'skip' pour passer).")
    return PHOTO

async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)

    # Dossier local par opérateur
    local_dir = f"bot/photos/{user.id}/anomalies"
    os.makedirs(local_dir, exist_ok=True)
    file_name = f"anomalie_{user.id}_{update.message.date.strftime('%Y%m%d_%H%M%S')}.jpg"
    file_path = f"{local_dir}/{file_name}"
    await file.download_to_drive(file_path)

    # Redimensionnement
    resized_path = f"{local_dir}/resized_{file_name}"
    try:
        with Image.open(file_path) as img:
            img.thumbnail((1024, 1024))
            img.save(resized_path, "JPEG")
    except Exception as e:
        resized_path = file_path
        print(f"Erreur resize: {e}")

    # Upload Firebase Storage
    storage_path = f"anomalies/{user.id}/{file_name}"
    public_url = upload_photo_to_storage(resized_path, storage_path)

    context.user_data['anomalie']['photo_path'] = file_path
    context.user_data['anomalie']['firebase_url'] = public_url

    await update.message.reply_text("📍 Merci d'envoyer votre position (ou tapez 'skip' pour passer).")
    return GEOLOC

async def skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📍 Merci d'envoyer votre position (ou tapez 'skip' pour passer).")
    return GEOLOC

async def receive_geoloc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loc = update.message.location
    context.user_data['anomalie']['latitude'] = loc.latitude
    context.user_data['anomalie']['longitude'] = loc.longitude
    return await save_and_confirm(update, context)

async def skip_geoloc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await save_and_confirm(update, context)

async def save_and_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    data = context.user_data['anomalie']
    data['operateur_id'] = user.id
    data['nom'] = user.full_name
    data['timestamp'] = update.message.date.isoformat()
    save_anomalie(data)
    await update.message.reply_text("✅ Anomalie enregistrée et transmise à l'encadrement. Merci pour votre vigilance !")
    return ConversationHandler.END

def get_anomalie_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("anomalie", start_anomalie), MessageHandler(filters.Regex("^Signaler une anomalie$"), start_anomalie)],
        states={
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_description)],
            PHOTO: [MessageHandler(filters.PHOTO, receive_photo), MessageHandler(filters.Regex("^skip$"), skip_photo)],
            GEOLOC: [MessageHandler(filters.LOCATION, receive_geoloc), MessageHandler(filters.Regex("^skip$"), skip_geoloc)]
        },
        fallbacks=[]
    )

# À intégrer dans le dispatcher du bot dans main.py 