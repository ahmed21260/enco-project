from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from utils.firestore import db, upload_photo_to_storage
import logging
import os
from datetime import datetime
from PIL import Image

# États de conversation
PHOTO, DESCRIPTION, GPS = range(3)

async def start_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    await update.message.reply_text(
        "📷 **ENVOI DE PHOTO**\n\n"
        "Envoie une photo avec une description (optionnel) :"
    )
    return PHOTO

async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    
    if update.message.photo:
        # Traitement de la photo
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        
        # Créer le dossier local
        user = update.effective_user
        if not user:
            await update.message.reply_text("❌ Erreur : utilisateur non trouvé.")
            return ConversationHandler.END
        local_dir = f"bot/photos/{user.id}"
        os.makedirs(local_dir, exist_ok=True)
        
        # Nom du fichier
        file_name = f"{user.id}_photo_{update.message.date.strftime('%Y%m%d_%H%M%S')}.jpg"
        file_path = f"{local_dir}/{file_name}"
        
        # Télécharger et optimiser
        await file.download_to_drive(file_path)
        
        # Optimiser l'image
        try:
            with Image.open(file_path) as img:
                img.thumbnail((1024, 1024))
                img.save(file_path, "JPEG")
        except Exception as e:
            print(f"Erreur resize: {e}")
        
        # Upload vers Firebase Storage
        from utils.firestore import upload_photo_to_storage
        storage_path = f"photos/{user.id}/{file_name}"
        photoURL = upload_photo_to_storage(file_path, storage_path)
        
        # Enregistrer dans Firestore
        photo_data = {
            "operatorId": user.id,
            "operatorName": user.full_name,
            "timestamp": update.message.date.isoformat(),
            "photoURL": photoURL,
            "description": context.user_data.get('description', ''),
            "type": "photo_mission"
        }
        
        try:
            db.collection('photos').add(photo_data)
            await update.message.reply_text(
                "✅ Photo enregistrée avec succès !",
                reply_markup=ReplyKeyboardMarkup([
                    ["Menu principal", "Envoyer une autre photo"],
                    ["Déclarer une panne", "URGENCE SNCF"]
                ], resize_keyboard=True)
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Erreur lors de l'enregistrement : {str(e)}")
        
        return ConversationHandler.END
    else:
        await update.message.reply_text("❗ Envoie une photo valide.")
        return PHOTO

async def receive_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reçoit la description et demande la localisation"""
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    
    if update.message.text in ["🤖 Aide IA", "💬 Aide IA"]:
        from services.enco_ai_assistant import ENCOAIAssistant
        assistant = ENCOAIAssistant()
        suggestion = await assistant.generate_railway_response("Aide demandée pour la description de photo.")
        await update.message.reply_text(f"🤖 Suggestion IA : {suggestion}")
        return DESCRIPTION
    
    if update.message.text and update.message.text.lower() == 'skip':
        context.user_data['description'] = ''
    else:
        context.user_data['description'] = update.message.text or ''
    
    await update.message.reply_text(
        "📍 Envoie ta localisation GPS (optionnel, tape 'skip' pour passer) :",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("📍 Envoyer ma position", request_location=True)],
            ["skip"],
            ["🤖 Aide IA"]
        ], one_time_keyboard=True, resize_keyboard=True)
    )
    logging.info(f"[PHOTO] Description reçue pour user {update.effective_user.id}")
    return GPS

async def receive_gps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Finalise l'envoi de photo avec localisation"""
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    
    if update.message.text in ["🤖 Aide IA", "💬 Aide IA"]:
        from services.enco_ai_assistant import ENCOAIAssistant
        assistant = ENCOAIAssistant()
        suggestion = await assistant.generate_railway_response("Aide demandée pour la localisation de photo.")
        await update.message.reply_text(f"🤖 Suggestion IA : {suggestion}")
        return GPS
    
    user = update.effective_user
    photo_file_id = context.user_data.get('photo')
    description = context.user_data.get('description', '')
    
    # Préparer les données pour Firestore
    photo_data = {
        "operateur_id": user.id,
        "operatorId": user.id,
        "nom": user.full_name,
        "timestamp": datetime.now().isoformat(),
        "photo_file_id": photo_file_id,
        "description": description,
        "type": "photo_utilisateur"
    }
    
    # Ajouter la localisation si fournie
    if update.message.location:
        photo_data["latitude"] = update.message.location.latitude
        photo_data["longitude"] = update.message.location.longitude
        photo_data["position"] = {
            "lat": update.message.location.latitude,
            "lng": update.message.location.longitude
        }
    
    # Sauvegarder dans Firestore
    try:
        db.collection('photos').add(photo_data)
        logging.info(f"[PHOTO] Enregistrée pour user {user.id}")
        
        await update.message.reply_text(
            "✅ **Photo enregistrée !**\n\n"
            "📷 Photo sauvegardée dans le système.\n"
            "📝 Description ajoutée au dossier.",
            reply_markup=ReplyKeyboardMarkup([
                ["📷 Envoyer une autre photo"],
                ["Menu principal"]
            ], resize_keyboard=True)
        )
    except Exception as e:
        logging.error(f"[PHOTO] Erreur Firestore: {e}")
        await update.message.reply_text(
            "❌ Erreur lors de l'enregistrement. Merci de réessayer.",
            reply_markup=ReplyKeyboardMarkup([
                ["Menu principal"]
            ], resize_keyboard=True)
        )
    
    return ConversationHandler.END

def get_photo_handler():
    return ConversationHandler(
        entry_points=[
            CommandHandler("photo", start_photo),
            MessageHandler(filters.Regex(r"^📷 Envoyer une photo$"), start_photo)
        ],
        states={
            PHOTO: [MessageHandler(filters.PHOTO | filters.TEXT & ~filters.COMMAND, receive_photo)],
        },
        fallbacks=[]
    ) 