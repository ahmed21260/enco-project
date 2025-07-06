from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

# Fonction partagée pour afficher le menu principal du bot ENCO
MENU_KEYBOARD = [
    ["📌 Prise de poste", "📷 Envoyer une photo"],
    ["📄 Bon d'attachement", "🛑 URGENCE / INCIDENT"],
    ["🔧 Déclarer une panne", "🗺️ Outils ferroviaires"],
    ["🤖 Assistant AI", "🗓️ Planning"]
]

async def menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = ReplyKeyboardMarkup(MENU_KEYBOARD, resize_keyboard=True)
    await update.message.reply_text(
        "👋 Bienvenue sur ENCO Bot !\n\n"
        "Voici ce que tu peux faire :\n"
        "📌 Prise de poste : démarre ta journée\n"
        "🖼️ Envoyer une photo : signale un état ou une anomalie\n"
        "🛑 URGENCE / INCIDENT : déclare une urgence immédiate\n"
        "🔧 Déclarer une panne : signale une anomalie machine\n"
        "📄 Bon d'attachement : envoie un bon d'attachement\n"
        "🗺️ Outils ferroviaires : géoportail, règlements, procédures\n"
        "🗓️ Planning, etc.\n\n"
        "Utilise les boutons ci-dessous pour naviguer, ou tape /aide pour plus d'infos.",
        reply_markup=reply_markup
    ) 