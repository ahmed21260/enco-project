from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def portail_sncf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler pour les portails d'accès SNCF"""
    keyboard = [
        [InlineKeyboardButton("📍 Portail le plus proche", callback_data="portail_proche")],
        [InlineKeyboardButton("🗺️ Voir tous les portails", callback_data="portails_liste")],
        [InlineKeyboardButton("📞 Contacter SNCF", callback_data="sncf_contact")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🚂 **Portails d'Accès SNCF**\n\n"
        "Sélectionnez une option pour accéder aux portails SNCF :\n\n"
        "• **Portail le plus proche** : Trouver le portail SNCF le plus proche de votre position\n"
        "• **Voir tous les portails** : Liste complète des portails d'accès\n"
        "• **Contacter SNCF** : Numéros d'urgence et contacts",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def portail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback pour les boutons portail"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "portail_proche":
        await query.edit_message_text(
            "📍 **Portail SNCF le plus proche**\n\n"
            "Pour localiser le portail le plus proche, envoyez votre position.\n\n"
            "**Portails principaux :**\n"
            "• Gare de Lyon (Paris)\n"
            "• Gare du Nord (Paris)\n"
            "• Gare de l'Est (Paris)\n"
            "• Gare Montparnasse (Paris)\n\n"
            "📞 **Urgence SNCF :** 3635",
            parse_mode="Markdown"
        )
    elif query.data == "portails_liste":
        await query.edit_message_text(
            "🗺️ **Tous les Portails SNCF**\n\n"
            "**Portails d'accès principaux :**\n\n"
            "🏛️ **Paris :**\n"
            "• Gare de Lyon\n"
            "• Gare du Nord\n"
            "• Gare de l'Est\n"
            "• Gare Montparnasse\n"
            "• Gare Saint-Lazare\n\n"
            "🏙️ **Régions :**\n"
            "• Lyon Part-Dieu\n"
            "• Marseille Saint-Charles\n"
            "• Lille Flandres\n"
            "• Strasbourg\n"
            "• Nantes\n\n"
            "📞 **Contact général :** 3635",
            parse_mode="Markdown"
        )
    elif query.data == "sncf_contact":
        await query.edit_message_text(
            "📞 **Contacts SNCF**\n\n"
            "**Numéros d'urgence :**\n"
            "• 🚨 Urgence : 3635\n"
            "• 🚂 Voyageurs : 3635\n"
            "• 🚧 Infrastructure : 3635\n\n"
            "**Contacts spécialisés :**\n"
            "• 🏗️ Travaux : 3635\n"
            "• 🚨 Sécurité : 3635\n"
            "• 📋 Administration : 3635\n\n"
            "**Site web :** www.sncf.com",
            parse_mode="Markdown"
        ) 