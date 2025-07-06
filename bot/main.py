# redeploy trigger 2025-07-04
print("=== Début du script main.py ===")
import os
import asyncio
import logging
print("=== Imports standards OK ===")
from dotenv import load_dotenv
load_dotenv()
print("=== dotenv chargé ===")
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
print("=== Imports telegram OK ===")
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
from handlers.ai_assistant import get_ai_assistant_handler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot, Update
from utils.firestore import db
from services.enco_ai_assistant import ENCOAIAssistant
import firebase_admin
from firebase_admin import credentials
import json
from datetime import datetime
print("=== Imports handlers et services OK ===")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.info("=== Logging configuré ===")

# Supporte BOT_TOKEN ou TELEGRAM_TOKEN
BOT_TOKEN = os.environ.get("BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN")
if not BOT_TOKEN:
    logging.error("❌ ERREUR : BOT_TOKEN ou TELEGRAM_TOKEN non défini dans les variables d'environnement !")
    print("❌ ERREUR : BOT_TOKEN ou TELEGRAM_TOKEN non défini dans les variables d'environnement !")
    exit(1)
BOT_TOKEN = str(BOT_TOKEN)
PORT = int(os.environ.get("PORT", 8080))
WEBHOOK_PATH = "webhook-enco-SECRET123"
WEBHOOK_URL = f"https://enco-prestarail-bot.up.railway.app/{WEBHOOK_PATH}"
bot = Bot(token=BOT_TOKEN)
print("=== Token et bot Telegram OK ===")

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
        print("✅ Firebase initialisé avec succès")
    else:
        logging.warning("⚠️  Firebase désactivé (ENCO_USE_FIRESTORE != 1)")
        print("⚠️  Firebase désactivé (ENCO_USE_FIRESTORE != 1)")
except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
    logging.error(f"❌ Erreur Firebase credentials: {e}")
    logging.warning("🔄 Mode temporaire activé - Bot fonctionnera sans Firebase")
    print(f"❌ Erreur Firebase credentials: {e}")
    print("🔄 Mode temporaire activé - Bot fonctionnera sans Firebase")

print("=== Config Firebase OK ===")

# Vérification OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("❌ OPENAI_API_KEY non définie ! L'IA ne fonctionnera pas.")
else:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        print("✅ OPENAI_API_KEY détectée et client OpenAI initialisé !")
    except Exception as e:
        print(f"❌ Erreur initialisation OpenAI : {e}")

API_URL = os.getenv("API_URL", "https://believable-motivation-production.up.railway.app/api")

async def send_daily_reminder():
    print("=== send_daily_reminder appelé ===")
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
    print("=== test_rappel appelé ===")
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

async def handle_all_text_to_firestore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.effective_user:
        user_id = str(update.effective_user.id)
        prompt = update.message.text
        db.collection(f'users/{user_id}/messages').add({
            'prompt': prompt,
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id
        })
    # Ne répond pas ici pour laisser la logique métier du menu s'exécuter

def schedule_reminders():
    print("=== schedule_reminders appelé ===")
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_daily_reminder, 'cron', hour=19, minute=0)
    return scheduler

async def on_startup(app):
    print("=== on_startup appelé ===")
    scheduler = schedule_reminders()
    scheduler.start()
    logging.info("🕖 Scheduler des rappels quotidiens démarré !")
    
    # Démarrer l'écouteur Firestore pour le chatbot
    if os.getenv('ENCO_USE_FIRESTORE', '0') == '1' and db:
        try:
            assistant = ENCOAIAssistant()
            if assistant.client:
                watch = assistant.start_firestore_listener()
                if watch:
                    logging.info("✅ Écouteur Firestore chatbot démarré !")
                    print("✅ Écouteur Firestore chatbot démarré !")
                else:
                    logging.warning("⚠️ Impossible de démarrer l'écouteur Firestore")
                    print("⚠️ Impossible de démarrer l'écouteur Firestore")
            else:
                logging.warning("⚠️ Assistant AI non disponible - écouteur Firestore non démarré")
                print("⚠️ Assistant AI non disponible - écouteur Firestore non démarré")
        except Exception as e:
            logging.error(f"❌ Erreur démarrage écouteur Firestore: {e}")
            print(f"❌ Erreur démarrage écouteur Firestore: {e}")
    else:
        logging.info("ℹ️ Écouteur Firestore non démarré (Firebase désactivé)")
        print("ℹ️ Écouteur Firestore non démarré (Firebase désactivé)")
    
    logging.info("🚀 Webhook initialisé : %s", WEBHOOK_URL)
    print(f"🚀 Webhook initialisé : {WEBHOOK_URL}")

async def prompt_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("=== prompt_photo appelé ===")
    if update.message:
        await update.message.reply_text("Merci d'envoyer la photo maintenant.")

async def log_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("=== log_update appelé ===")
    chat_id = update.effective_chat.id if update.effective_chat else "N/A"
    user = update.effective_user.username if update.effective_user else "N/A"
    logging.info("[UPDATE] Chat %s | User %s | Type %s", chat_id, user, update.update_id)
    if update.message and update.message.text:
        logging.info("[UPDATE] Texte : %s", update.message.text)
    if update.message and update.message.photo:
        logging.info("[UPDATE] Photo reçue (%d variantes)", len(update.message.photo))

async def error_handler(update, context):
    print("=== error_handler appelé ===")
    """Gestionnaire d'erreur global"""
    error_msg = str(context.error) if context.error else "Unknown error"
    
    # Ignorer les erreurs de parsing des requêtes non-Telegram
    if any(keyword in error_msg for keyword in [
        "unexpected keyword argument 'type'",
        "missing 1 required positional argument: 'update_id'",
        "got an unexpected keyword argument"
    ]):
        logging.warning("🚫 Requête non-Telegram ignorée (Railway notification)")
        print("🚫 Requête non-Telegram ignorée (Railway notification)")
        return
    
    # Log des autres erreurs
    logging.error(f"❌ Erreur lors du traitement d'un update: {error_msg}")
    print(f"❌ Erreur lors du traitement d'un update: {error_msg}")
    if update:
        logging.error(f"Update ID: {update.update_id if hasattr(update, 'update_id') else 'Unknown'}")
        print(f"Update ID: {update.update_id if hasattr(update, 'update_id') else 'Unknown'}")

# Exemple d'écoute groupée Firestore pour tous les messages IA (pour dashboard)
# (À utiliser côté dashboard JS/TS)
'''
import { getFirestore, collectionGroup, onSnapshot } from "firebase/firestore";

const db = getFirestore();
const messagesQuery = collectionGroup(db, "messages");
onSnapshot(messagesQuery, (snapshot) => {
  snapshot.docChanges().forEach((change) => {
    const data = change.doc.data();
    // Ici, tu peux organiser/afficher tous les messages IA de tous les users
    // Exemple :
    // displayIAMessage(data.user_id, data.prompt, data.response, data.status)
  });
});
'''

def main():
    print("=== main() appelé ===")
    application = ApplicationBuilder().token(str(BOT_TOKEN)).post_init(on_startup).build()
    print("=== Application Telegram construite ===")
    application.add_error_handler(error_handler)
    
    # Ajouter le handler de logging en premier
    application.add_handler(MessageHandler(filters.ALL, log_update), group=1)
    
    # Ajouter un handler universel pour stocker chaque message texte dans Firestore
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_text_to_firestore), group=2)
    
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
    application.add_handler(get_ai_assistant_handler())
    application.add_handler(CallbackQueryHandler(portail_callback))
    
    # Ajouter les handlers de photos et voix
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))

    # Ajouter le handler de texte général en dernier (logique métier du menu)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))

    logging.info(f"✅ Bot ENCO démarré et en écoute sur Telegram en mode webhook sur le port {PORT} !")
    print(f"✅ Bot ENCO démarré et en écoute sur Telegram en mode webhook sur le port {PORT} !")
    logging.info(f"🔗 Webhook URL : {WEBHOOK_URL}")
    print(f"🔗 Webhook URL : {WEBHOOK_URL}")

    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
        url_path=f"/{WEBHOOK_PATH}"
    )
    print("=== Fin de main() ===")

if __name__ == "__main__":
    print("=== __main__ détecté, appel main() ===")
    main()
