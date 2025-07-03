import os
import logging
from dotenv import load_dotenv
load_dotenv()
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from handlers.menu import get_menu_handlers
from handlers.prise_de_poste import get_handler as prise_handler
from handlers.fin_de_poste import get_handler as fin_handler
from handlers.checklist import get_checklist_handler
from handlers.anomalie import get_anomalie_handler
from handlers.consult_docs import consulter_documents
from handlers.historique import afficher_historique
from handlers.urgence import get_urgence_handler
from handlers.portail import portail_sncf, portail_callback
from handlers.photo import handle_photo, handle_voice
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
BOT_TOKEN = str(BOT_TOKEN)  # assure que BOT_TOKEN est bien un str
PORT = int(os.environ.get("PORT", 8080))
WEBHOOK_PATH = "webhook"
WEBHOOK_URL = "https://enco-prestarail-bot.railway.app/webhook"
bot = Bot(token=BOT_TOKEN)

if not os.getenv('ENCO_USE_FIRESTORE', '0') == '1':
    logging.error('❌ ERREUR : ***REMOVED*** doit être défini dans le .env pour activer Firebase !')
    exit(1)

if os.getenv("FIREBASE_SERVICE_ACCOUNT"):
    cred = credentials.Certificate(json.loads(os.environ["FIREBASE_SERVICE_ACCOUNT"]))
else:
    cred = credentials.Certificate("serviceAccountKey.json")  # fallback local

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {
        'storageBucket': os.getenv("FIREBASE_STORAGE_BUCKET", "enco-prestarail.firebasestorage.app")
    })

API_URL = os.getenv("API_URL", "https://enco-prestarail-api.up.railway.app/api")

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

async def test_rappel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_daily_reminder()
    if update.message:
        await update.message.reply_text("Rappel envoyé à tous les opérateurs inscrits !")

def schedule_reminders():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_daily_reminder, 'cron', hour=19, minute=0)
    return scheduler

async def on_startup(app):
    scheduler = schedule_reminders()
    scheduler.start()
    logging.info("🕖 Scheduler des rappels quotidiens démarré !")

async def prompt_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("Merci d'envoyer la photo maintenant.")

async def log_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"[LOG] Message reçu : {update}")
    try:
        if update.message:
            logging.info(f"[LOG] Texte : {update.message.text}")
    except Exception as e:
        logging.error(f"❌ ERREUR dans log_update : {e}")

async def error_handler(update, context):
    logging.error(msg="Exception while handling an update:", exc_info=context.error)

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).post_init(on_startup).build()
    application.add_error_handler(error_handler)
    application.add_handler(MessageHandler(filters.ALL, log_update), group=0)
    application.add_handler(CommandHandler("test_rappel", test_rappel))
    for handler in get_menu_handlers():
        application.add_handler(handler)
    application.add_handler(prise_handler())
    application.add_handler(fin_handler())
    application.add_handler(get_checklist_handler())
    application.add_handler(get_urgence_handler())
    application.add_handler(get_anomalie_handler())
    application.add_handler(CommandHandler("docs", consulter_documents))
    application.add_handler(CommandHandler("historique", afficher_historique))
    application.add_handler(MessageHandler(filters.Regex("^Portail d'accès SNCF$"), portail_sncf))
    application.add_handler(CallbackQueryHandler(portail_callback))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.Regex("^Envoyer une photo$"), prompt_photo))
    logging.info(f"✅ Bot ENCO démarré et en écoute sur Telegram sur le port {PORT} !")
    logging.info(f"🔗 Webhook URL : {WEBHOOK_URL}")
    logging.info("VERSION DEBUG 2025-07-03")
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=WEBHOOK_PATH,
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"❌ ERREUR FATALE : {e}") 