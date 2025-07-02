from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from utils.firestore import save_position

GEOLOC = 0

async def start_prise(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 **Prise de poste**\n\nMerci d'envoyer votre position pour commencer votre poste.",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📍 Envoyer ma position", request_location=True)]],
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )
    return GEOLOC

async def save_geoloc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    loc = update.message.location
    
    # Sauvegarde de la position
    position_data = {
        "operateur_id": user.id,
        "nom": user.full_name,
        "timestamp": update.message.date.isoformat(),
        "latitude": loc.latitude,
        "longitude": loc.longitude,
        "type": "prise_de_poste"
    }
    
    save_position(position_data)
    
    await update.message.reply_text(
        "✅ **Prise de poste enregistrée !**\n\n"
        f"👤 Opérateur : {user.full_name}\n"
        f"📍 Position : {loc.latitude:.4f}, {loc.longitude:.4f}\n"
        f"🕐 Heure : {update.message.date.strftime('%H:%M')}\n\n"
        "Vous pouvez maintenant utiliser /checklist pour la vérification sécurité."
    )
    return ConversationHandler.END

def get_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("prise", start_prise)],
        states={GEOLOC: [MessageHandler(filters.LOCATION, save_geoloc)]},
        fallbacks=[]
    ) 