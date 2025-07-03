"""Main entry point for the ENCO Telegram bot.

The bot uses python-telegram-bot in webhook mode. Core responsibilities:
    • register command / message handlers
    • schedule daily reminders via APScheduler
    • expose a webhook endpoint handled by PTB Application

Environment variables required:
    BOT_TOKEN / TELEGRAM_TOKEN   – Telegram bot token
    PORT                         – Port to bind the webhook listener (Railway sets it)
    WEBHOOK_URL                  – Public https URL that Telegram will call
    ENCO_USE_FIRESTORE           – "1" to enable Firebase / Firestore persistence

Any missing mandatory variable aborts startup with a clear log message.
"""

from __future__ import annotations

import os
import logging

# Third-party imports wrapped in try/except for informative error messages.
try:
    from dotenv import load_dotenv  # type: ignore
except ModuleNotFoundError as exc:  # pragma: no cover
    raise ModuleNotFoundError(
        "python-dotenv n'est pas installé. Exécutez 'pip install python-dotenv'."
    ) from exc

load_dotenv()

try:
    from telegram.ext import (
        ApplicationBuilder,
        CommandHandler,
        CallbackQueryHandler,
        MessageHandler,
        filters,
        ContextTypes,
    )  # type: ignore[import-untyped]
except ModuleNotFoundError as exc:  # pragma: no cover
    raise ModuleNotFoundError(
        "python-telegram-bot n'est pas installé. Exécutez 'pip install python-telegram-bot[webhooks]'."
    ) from exc

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

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore[import]
except ModuleNotFoundError as exc:  # pragma: no cover
    raise ModuleNotFoundError(
        "APScheduler n'est pas installé. Exécutez 'pip install APScheduler'."
    ) from exc

from telegram import Bot, Update  # type: ignore[import-untyped]

try:
    import firebase_admin  # type: ignore[import]
    from firebase_admin import credentials  # type: ignore[import]
except ModuleNotFoundError as exc:  # pragma: no cover
    raise ModuleNotFoundError(
        "firebase-admin n'est pas installé. Exécutez 'pip install firebase-admin'."
    ) from exc

from utils.firestore import db
import json
from typing import Final

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

if not os.getenv('ENCO_USE_FIRESTORE', '0') == '1':
    logging.error('❌ ERREUR : ENCO_USE_FIRESTORE=1 doit être défini dans le .env pour activer Firebase !')
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

async def send_daily_reminder() -> None:
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

async def test_rappel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_daily_reminder()
    if update.message:
        await update.message.reply_text("Rappel envoyé à tous les opérateurs inscrits !")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Commande de test simple pour vérifier que le webhook fonctionne."""
    logging.info("[PING] Reçu /ping depuis %s", update.effective_user.id if update.effective_user else "unknown")
    if update.message:
        await update.message.reply_text("pong 🏓")

def schedule_reminders() -> AsyncIOScheduler:
    """Configure and return the APScheduler instance responsible for daily reminders."""
    scheduler: AsyncIOScheduler = AsyncIOScheduler()
    scheduler.add_job(send_daily_reminder, "cron", hour=19, minute=0)
    return scheduler

async def on_startup(app) -> None:
    scheduler: AsyncIOScheduler = schedule_reminders()
    scheduler.start()
    logging.info("🕖 Scheduler des rappels quotidiens démarré !")
    logging.info("🚀 Webhook initialisé : %s", WEBHOOK_URL)

async def prompt_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text("Merci d'envoyer la photo maintenant.")

async def log_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id if update.effective_chat else "N/A"
    user = update.effective_user.username if update.effective_user else "N/A"
    logging.info("[UPDATE] Chat %s | User %s | Type %s", chat_id, user, update.update_id)
    if update.message and update.message.text:
        logging.info("[UPDATE] Texte : %s", update.message.text)
    if update.message and update.message.photo:
        logging.info("[UPDATE] Photo reçue (%d variantes)", len(update.message.photo))

async def error_handler(update, context) -> None:
    logging.error(msg="Exception while handling an update:", exc_info=context.error)

def main() -> None:
    """Instantiate the PTB `Application` and start the webhook long-running loop."""
    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(on_startup)
        .build()
    )
    application.add_error_handler(error_handler)
    application.add_handler(MessageHandler(filters.ALL, log_update), group=0)
    application.add_handler(CommandHandler("test_rappel", test_rappel))
    application.add_handler(CommandHandler("ping", ping))
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
    logging.info("VERSION DEBUG 2025-07-04")
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