from telegram import Update
from telegram.ext import ContextTypes
from utils.firestore import get_historique

# type: ignore
async def afficher_historique(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    histo = get_historique(user.id, limit=10)
    if not histo:
        await update.message.reply_text("⏳ Aucun historique trouvé.")
        return
    msg = "🕒 *Votre historique récent :*\n\n"
    for h in histo:
        t = h.get('type', 'action')
        ts = h.get('timestamp', '')
        desc = h.get('description', '')
        if t == 'anomalie':
            msg += f"- 🚨 Anomalie ({ts}) : {desc}\n"
        elif t == 'checklist':
            msg += f"- ✅ Checklist ({ts})\n"
        else:
            msg += f"- 📍 {t.capitalize()} ({ts})\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

# À intégrer dans le dispatcher du bot dans main.py 