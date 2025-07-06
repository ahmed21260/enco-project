from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from utils.firestore import db, upload_photo_to_storage
import logging
import os
from datetime import datetime

# États de conversation
PHOTO, DESCRIPTION, GPS = range(3)

async def start_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Démarre le workflow d'envoi de photo"""
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    
    await update.message.reply_text(
        "📷 **Envoi de photo**\n\n"
        "Prends une photo de l'état ou du problème à signaler :",
        reply_markup=ReplyKeyboardMarkup([
            ["📷 Prendre une photo"],
            ["🤖 Aide IA"]
        ], resize_keyboard=True)
    )
    logging.info(f"[PHOTO] Début envoi photo pour user {update.effective_user.id}")
    return PHOTO

async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reçoit la photo et demande une description"""
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    
    if update.message.text in ["🤖 Aide IA", "💬 Aide IA"]:
        from services.enco_ai_assistant import ENCOAIAssistant
        assistant = ENCOAIAssistant()
        suggestion = await assistant.generate_railway_response("Aide demandée pour l'envoi de photo.")
        await update.message.reply_text(f"🤖 Suggestion IA : {suggestion}")
        return PHOTO
    
    if not update.message.photo:
        await update.message.reply_text(
            "❗ Merci d'envoyer une photo.",
            reply_markup=ReplyKeyboardMarkup([
                ["📷 Prendre une photo"],
                ["🤖 Aide IA"]
            ], resize_keyboard=True)
        )
        return PHOTO
    
    # Sauvegarder la photo
    context.user_data['photo'] = update.message.photo[-1].file_id
    
    await update.message.reply_text(
        "📝 Ajoute une description (optionnel, tape 'skip' pour passer) :",
        reply_markup=ReplyKeyboardMarkup([
            ["Ajouter une description"],
            ["skip"],
            ["🤖 Aide IA"]
        ], resize_keyboard=True)
    )
    logging.info(f"[PHOTO] Photo reçue pour user {update.effective_user.id}")
    return DESCRIPTION

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
    """Retourne le handler pour l'envoi de photos"""
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^📷 Envoyer une photo$"), start_photo)
        ],
        states={
            PHOTO: [MessageHandler(filters.PHOTO | filters.TEXT, receive_photo)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_description)],
            GPS: [MessageHandler(filters.LOCATION | filters.TEXT, receive_gps)],
        },
        fallbacks=[]
    ) 