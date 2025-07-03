from telegram import Update
from telegram.ext import ContextTypes
import os
from utils.firestore import upload_photo_to_storage
from PIL import Image
import tempfile

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.from_user or not update.message.photo:
        if update.message:
            await update.message.reply_text("❗ Erreur : message ou photo non reconnu.")
        return
    user = update.message.from_user
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)

    # Dossier local par opérateur
    local_dir = f"bot/photos/{user.id}"
    os.makedirs(local_dir, exist_ok=True)
    file_name = f"{user.id}_{update.message.date.strftime('%Y%m%d_%H%M%S')}.jpg"
    file_path = f"{local_dir}/{file_name}"
    await file.download_to_drive(file_path)

    # Redimensionnement (ex: max 1024x1024)
    resized_path = f"{local_dir}/resized_{file_name}"
    try:
        with Image.open(file_path) as img:
            img.thumbnail((1024, 1024))
            img.save(resized_path, "JPEG")
    except Exception as e:
        resized_path = file_path  # fallback si erreur
        print(f"Erreur resize: {e}")

    # Upload Firebase Storage (dans dossier par opérateur)
    storage_path = f"photos/{user.id}/{file_name}"
    public_url = upload_photo_to_storage(resized_path, storage_path)

    # Double structure
    log_entry = {
        "operateur_id": user.id,
        "operatorId": user.id,
        "timestamp": update.message.date.isoformat(),
        "photo_path": file_path,
        "firebase_url": public_url
    }
    with open("bot/photos_log.jsonl", "a", encoding="utf-8") as f:
        import json
        f.write(json.dumps(log_entry) + "\n")

    # Enregistrement Firestore (photos)
    from utils.firestore import db
    db.collection('photos').add({
        "operateur_id": user.id,
        "operatorId": user.id,
        "timestamp": update.message.date.isoformat(),
        "urlPhoto": public_url
    })

    if public_url:
        await update.message.reply_text("📸 Photo reçue, redimensionnée et uploadée sur le cloud !")
    else:
        await update.message.reply_text("❗ Erreur upload cloud, photo sauvegardée localement.")

async def transcribe_voice(voice_path):
    # MOCK : à remplacer par une vraie API (Google Speech, Whisper, etc.)
    return "[Transcription vocale ici]"

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.from_user or not update.message.voice:
        if update.message:
            await update.message.reply_text("❗ Erreur : message vocal non reconnu.")
        return
    user = update.message.from_user
    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as tmp:
        await file.download_to_drive(tmp.name)
        transcript = await transcribe_voice(tmp.name)
    # Associer ce commentaire à la dernière photo de l'utilisateur (mock)
    # Ici, on pourrait mettre à jour Firestore ou le log local
    await update.message.reply_text(f"🗣️ Commentaire vocal reçu : {transcript}")

async def start_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_photo(update, context) 