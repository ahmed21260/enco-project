from telegram import Update
from telegram.ext import ContextTypes

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler de test simple"""
    await update.message.reply_text("✅ Bot ENCO fonctionne ! Test réussi !")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler de démarrage"""
    await update.message.reply_text(
        "🚀 **Bienvenue sur ENCO Bot !**\n\n"
        "Commandes disponibles :\n"
        "/test - Test du bot\n"
        "/prise - Prise de poste\n"
        "/fin - Fin de poste\n"
        "/checklist - Checklist sécurité\n"
        "/anomalie - Signaler une anomalie\n"
        "/docs - Consulter documents\n"
        "/historique - Voir l'historique"
    ) 