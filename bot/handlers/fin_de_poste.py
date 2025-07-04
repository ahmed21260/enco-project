from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters, ContextTypes
from utils.firestore import db

PHOTO, CONFIRM = range(2)

async def start_fin_wizard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📷 Merci d'envoyer une photo du bon d’attachement papier signé (obligatoire, JPG/PDF max 5 Mo) :"
    )
    return PHOTO

async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("❗ Photo obligatoire pour clôturer la fin de poste.")
        return PHOTO
    context.user_data['photo'] = update.message.photo[-1].file_id
    await update.message.reply_text("✅ Confirme la clôture de la fin de poste ? (oui/non)")
    return CONFIRM

async def confirm_fin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.lower() != "oui":
        await update.message.reply_text("❌ Clôture annulée.")
        return ConversationHandler.END
    user = update.message.from_user
    # Suppression/MAJ Firestore : positions_operateurs (désactivation ou suppression)
    doc_id = str(user.id)
    try:
        db.collection('positions_operateurs').document(doc_id).update({"type": "fin_de_poste", "actif": False})
    except Exception:
        db.collection('positions_operateurs').document(doc_id).delete()
    # Historique détaillé
    db.collection('positions_log').add({
        "operateur_id": user.id,
        "operatorId": user.id,
        "nom": user.full_name,
        "timestamp": update.message.date.isoformat(),
        "type": "fin_de_poste",
        "photo_file_id": context.user_data.get('photo')
    })
    await update.message.reply_text("✅ Fin de poste enregistrée et opérateur retiré de la carte !", reply_markup=ReplyKeyboardMarkup(
        [
            ["Menu principal", "Commencer ma prise de poste"],
            ["Envoyer photo en cours de mission", "Voir mes stats"]
        ], resize_keyboard=True
    ))
    await update.message.reply_text("✅ Poste terminé. Merci pour ton travail aujourd’hui 💪\nTon bon est bien enregistré. À demain !")
    return ConversationHandler.END

def get_fin_wizard_handler():
    return ConversationHandler(
        entry_points=[
            CommandHandler("fin", start_fin_wizard),
            MessageHandler(filters.Regex("^Fin de poste / Bon papier$"), start_fin_wizard)
        ],
        states={
            PHOTO: [MessageHandler(filters.PHOTO, receive_photo)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_fin)],
        },
        fallbacks=[]
    ) 