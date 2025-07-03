import os
from dotenv import load_dotenv
load_dotenv()
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers.menu import get_menu_handlers
from handlers.prise_de_poste import get_handler as prise_handler
from handlers.fin_de_poste import get_handler as fin_handler
from handlers.checklist import get_checklist_handler
from handlers.anomalie import get_anomalie_handler
from handlers.consult_docs import consulter_documents
from handlers.historique import afficher_historique
from handlers.test import test_command, start_command
from handlers.urgence import get_urgence_handler
from handlers.portail import portail_sncf, portail_callback
from handlers.photo import handle_photo, handle_voice

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot, Update
from telegram.ext import ContextTypes
from utils.firestore import db
import firebase_admin
from firebase_admin import credentials
import json

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    print("❌ ERREUR : TELEGRAM_TOKEN non défini dans le .env !")
    exit(1)
bot = Bot(token=TELEGRAM_TOKEN)

if not os.getenv('ENCO_USE_FIRESTORE', '0') == '1':
    print('❌ ERREUR : ENCO_USE_FIRESTORE=1 doit être défini dans le .env pour activer Firebase !')
    exit(1)

if os.getenv("FIREBASE_SERVICE_ACCOUNT"):
    cred = credentials.Certificate(json.loads(os.environ["FIREBASE_SERVICE_ACCOUNT"]))
else:
    cred = credentials.Certificate("serviceAccountKey.json")  # fallback local

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {
        'storageBucket': os.getenv("FIREBASE_STORAGE_BUCKET", "enco-prestarail.firebasestorage.app")
    })

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
                print(f"Erreur envoi à {chat_id} : {e}")

# Commande manuelle pour tester le rappel
async def test_rappel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_daily_reminder()
    if update.message:
        await update.message.reply_text("Rappel envoyé à tous les opérateurs inscrits !")

def schedule_reminders():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_daily_reminder, 'cron', hour=19, minute=0)
    return scheduler

async def on_startup(app):
    # Démarre le scheduler dans le contexte asyncio du bot
    scheduler = schedule_reminders()
    scheduler.start()
    print("🕖 Scheduler des rappels quotidiens démarré !")

async def prompt_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("Merci d'envoyer la photo maintenant.")

async def log_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"[LOG] Message reçu : {update}")
    try:
        if update.message:
            print(f"[LOG] Texte : {update.message.text}")
    except Exception as e:
        print(f"❌ ERREUR dans log_update : {e}")

def main():
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "your_telegram_bot_token_here":
        print("❌ ERREUR : Token Telegram non configuré !")
        print("1. Crée un bot sur @BotFather")
        print("2. Remplace le token dans bot/.env")
        return
    
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(on_startup).build()
    
    # Log chaque message reçu
    app.add_handler(MessageHandler(filters.ALL, log_update), group=0)

    # Handlers de test simples
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("test", test_command))
    app.add_handler(CommandHandler("test_rappel", test_rappel))
    
    # Handlers principaux
    for handler in get_menu_handlers():
        app.add_handler(handler)
    app.add_handler(prise_handler())
    app.add_handler(fin_handler())
    app.add_handler(get_checklist_handler())
    app.add_handler(get_urgence_handler())
    
    # Handlers de commandes
    app.add_handler(get_anomalie_handler())
    app.add_handler(CommandHandler("docs", consulter_documents))
    app.add_handler(CommandHandler("historique", afficher_historique))
    
    # Handlers pour les boutons du menu
    app.add_handler(MessageHandler(filters.Regex("^Portail d'accès SNCF$"), portail_sncf))
    app.add_handler(CallbackQueryHandler(portail_callback))
    
    # Handler pour les photos envoyées
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.Regex("^Envoyer une photo$"), prompt_photo))

    print("✅ Bot ENCO démarré et en écoute sur Telegram...")
    print("🔗 Test avec /start ou /test sur ton bot")
    print("📱 Tous les boutons du menu sont maintenant fonctionnels !")
    print("VERSION DEBUG 2025-07-03")
    PORT = int(os.environ.get("PORT", 8080))
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="webhook",
        webhook_url="https://sparkling-wonder-production-39a8.up.railway.app/webhook"
    )

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ ERREUR FATALE : {e}") 