# redeploy trigger 2025-07-04
print("=== Début du script main.py ===")
import os
import asyncio
import logging
print("=== Imports standards OK ===")
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
from handlers.photo import get_photo_handler
from handlers.planning import get_planning_wizard_handler
from handlers.ai_assistant import get_ai_assistant_handler
from handlers.photo import get_photo_handler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot, Update
from utils.firestore import db
from services.enco_ai_assistant import ENCOAIAssistant
import firebase_admin
from firebase_admin import credentials
import json
from datetime import datetime
print("=== Imports handlers et services OK ===")

# Configuration logging robuste
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),  # Console
        logging.FileHandler('bot.log')  # Fichier local
    ]
)
logger = logging.getLogger(__name__)
logger.info("=== Logging configuré ===")
print("=== Logging configuré ===")

# Supporte BOT_TOKEN ou TELEGRAM_TOKEN
BOT_TOKEN = os.environ.get("BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN")
if not BOT_TOKEN:
    logger.error("❌ ERREUR : BOT_TOKEN ou TELEGRAM_TOKEN non défini dans les variables d'environnement !")
    print("❌ ERREUR : BOT_TOKEN ou TELEGRAM_TOKEN non défini dans les variables d'environnement !")
    exit(1)
BOT_TOKEN = str(BOT_TOKEN)
PORT = int(os.environ.get("PORT", 8080))
WEBHOOK_PATH = "webhook-enco-SECRET123"
WEBHOOK_URL = f"https://enco-prestarail-bot.up.railway.app/{WEBHOOK_PATH}"
bot = Bot(token=BOT_TOKEN)
logger.info("=== Token et bot Telegram OK ===")
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
        logger.info("✅ Firebase initialisé avec succès")
        print("✅ Firebase initialisé avec succès")
    else:
        logger.warning("⚠️  Firebase désactivé (ENCO_USE_FIRESTORE != 1)")
        print("⚠️  Firebase désactivé (ENCO_USE_FIRESTORE != 1)")
except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
    logger.error(f"❌ Erreur Firebase credentials: {e}")
    logger.warning("🔄 Mode temporaire activé - Bot fonctionnera sans Firebase")
    print(f"❌ Erreur Firebase credentials: {e}")
    print("🔄 Mode temporaire activé - Bot fonctionnera sans Firebase")

print("=== Config Firebase OK ===")

# Vérification OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.warning("❌ OPENAI_API_KEY non définie ! L'IA ne fonctionnera pas.")
    print("❌ OPENAI_API_KEY non définie ! L'IA ne fonctionnera pas.")
else:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info("✅ OPENAI_API_KEY détectée et client OpenAI initialisé !")
        print("✅ OPENAI_API_KEY détectée et client OpenAI initialisé !")
    except Exception as e:
        logger.error(f"❌ Erreur initialisation OpenAI : {e}")
        print(f"❌ Erreur initialisation OpenAI : {e}")

# URL de l'API - utilise l'API déployée sur Railway
API_URL = os.getenv("API_URL", "https://enco-api-production.up.railway.app")

async def send_daily_reminder():
    logger.info("=== send_daily_reminder appelé ===")
    print("=== send_daily_reminder appelé ===")
    if not db:
        logger.warning("Firebase non disponible pour les rappels")
        return
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
                logger.info(f"Rappel envoyé à {chat_id}")
            except Exception as e:
                logger.error(f"Erreur envoi à {chat_id} : {e}")

ADMIN_ID = 7648184043

async def test_rappel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("=== test_rappel appelé ===")
    print("=== test_rappel appelé ===")
    if not update.effective_user or update.effective_user.id != ADMIN_ID:
        if update.message:
            await update.message.reply_text("Accès réservé à l'administrateur.")
        return
    await send_daily_reminder()
    if update.message:
        await update.message.reply_text("Rappel envoyé à tous les opérateurs inscrits !")

async def test_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Handler /test exécuté !")
    print("Handler /test exécuté !")
    if update.message:
        await update.message.reply_text("✅ Test réussi ! Le bot fonctionne !")
    else:
        logger.error(f"update.message est None ! update = {update}")
        print(f"update.message est None ! update = {update}")

async def ping(update, context):
    logger.info("Handler /ping exécuté !")
    print("Handler /ping exécuté !")
    if update.message:
        await update.message.reply_text("pong")
    else:
        logger.error(f"update.message est None ! update = {update}")
        print(f"update.message est None ! update = {update}")

async def handle_docs_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler pour la commande docs (admin seulement)"""
    if not update.effective_user or update.effective_user.id != ADMIN_ID:
        if update.message:
            await update.message.reply_text("Accès réservé à l'administrateur.")
        return
    await consulter_documents(update, context)

async def handle_historique_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler pour la commande historique (admin seulement)"""
    if not update.effective_user or update.effective_user.id != ADMIN_ID:
        if update.message:
            await update.message.reply_text("Accès réservé à l'administrateur.")
        return
    await afficher_historique(update, context)

async def handle_all_text_to_firestore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler universel pour tous les messages texte - log dans Firestore + IA"""
    if not update.message or not update.effective_user:
        return
    
    user_id = str(update.effective_user.id)
    prompt = update.message.text
    
    if not prompt:
        return
    
    # Log détaillé
    logger.info(f"[MESSAGE] User {user_id} ({update.effective_user.full_name}): {prompt}")
    print(f"[MESSAGE] User {user_id} ({update.effective_user.full_name}): {prompt}")
    
    # Enregistrer dans Firestore si disponible
    if db:
        try:
            message_ref = db.collection(f'users/{user_id}/messages').add({
                'prompt': prompt,
                'timestamp': datetime.now().isoformat(),
                'user_id': user_id,
                'user_name': update.effective_user.full_name,
                'status': {
                    'state': 'pending',
                    'created_at': datetime.now().isoformat()
                }
            })
            logger.info(f"[FIRESTORE] Message enregistré pour user {user_id}")
            
            # Envoyer message "en attente IA"
            await update.message.reply_text("🤖 **Message reçu, IA en cours d'analyse...**")
            
            # Appel IA asynchrone
            try:
                assistant = ENCOAIAssistant()
                if assistant.client:
                    response = await assistant.generate_railway_response(prompt)
                    if response:
                        # Mettre à jour Firestore avec la réponse
                        message_ref[1].update({
                            'response': response,
                            'status': {
                                'state': 'completed',
                                'updated_at': datetime.now().isoformat()
                            }
                        })
                        # Envoyer la réponse IA
                        await update.message.reply_text(f"💡 **Réponse IA :**\n{response}")
                        logger.info(f"[IA] Réponse envoyée à user {user_id}")
                    else:
                        await update.message.reply_text("❌ Désolé, je n'ai pas pu générer de réponse.")
                else:
                    await update.message.reply_text("⚠️ Assistant IA temporairement indisponible.")
            except Exception as e:
                logger.error(f"[IA] Erreur génération réponse: {e}")
                await update.message.reply_text("❌ Erreur lors de la génération de la réponse IA.")
                
        except Exception as e:
            logger.error(f"[FIRESTORE] Erreur enregistrement message: {e}")
    else:
        logger.warning("Firebase non disponible - message non enregistré")

async def test_ai(update, context):
    """Test OpenAI depuis Telegram"""
    from services.enco_ai_assistant import ENCOAIAssistant
    prompt = "Donne-moi un résumé de l'activité ferroviaire de la journée, comme une secrétaire intelligente."
    try:
        assistant = ENCOAIAssistant()
        if assistant.client:
            response = await assistant.generate_railway_response(prompt)
            await update.message.reply_text(f"Réponse IA :\n{response}")
        else:
            await update.message.reply_text("❌ OpenAI non configuré ou indisponible.")
    except Exception as e:
        await update.message.reply_text(f"Erreur IA : {e}")

def schedule_reminders():
    logger.info("=== schedule_reminders appelé ===")
    print("=== schedule_reminders appelé ===")
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_daily_reminder, 'cron', hour=19, minute=0)
    return scheduler

async def on_startup(app):
    logger.info("=== on_startup appelé ===")
    print("=== on_startup appelé ===")
    scheduler = schedule_reminders()
    scheduler.start()
    logger.info("🕖 Scheduler des rappels quotidiens démarré !")
    
    # Démarrer l'écouteur Firestore pour le chatbot
    if os.getenv('ENCO_USE_FIRESTORE', '0') == '1' and db:
        try:
            assistant = ENCOAIAssistant()
            if assistant.client:
                watch = assistant.start_firestore_listener()
                if watch:
                    logger.info("✅ Écouteur Firestore chatbot démarré !")
                    print("✅ Écouteur Firestore chatbot démarré !")
                else:
                    logger.warning("⚠️ Impossible de démarrer l'écouteur Firestore")
                    print("⚠️ Impossible de démarrer l'écouteur Firestore")
            else:
                logger.warning("⚠️ Assistant AI non disponible - écouteur Firestore non démarré")
                print("⚠️ Assistant AI non disponible - écouteur Firestore non démarré")
        except Exception as e:
            logger.error(f"❌ Erreur démarrage écouteur Firestore: {e}")
            print(f"❌ Erreur démarrage écouteur Firestore: {e}")
    else:
        logger.info("ℹ️ Écouteur Firestore non démarré (Firebase désactivé)")
        print("ℹ️ Écouteur Firestore non démarré (Firebase désactivé)")
    
    logger.info("🚀 Webhook initialisé : %s", WEBHOOK_URL)
    print(f"🚀 Webhook initialisé : {WEBHOOK_URL}")

async def prompt_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("=== prompt_photo appelé ===")
    print("=== prompt_photo appelé ===")
    if update.message:
        await update.message.reply_text("Merci d'envoyer la photo maintenant.")

async def log_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler universel de logging pour tous les updates"""
    logger.info("=== log_update appelé ===")
    print("=== log_update appelé ===")
    
    if not update:
        logger.warning("Update None reçu")
        return
    
    chat_id = update.effective_chat.id if update.effective_chat else "N/A"
    user = update.effective_user.username if update.effective_user else "N/A"
    user_id = update.effective_user.id if update.effective_user else "N/A"
    
    logger.info(f"[UPDATE] ID: {update.update_id} | Chat: {chat_id} | User: {user} ({user_id})")
    print(f"[UPDATE] ID: {update.update_id} | Chat: {chat_id} | User: {user} ({user_id})")
    
    if update.message:
        if update.message.text:
            logger.info(f"[UPDATE] Texte: {update.message.text}")
            print(f"[UPDATE] Texte: {update.message.text}")
        if update.message.photo:
            logger.info(f"[UPDATE] Photo reçue ({len(update.message.photo)} variantes)")
            print(f"[UPDATE] Photo reçue ({len(update.message.photo)} variantes)")
        if update.message.location:
            logger.info(f"[UPDATE] Localisation: {update.message.location.latitude}, {update.message.location.longitude}")
            print(f"[UPDATE] Localisation: {update.message.location.latitude}, {update.message.location.longitude}")
        if update.message.voice:
            logger.info(f"[UPDATE] Message vocal reçu")
            print(f"[UPDATE] Message vocal reçu")

async def error_handler(update, context):
    logger.error("=== error_handler appelé ===")
    print("=== error_handler appelé ===")
    """Gestionnaire d'erreur global"""
    error_msg = str(context.error) if context.error else "Unknown error"
    
    # Ignorer les erreurs de parsing des requêtes non-Telegram
    if any(keyword in error_msg for keyword in [
        "unexpected keyword argument 'type'",
        "missing 1 required positional argument: 'update_id'",
        "got an unexpected keyword argument"
    ]):
        logger.warning("🚫 Requête non-Telegram ignorée (Railway notification)")
        print("🚫 Requête non-Telegram ignorée (Railway notification)")
        return
    
    # Log des autres erreurs
    logger.error(f"❌ Erreur lors du traitement d'un update: {error_msg}")
    print(f"❌ Erreur lors du traitement d'un update: {error_msg}")
    if update:
        logger.error(f"Update ID: {update.update_id if hasattr(update, 'update_id') else 'Unknown'}")
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
    logger.info("=== main() appelé ===")
    print("=== main() appelé ===")
    application = ApplicationBuilder().token(str(BOT_TOKEN)).post_init(on_startup).build()
    logger.info("=== Application Telegram construite ===")
    print("=== Application Telegram construite ===")
    application.add_error_handler(error_handler)
    
    # Ajouter le handler de logging en premier (priorité haute)
    application.add_handler(MessageHandler(filters.ALL, log_update), group=1)
    
    # Ajouter un handler universel pour les messages texte (IA + Firestore)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_text_to_firestore), group=2)
    
    # Ajouter un handler de test
    application.add_handler(CommandHandler("test", test_handler))
    application.add_handler(CommandHandler("ping", ping))
    application.add_handler(CommandHandler("test_ai", test_ai))
    
    # Ajouter les handlers de commandes
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("test_rappel", test_rappel))
    application.add_handler(CommandHandler("docs", handle_docs_admin))
    application.add_handler(CommandHandler("historique", handle_historique_admin))
    
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
    application.add_handler(get_photo_handler())
    application.add_handler(CallbackQueryHandler(portail_callback))
    
    # Ajouter les handlers de photos et voix
    # Les photos sont maintenant gérées par le handler photo dédié
    async def handle_voice_disabled(update, context):
        if update.message:
            await update.message.reply_text("🗣️ Messages vocaux temporairement désactivés.")
    application.add_handler(MessageHandler(filters.VOICE, handle_voice_disabled))

    # Ajouter le handler de texte général en dernier (logique métier du menu)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))

    logger.info(f"✅ Bot ENCO démarré et en écoute sur Telegram en mode webhook sur le port {PORT} !")
    print(f"✅ Bot ENCO démarré et en écoute sur Telegram en mode webhook sur le port {PORT} !")
    logger.info(f"🔗 Webhook URL : {WEBHOOK_URL}")
    print(f"🔗 Webhook URL : {WEBHOOK_URL}")
    logger.info(f"🔗 API URL : {API_URL}")
    print(f"🔗 API URL : {API_URL}")

    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
        url_path=f"/{WEBHOOK_PATH}"
    )
    logger.info("=== Fin de main() ===")
    print("=== Fin de main() ===")

if __name__ == "__main__":
    logger.info("=== __main__ détecté, appel main() ===")
    print("=== __main__ détecté, appel main() ===")
    main()
