from telegram import Update
from telegram.ext import ContextTypes
import os
from utils.firestore import upload_photo_to_storage
from PIL import Image

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

    # Log enrichi
    log_entry = {
        "operateur_id": user.id,
        "nom": user.full_name,
        "timestamp": update.message.date.isoformat(),
        "photo_path": file_path,
        "firebase_url": public_url
    }
    with open("bot/photos_log.jsonl", "a", encoding="utf-8") as f:
        import json
        f.write(json.dumps(log_entry) + "\n")

    if public_url:
        await update.message.reply_text("📸 Photo reçue, redimensionnée et uploadée sur le cloud !")
    else:
        await update.message.reply_text("❗ Erreur upload cloud, photo sauvegardée localement.") 