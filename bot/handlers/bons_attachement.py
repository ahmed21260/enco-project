from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters, ContextTypes
from utils.firestore import db
import os
from datetime import datetime

# États du wizard
UPLOAD_DOC, SAISIE_INFOS, CONFIRM = range(3)

async def start_bon_wizard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📄 **Bon d'attachement**\n\n"
        "Envoie une photo ou un document PDF du bon d'attachement (obligatoire).",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("❌ Annuler")]],
            one_time_keyboard=True, resize_keyboard=True
        )
    )
    return UPLOAD_DOC

async def receive_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text and update.message.text == "❌ Annuler":
        await update.message.reply_text("❌ Bon d'attachement annulé.")
        return ConversationHandler.END
    
    # Vérifier si c'est une photo ou un document
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        file_type = "photo"
    elif update.message.document:
        file_id = update.message.document.file_id
        file_type = "document"
        # Vérifier que c'est un PDF
        if not update.message.document.mime_type or "pdf" not in update.message.document.mime_type.lower():
            await update.message.reply_text("❗ Seuls les fichiers PDF sont acceptés pour les documents.")
            return UPLOAD_DOC
    else:
        await update.message.reply_text("❗ Envoie une photo ou un document PDF du bon d'attachement.")
        return UPLOAD_DOC
    
    context.user_data['file_id'] = file_id
    context.user_data['file_type'] = file_type
    
    await update.message.reply_text(
        "✅ Document reçu.\n\n"
        "Saisis les informations du bon d'attachement :\n"
        "• Numéro du bon\n"
        "• Type de travail\n"
        "• Description (optionnel)\n\n"
        "Format : numéro|type|description\n"
        "Exemple : BON-2024-001|Maintenance|Réparation signalisation"
    )
    return SAISIE_INFOS

async def receive_infos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Annuler":
        await update.message.reply_text("❌ Bon d'attachement annulé.")
        return ConversationHandler.END
    
    # Parser les informations
    parts = update.message.text.split('|')
    if len(parts) < 2:
        await update.message.reply_text("❗ Format incorrect. Utilise : numéro|type|description")
        return SAISIE_INFOS
    
    numero = parts[0].strip()
    type_travail = parts[1].strip()
    description = parts[2].strip() if len(parts) > 2 else ""
    
    context.user_data['numero'] = numero
    context.user_data['type_travail'] = type_travail
    context.user_data['description'] = description
    
    await update.message.reply_text(
        f"📋 **Récapitulatif Bon d'attachement**\n\n"
        f"📄 Numéro : {numero}\n"
        f"🔧 Type : {type_travail}\n"
        f"📝 Description : {description or 'Aucune'}\n"
        f"📎 Type de fichier : {context.user_data['file_type']}\n\n"
        f"Confirmer l'enregistrement ? (oui/non)"
    )
    return CONFIRM

async def confirm_bon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.lower() != "oui":
        await update.message.reply_text("❌ Bon d'attachement annulé.")
        return ConversationHandler.END
    
    user = update.message.from_user
    
    # Enregistrer dans Firestore
    bon_data = {
        "operatorId": user.id,
        "operatorName": user.full_name,
        "timestamp": datetime.now().isoformat(),
        "numero": context.user_data['numero'],
        "type_travail": context.user_data['type_travail'],
        "description": context.user_data['description'],
        "file_id": context.user_data['file_id'],
        "file_type": context.user_data['file_type'],
        "type": "bon_attachement"
    }
    
    try:
        db.collection('bons_attachement').add(bon_data)
        await update.message.reply_text(
            "✅ Bon d'attachement enregistré avec succès !",
            reply_markup=ReplyKeyboardMarkup(
                [
                    ["Voir ma localisation & infos", "Déclarer une panne"],
                    ["URGENCE SNCF", "Envoyer photo en cours de mission"],
                    ["Fin de poste / Bon papier", "Coffre-fort machine"],
                    ["Outils ferroviaires / Géoportail SNCF", "Modifier ma machine / chantier"],
                    ["Voir mes stats", "Clôturer ma session"]
                ], resize_keyboard=True
            )
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur lors de l'enregistrement : {str(e)}")
    
    return ConversationHandler.END

def get_bon_wizard_handler():
    return ConversationHandler(
        entry_points=[
            CommandHandler("bon", start_bon_wizard),
            MessageHandler(filters.Regex("^Bon d'attachement$"), start_bon_wizard)
        ],
        states={
            UPLOAD_DOC: [MessageHandler(filters.PHOTO | filters.Document.ALL | filters.TEXT, receive_document)],
            SAISIE_INFOS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_infos)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_bon)],
        },
        fallbacks=[]
    ) 