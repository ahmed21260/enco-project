# redeploy trigger 2025-07-04
import os
import asyncio
import logging
from dotenv import load_dotenv
load_dotenv()
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from handlers.menu import menu_principal, handle_menu, start
from handlers.prise_de_poste import get_prise_wizard_handler as prise_handler
from handlers.fin_de_poste import get_fin_wizard_handler as fin_handler
from handlers.checklist import get_checklist_handler
from handlers.anomalie import get_anomalie_wizard_handler as get_anomalie_handler
from handlers.bons_attachement import get_bon_wizard_handler
from handlers.rapport_technique import get_rapport_wizard_handler
from handlers.outils_ferroviaires import get_outils_ferroviaires_handler
from handlers.consult_docs import consulter_documents
from handlers.historique import afficher_historique
from handlers.urgence import get_urgence_wizard_handler as get_urgence_handler
from handlers.portail import portail_callback
from handlers.photo import handle_photo, handle_voice
from handlers.planning import get_planning_wizard_handler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot, Update
from utils.firestore import db
import firebase_admin
from firebase_admin import credentials
import json

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Supporte BOT_TOKEN ou TELEGRAM_TOKEN
BOT_TOKEN = os.environ.get("BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN")
if not BOT_TOKEN:
    logging.error("❌ ERREUR : BOT_TOKEN ou TELEGRAM_TOKEN non défini dans les variables d'environnement !")
    exit(1)
BOT_TOKEN = str(BOT_TOKEN)
PORT = int(os.environ.get("PORT", 8080))
WEBHOOK_PATH = "webhook-enco-SECRET123"
WEBHOOK_URL = f"https://enco-prestarail-bot.up.railway.app/{WEBHOOK_PATH}"
bot = Bot(token=BOT_TOKEN)

# Initialisation Firebase avec gestion d'erreurs
try:
    if os.getenv('ENCO_USE_FIRESTORE', '0') == '1':
        if os.getenv("FIREBASE_SERVICE_ACCOUNT"):
            cred = credentials.Certificate(json.loads(os.environ["FIREBASE_SERVICE_ACCOUNT"]))
        else:
            cred_file = "firebase_credentials.json" if os.path.exists("firebase_credentials.json") else "serviceAccountKey.json"
            cred = credentials.Certificate(cred_file)

        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred, {
                'storageBucket': os.getenv("FIREBASE_STORAGE_BUCKET", "enco-prestarail.appspot.com")
            })
        logging.info("✅ Firebase initialisé avec succès")
    else:
        logging.warning("⚠️  Firebase désactivé (ENCO_USE_FIRESTORE != 1)")
except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
    logging.error(f"❌ Erreur Firebase credentials: {e}")
    logging.warning("🔄 Mode temporaire activé - Bot fonctionnera sans Firebase")
    os.environ['ENCO_USE_FIRESTORE'] = '0'

API_URL = os.getenv("API_URL", "https://believable-motivation-production.up.railway.app/api")

async def send_daily_reminder():
    operateurs = db.collection('operateurs').stream()
    for op in operateurs:
        data = op.to_dict()
        chat_id = data.get('telegram_id')
        if chat_id:
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text="⚡️ RAPPEL : Merci d'envoyer votre bon d'attachement du jour avant la fin de service !"
                )
            except Exception as e:
                logging.error(f"Erreur envoi à {chat_id} : {e}")

ADMIN_ID = 7648184043

async def test_rappel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Accès réservé à l'administrateur.")
        return
    await send_daily_reminder()
    if update.message:
        await update.message.reply_text("Rappel envoyé à tous les opérateurs inscrits !")

async def test_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Handler /test exécuté !")
    if update.message:
        await update.message.reply_text("✅ Test réussi ! Le bot fonctionne !")
    else:
        print(f"update.message est None ! update = {update}")

async def ping(update, context):
    print("Handler /ping exécuté !")
    if update.message:
        await update.message.reply_text("pong")
    else:
        print(f"update.message est None ! update = {update}")

def schedule_reminders():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_daily_reminder, 'cron', hour=19, minute=0)
    return scheduler

async def on_startup(app):
    scheduler = schedule_reminders()
    scheduler.start()
    logging.info("🕖 Scheduler des rappels quotidiens démarré !")
    logging.info("🚀 Webhook initialisé : %s", WEBHOOK_URL)

async def prompt_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("Merci d'envoyer la photo maintenant.")

async def log_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id if update.effective_chat else "N/A"
    user = update.effective_user.username if update.effective_user else "N/A"
    logging.info("[UPDATE] Chat %s | User %s | Type %s", chat_id, user, update.update_id)
    if update.message and update.message.text:
        logging.info("[UPDATE] Texte : %s", update.message.text)
    if update.message and update.message.photo:
        logging.info("[UPDATE] Photo reçue (%d variantes)", len(update.message.photo))

async def error_handler(update, context):
    """Gestionnaire d'erreur global"""
    error_msg = str(context.error) if context.error else "Unknown error"
    
    # Ignorer les erreurs de parsing des requêtes non-Telegram
    if any(keyword in error_msg for keyword in [
        "unexpected keyword argument 'type'",
        "missing 1 required positional argument: 'update_id'",
        "got an unexpected keyword argument"
    ]):
        logging.warning("🚫 Requête non-Telegram ignorée (Railway notification)")
        return
    
    # Log des autres erreurs
    logging.error(f"❌ Erreur lors du traitement d'un update: {error_msg}")
    if update:
        logging.error(f"Update ID: {update.update_id if hasattr(update, 'update_id') else 'Unknown'}")

def main():
    application = ApplicationBuilder().token(str(BOT_TOKEN)).post_init(on_startup).build()
    application.add_error_handler(error_handler)
    
    # Ajouter le handler de logging en premier
    application.add_handler(MessageHandler(filters.ALL, log_update), group=1)
    
    # Ajouter un handler de test
    application.add_handler(CommandHandler("test", test_handler))
    application.add_handler(CommandHandler("ping", ping))
    
    # Ajouter les handlers de commandes
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("test_rappel", test_rappel))
    application.add_handler(CommandHandler("docs", lambda u, c: consulter_documents(u, c) if u.effective_user.id == ADMIN_ID else u.message.reply_text("Accès réservé à l'administrateur.")))
    application.add_handler(CommandHandler("historique", lambda u, c: afficher_historique(u, c) if u.effective_user.id == ADMIN_ID else u.message.reply_text("Accès réservé à l'administrateur.")))
    
    # Ajouter les handlers spécifiques
    application.add_handler(prise_handler())
    application.add_handler(fin_handler())
    application.add_handler(get_checklist_handler())
    application.add_handler(get_anomalie_handler())
    application.add_handler(get_urgence_handler())
    application.add_handler(get_bon_wizard_handler())
    application.add_handler(get_rapport_wizard_handler())
    application.add_handler(get_outils_ferroviaires_handler())
    application.add_handler(get_planning_wizard_handler())
    application.add_handler(CallbackQueryHandler(portail_callback))
    
    # Ajouter les handlers de photos et voix
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))

    # Ajouter le handler de texte général en dernier
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))

    logging.info(f"✅ Bot ENCO démarré et en écoute sur Telegram en mode webhook sur le port {PORT} !")
    logging.info(f"🔗 Webhook URL : {WEBHOOK_URL}")

    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
        url_path=f"/{WEBHOOK_PATH}"
    )

if __name__ == "__main__":
        main()
