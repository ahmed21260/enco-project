from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters, ContextTypes
from utils.firestore import db
from datetime import datetime

PHOTO, CONFIRM = range(2)

async def start_fin_wizard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    await update.message.reply_text(
        "📷 Merci d'envoyer une photo du bon d'attachement papier signé (obligatoire, JPG/PDF max 5 Mo) :"
    )
    return PHOTO

async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    if not update.message.photo:
        await update.message.reply_text("❗ Photo obligatoire pour clôturer la fin de poste.")
        return PHOTO
    context.user_data['photo'] = update.message.photo[-1].file_id
    await update.message.reply_text("✅ Confirme la clôture de la fin de poste ? (oui/non)")
    return CONFIRM

async def confirm_fin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    if not update.message.text:
        await update.message.reply_text("❌ Réponse invalide.")
        return CONFIRM
    if update.message.text.lower() != "oui":
        await update.message.reply_text("❌ Clôture annulée.")
        return ConversationHandler.END
    user = update.message.from_user
    if not user:
        await update.message.reply_text("❌ Erreur : utilisateur non trouvé.")
        return ConversationHandler.END
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
    await update.message.reply_text(
        "\u2705 Fin de poste enregistr\u00e9e et op\u00e9rateur retir\u00e9 de la carte !", reply_markup=ReplyKeyboardMarkup(
        [
            ["Menu principal", "Commencer ma prise de poste"],
            ["Envoyer photo en cours de mission", "Voir mes stats"]
        ], resize_keyboard=True
    ))
    # Ajout : gestion du retour menu principal
    if update.message.text == "Menu principal":
        from handlers.menu import start
        await start(update, context)
    await update.message.reply_text("✅ Poste terminé. Merci pour ton travail aujourd'hui 💪\nTon bon est bien enregistré. À demain !")
    return ConversationHandler.END

async def start_fin_de_poste(update, context):
    user = update.effective_user
    if not user:
        await update.message.reply_text("❌ Erreur : utilisateur non trouvé.")
        return ConversationHandler.END
    # Vérifie s'il y a déjà une fin de poste aujourd'hui
    today = datetime.now().date().isoformat()
    fin_docs = list(db.collection('positions_log')
        .where('operatorId', '==', str(user.id))
        .where('type', 'in', ['fin_de_poste', 'fin'])
        .where('timestamp', '>=', today)
        .stream())
    if fin_docs:
        await update.message.reply_text("❗ Tu as déjà enregistré une fin de poste aujourd'hui. Pas de doublon possible.")
        return ConversationHandler.END
    reply_markup = ReplyKeyboardMarkup([
        ["Confirmer fin de poste"],
        ["Menu principal"]
    ], resize_keyboard=True)
    await update.message.reply_text("Veux-tu vraiment enregistrer ta fin de poste ?", reply_markup=reply_markup)
    context.user_data['fin_de_poste_demande'] = True
    return CONFIRM

def get_fin_wizard_handler():
    return ConversationHandler(
        entry_points=[
            CommandHandler("fin", start_fin_wizard),
            MessageHandler(filters.Regex(r"^Fin de poste$"), start_fin_wizard)
        ],
        states={
            PHOTO: [MessageHandler(filters.PHOTO | filters.TEXT & ~filters.COMMAND, receive_photo)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_fin)],
        },
        fallbacks=[]
    )

def get_fin_de_poste_handler():
    return ConversationHandler(
        entry_points=[
            CommandHandler("fin_de_poste", start_fin_de_poste),
            MessageHandler(filters.Regex(r"^🔴 Fin de poste$"), start_fin_de_poste)
        ],
        states={
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_fin)],
        },
        fallbacks=[]
    ) 