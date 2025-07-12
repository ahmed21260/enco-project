from telegram import Update
from telegram.ext import ContextTypes
from utils.firestore import get_documents

# type: ignore
async def consulter_documents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    docs = get_documents()
    if not docs:
        await update.message.reply_text("📄 Aucun document disponible.")
        return
    msg = "📄 *Fiches techniques disponibles :*\n\n"
    for doc in docs:
        msg += f"- {doc.get('machine', 'Machine inconnue')} : [{doc.get('titre', 'Document')}]({doc.get('url', '#')})\n"
    await update.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=True)

# À intégrer dans le dispatcher du bot dans main.py 