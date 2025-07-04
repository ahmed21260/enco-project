from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters, ContextTypes
from utils.firestore import db
from datetime import datetime

# États du wizard
TYPE_RAPPORT, DESCRIPTION, PHOTO, CONFIRM = range(4)

# Types de rapports techniques
RAPPORT_TYPES = [
    ["🔧 Rapport maintenance", "📊 Rapport performance"],
    ["🛠️ Rapport réparation", "📋 Rapport inspection"],
    ["⚙️ Rapport technique général", "Autre type de rapport"]
]

async def start_rapport_wizard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 **RAPPORT TECHNIQUE**\n\n"
        "Sélectionne le type de rapport :",
        reply_markup=ReplyKeyboardMarkup(RAPPORT_TYPES, one_time_keyboard=True, resize_keyboard=True)
    )
    return TYPE_RAPPORT

async def receive_type_rapport(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['type_rapport'] = update.message.text
    
    await update.message.reply_text(
        f"📋 **{update.message.text}**\n\n"
        f"Décris le rapport technique en détail :\n"
        f"• Observations\n"
        f"• Actions réalisées\n"
        f"• Recommandations\n"
        f"• Problèmes identifiés\n\n"
        f"Tape 'skip' si tu veux passer cette étape."
    )
    return DESCRIPTION

async def receive_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text and update.message.text.lower() == 'skip':
        context.user_data['description'] = ''
    else:
        context.user_data['description'] = update.message.text or ''
    
    await update.message.reply_text(
        "📸 Envoie une photo pour illustrer le rapport (optionnel, tape 'skip' pour passer) :"
    )
    return PHOTO

async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text and update.message.text.lower() == 'skip':
        context.user_data['photo_file_id'] = None
    elif update.message.photo:
        context.user_data['photo_file_id'] = update.message.photo[-1].file_id
    else:
        await update.message.reply_text("❗ Envoie une photo ou tape 'skip' pour passer.")
        return PHOTO
    
    # Récapitulatif
    type_rapport = context.user_data.get('type_rapport', '')
    description = context.user_data.get('description', 'Aucune')
    photo = 'Oui' if context.user_data.get('photo_file_id') else 'Non'
    
    await update.message.reply_text(
        f"📋 **Récapitulatif Rapport Technique**\n\n"
        f"📋 Type : {type_rapport}\n"
        f"📝 Description : {description}\n"
        f"📸 Photo : {photo}\n\n"
        f"✅ Confirme l'envoi du rapport ? (oui/non)"
    )
    return CONFIRM

async def confirm_rapport(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.lower() != "oui":
        await update.message.reply_text("❌ Rapport annulé.")
        return ConversationHandler.END
    
    user = update.message.from_user
    
    # Données pour Firestore
    rapport_data = {
        "operatorId": user.id,
        "operatorName": user.full_name,
        "timestamp": datetime.now().isoformat(),
        "type_rapport": context.user_data.get('type_rapport', ''),
        "description": context.user_data.get('description', ''),
        "photo_file_id": context.user_data.get('photo_file_id'),
        "type": "rapport_technique",
        "handled": False
    }
    
    try:
        db.collection('rapports_techniques').add(rapport_data)
        await update.message.reply_text(
            "✅ **RAPPORT TECHNIQUE ENREGISTRÉ !**\n\n"
            f"📋 Le rapport a été transmis à l'encadrement.\n"
            f"📝 Description et photo enregistrées.\n"
            f"🔄 Tu seras contacté pour le suivi.",
            reply_markup=ReplyKeyboardMarkup(
                [
                    ["Menu principal", "Nouveau rapport technique"],
                    ["Déclarer une panne", "URGENCE SNCF"]
                ], resize_keyboard=True
            )
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur lors de l'enregistrement : {str(e)}")
    
    return ConversationHandler.END

def get_rapport_wizard_handler():
    return ConversationHandler(
        entry_points=[
            CommandHandler("rapport", start_rapport_wizard),
            MessageHandler(filters.Regex("^🔧 Rapport technique machine$"), start_rapport_wizard)
        ],
        states={
            TYPE_RAPPORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_type_rapport)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_description)],
            PHOTO: [MessageHandler(filters.PHOTO | filters.TEXT, receive_photo)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_rapport)],
        },
        fallbacks=[]
    ) 