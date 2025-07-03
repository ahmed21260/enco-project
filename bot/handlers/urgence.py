from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
import os
from utils.firestore import save_position, upload_photo_to_storage
from PIL import Image

GEOLOC_URGENCE = 0

async def urgence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler pour déclencher une urgence"""
    await update.message.reply_text(
        "🚨 **URGENCE - ALERTE IMMÉDIATE**\n\n"
        "Une urgence a été déclenchée. Votre position sera transmise à l'encadrement.\n"
        "Envoyez votre position pour localisation :",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📍 Envoyer ma position", request_location=True)]],
            one_time_keyboard=True,
            resize_keyboard=True
        ),
        parse_mode="Markdown"
    )
    return GEOLOC_URGENCE

async def hors_voie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler pour mise hors voie urgente"""
    await update.message.reply_text(
        "⚠️ **MISE HORS VOIE URGENTE**\n\n"
        "Procédure d'évacuation immédiate activée.\n"
        "Envoyez votre position pour assistance :",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📍 Envoyer ma position", request_location=True)]],
            one_time_keyboard=True,
            resize_keyboard=True
        ),
        parse_mode="Markdown"
    )
    return GEOLOC_URGENCE

async def save_urgence_geoloc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sauvegarder la position d'urgence"""
    user = update.message.from_user
    loc = update.message.location
    urgence_type = context.user_data.get('urgence_type', 'inconnue')
    incident_data = {
        "operateur_id": user.id,
        "operatorId": user.id,
        "nom": user.full_name,
        "timestamp": update.message.date.isoformat(),
        "position": {"lat": loc.latitude, "lng": loc.longitude},
        "type": urgence_type,
        "handled": False
    }
    from utils.firestore import db
    db.collection('incidents').add(incident_data)
    await update.message.reply_text("🆘 Urgence transmise ! L'encadrement est alerté.")
    context.user_data['urgence_step'] = None
    context.user_data['urgence_type'] = None

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    local_dir = f"bot/photos/{user.id}/urgence"
    os.makedirs(local_dir, exist_ok=True)
    file_name = f"urgence_{user.id}_{update.message.date.strftime('%Y%m%d_%H%M%S')}.jpg"
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
    storage_path = f"urgence/{user.id}/{file_name}"
    public_url = upload_photo_to_storage(resized_path, storage_path)
    # Log enrichi
    log_entry = {
        "operateur_id": user.id,
        "nom": user.full_name,
        "timestamp": update.message.date.isoformat(),
        "photo_path": file_path,
        "firebase_url": public_url,
        "type": "urgence"
    }
    with open("bot/photos_log.jsonl", "a", encoding="utf-8") as f:
        import json
        f.write(json.dumps(log_entry) + "\n")
    if public_url:
        await update.message.reply_text("📸 Photo d'urgence reçue, redimensionnée et uploadée sur le cloud !")
    else:
        await update.message.reply_text("❗ Erreur upload cloud, photo d'urgence sauvegardée localement.")

def get_urgence_handler():
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^Déclencher une urgence$"), urgence),
            MessageHandler(filters.Regex("^Mise hors voie urgente$"), hors_voie)
        ],
        states={GEOLOC_URGENCE: [MessageHandler(filters.LOCATION, save_urgence_geoloc)]},
        fallbacks=[
            MessageHandler(filters.PHOTO, handle_photo),
            MessageHandler(filters.Regex("^Envoyer une photo$"), lambda u, c: u.message.reply_text("Merci d'envoyer la photo maintenant."))
        ]
    ) 