# redeploy trigger 2025-07-04
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
from flask import Flask, request, Response
import threading

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG if os.getenv("ENCO_DEBUG", "0") == "1" else logging.INFO
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

# Initialisation Firebase avec gestion d'erreurs
try:
    if os.getenv('ENCO_USE_FIRESTORE', '0') == '1':
        if os.getenv("FIREBASE_SERVICE_ACCOUNT"):
            cred = credentials.Certificate(json.loads(os.environ["FIREBASE_SERVICE_ACCOUNT"]))
        else:
            cred = credentials.Certificate("serviceAccountKey.json")  # fallback local

        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred, {
                'storageBucket': os.getenv("FIREBASE_STORAGE_BUCKET", "enco-prestarail.firebasestorage.app")
            })
        logging.info("✅ Firebase initialisé avec succès")
    else:
        logging.warning("⚠️  Firebase désactivé (ENCO_USE_FIRESTORE != 1)")
except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
    logging.error(f"❌ Erreur Firebase credentials: {e}")
    logging.warning("🔄 Mode temporaire activé - Bot fonctionnera sans Firebase")
    # Désactiver Firebase pour ce run
    os.environ['ENCO_USE_FIRESTORE'] = '0'

API_URL = os.getenv("API_URL", "https://enco-prestarail-api.up.railway.app/api")

# Flask app pour gérer le webhook manuellement
app = Flask(__name__)

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
    logging.error(msg="Exception while handling an update:", exc_info=context.error)

# Point 1 & 2 : Handler webhook personnalisé avec logs et protection
@app.route(f'/{WEBHOOK_PATH}', methods=['POST'])
def webhook_handler():
    try:
        # Récupérer le payload JSON
        data = request.get_json(force=True)
        
        # Point 1 : Log du payload reçu
        logging.info(f"🔍 PAYLOAD reçu sur /webhook: {json.dumps(data, indent=2)}")
        
        # Point 2 : Vérification que c'est un vrai update Telegram
        if not isinstance(data, dict):
            logging.warning("❌ Payload reçu n'est pas un dictionnaire JSON")
            return "Invalid JSON format", 400
            
        if "update_id" not in data:
            logging.warning("❌ Payload sans update_id reçu, ignoré (pas un update Telegram)")
            return "Not a Telegram update", 400
            
        # Point 3 : Vérification du format attendu
        required_fields = ["update_id"]
        for field in required_fields:
            if field not in data:
                logging.warning(f"❌ Champ requis '{field}' manquant dans le payload")
                return f"Missing required field: {field}", 400
        
        # Point 4 : Traitement sécurisé de l'update
        try:
            update = Update.de_json(data, bot)
            logging.info(f"✅ Update Telegram valide reçu (ID: {update.update_id})")
            
            # Traiter l'update avec l'application de manière asynchrone
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(application.process_update(update))
            finally:
                loop.close()
            
            return "OK", 200
            
        except Exception as e:
            logging.error(f"❌ Erreur lors du traitement de l'update: {e}")
            return "Error processing update", 500
            
    except Exception as e:
        logging.error(f"❌ Erreur générale dans webhook_handler: {e}")
        return "Internal server error", 500

def main():
    global application
    # BOT_TOKEN est déjà vérifié plus haut, donc on peut forcer le type
    application = ApplicationBuilder().token(str(BOT_TOKEN)).post_init(on_startup).build()
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
    logging.info("VERSION DEBUG 2025-07-04 - WEBHOOK SECURISE")
    
    # Démarrer Flask avec le handler personnalisé
    app.run(host="0.0.0.0", port=PORT, debug=False)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"❌ ERREUR FATALE : {e}") 