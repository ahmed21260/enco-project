from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters, ContextTypes
from utils.firestore import save_urgence, db
from datetime import datetime
from services.enco_ai_assistant import ENCOAIAssistant
import logging

TYPE, MESSAGE, GPS, CONFIRM = range(4)

# Types d'urgence spécifiques ferroviaires
URGENCE_TYPES = [
    ["🚨 Collision / Obstacle voie", "⚡ Panne électrique"],
    ["🔧 Panne machine critique", "🏥 Blessure opérateur"],
    ["🚧 Incident chantier", "🌊 Inondation / Intempéries"],
    ["📡 Panne signalisation", "🔥 Incendie / Fumée"],
    ["Autre urgence"]
]

async def start_urgence_wizard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    await update.message.reply_text(
        "🚨 **URGENCE FERROVIAIRE**\n\n"
        "Sélectionne le type d'urgence :",
        reply_markup=ReplyKeyboardMarkup(URGENCE_TYPES, one_time_keyboard=True, resize_keyboard=True)
    )
    logging.info(f"[URGENCE] Début déclaration pour user {update.effective_user.id}")
    return TYPE

async def receive_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    if update.message.text in ["🤖 Aide IA", "💬 Aide IA"]:
        assistant = ENCOAIAssistant()
        suggestion = await assistant.generate_railway_response("Aide demandée pour l'étape type d'urgence.")
        await update.message.reply_text(f"🤖 Suggestion IA : {suggestion}")
        return TYPE
    context.user_data['urgence_type'] = update.message.text
    
    # Afficher les numéros d'urgence selon le type
    numeros_urgence = get_numeros_urgence(update.message.text)
    
    await update.message.reply_text(
        f"🚨 **{update.message.text}**\n\n"
        f"Décris l'urgence ou ajoute une photo (optionnel, tape 'skip' pour passer) :\n\n"
        f"📞 **Numéros d'urgence :**\n"
        f"{numeros_urgence}",
        reply_markup=ReplyKeyboardMarkup([
            ["Envoyer un message d'urgence"],
            ["🤖 Aide IA"]
        ], resize_keyboard=True)
    )
    logging.info(f"[URGENCE] Type sélectionné: {update.message.text} pour user {update.effective_user.id}")
    return MESSAGE

def get_numeros_urgence(type_urgence):
    """Retourne les numéros d'urgence selon le type"""
    base_numeros = "🚨 Sécurité SNCF : 3117\n📞 ENCO Assistance : 06 XX XX XX XX"
    
    if type_urgence and ("Collision" in type_urgence or "Obstacle" in type_urgence):
        return f"{base_numeros}\n🚨 SAMU : 15\n🚔 Police : 17"
    elif type_urgence and "Blessure" in type_urgence:
        return f"{base_numeros}\n🚨 SAMU : 15\n🏥 Médecin chantier : [numéro local]"
    elif type_urgence and ("Incendie" in type_urgence or "Fumée" in type_urgence):
        return f"{base_numeros}\n🚨 Pompiers : 18\n🚨 SAMU : 15"
    elif type_urgence and "Panne machine" in type_urgence:
        return f"{base_numeros}\n🔧 Maintenance ENCO : [numéro local]"
    else:
        return f"{base_numeros}\n🚨 SAMU : 15\n🚔 Police : 17\n🚨 Pompiers : 18"

async def receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    if update.message.text in ["🤖 Aide IA", "💬 Aide IA"]:
        assistant = ENCOAIAssistant()
        suggestion = await assistant.generate_railway_response("Aide demandée pour l'étape message d'urgence.")
        await update.message.reply_text(f"🤖 Suggestion IA : {suggestion}")
        return MESSAGE
    if update.message.text and update.message.text.lower() == 'skip':
        context.user_data['urgence_message'] = ''
    else:
        context.user_data['urgence_message'] = update.message.text or ''
    
    await update.message.reply_text(
        "📍 **Envoie ta localisation GPS (obligatoire)** :\n\n"
        "Cette position sera transmise immédiatement à l'encadrement.",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("📍 Envoyer ma position", request_location=True)],
            ["🤖 Aide IA"]
        ], one_time_keyboard=True, resize_keyboard=True)
    )
    logging.info(f"[URGENCE] Message reçu pour user {update.effective_user.id}")
    return GPS

async def receive_gps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    if update.message.text in ["🤖 Aide IA", "💬 Aide IA"]:
        assistant = ENCOAIAssistant()
        suggestion = await assistant.generate_railway_response("Aide demandée pour l'étape GPS d'urgence.")
        await update.message.reply_text(f"🤖 Suggestion IA : {suggestion}")
        return GPS
    if not update.message.location:
        await update.message.reply_text("❗ Localisation obligatoire pour signaler une urgence.")
        return GPS
    
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    context.user_data['gps'] = update.message.location
    
    # Récapitulatif avec numéros d'urgence
    numeros_urgence = get_numeros_urgence(context.user_data.get('urgence_type', ''))
    
    await update.message.reply_text(
        f"🚨 **Récapitulatif Urgence**\n\n"
        f"📋 Type : {context.user_data.get('urgence_type', '')}\n"
        f"📝 Description : {context.user_data.get('urgence_message', 'Aucune')}\n"
        f"📍 Position : {update.message.location.latitude:.4f}, {update.message.location.longitude:.4f}\n\n"
        f"📞 **Numéros d'urgence :**\n"
        f"{numeros_urgence}\n\n"
        f"✅ Confirme l'envoi de l'urgence ? (oui/non)",
        reply_markup=ReplyKeyboardMarkup([
            ["oui", "non"],
            ["🤖 Aide IA"]
        ], resize_keyboard=True)
    )
    logging.info(f"[URGENCE] Localisation reçue pour user {update.effective_user.id}")
    return CONFIRM

async def confirm_urgence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    if update.message.text in ["🤖 Aide IA", "💬 Aide IA"]:
        assistant = ENCOAIAssistant()
        suggestion = await assistant.generate_railway_response("Aide demandée pour l'étape confirmation d'urgence.")
        await update.message.reply_text(f"🤖 Suggestion IA : {suggestion}")
        return CONFIRM
    if not update.message.text:
        await update.message.reply_text("Merci de répondre par 'oui' pour confirmer l'urgence.", reply_markup=ReplyKeyboardMarkup([
            ["oui", "non"],
            ["🤖 Aide IA"]
        ], resize_keyboard=True))
        return CONFIRM
    if update.message.text.lower() != "oui":
        await update.message.reply_text("❌ Signalement annulé.", reply_markup=ReplyKeyboardMarkup([
            ["Menu principal"],
            ["🤖 Aide IA"]
        ], resize_keyboard=True))
        logging.info(f"[URGENCE] Annulée pour user {update.effective_user.id}")
        return ConversationHandler.END
    
    user = update.message.from_user
    loc = context.user_data.get('gps')
    if not user or not loc:
        await update.message.reply_text("❌ Erreur : informations utilisateur ou localisation manquantes.")
        return ConversationHandler.END
    
    # Données pour Firestore
    urgence_data = {
        "operateur_id": user.id,
        "operatorId": user.id,
        "nom": user.full_name,
        "timestamp": datetime.now().isoformat(),
        "type": context.user_data.get('urgence_type', ''),
        "description": context.user_data.get('urgence_message', ''),
        "latitude": loc.latitude,
        "longitude": loc.longitude,
        "handled": False,
        "urgence_level": "CRITIQUE",
        "position": {
            "lat": loc.latitude,
            "lng": loc.longitude
        }
    }
    
    # Enrichissement IA si possible
    try:
        assistant = ENCOAIAssistant()
        if assistant.client:
            priority_info = assistant.prioritize_urgence(urgence_data["description"])
            urgence_data["ai_priority"] = priority_info.get("priority")
            urgence_data["ai_reason"] = priority_info.get("reason")
            urgence_data["ai_immediate_action"] = priority_info.get("immediate_action")
            logging.info(f"[URGENCE] Enrichissement IA effectué pour user {user.id}")
    except Exception as e:
        logging.error(f"[URGENCE] Erreur enrichissement IA: {e}")
    
    # Sauvegarder dans Firestore avec gestion d'erreur
    try:
        save_urgence(urgence_data)
        log_msg = f"[URGENCE] Enregistrée pour {user.full_name} ({user.id}) : {urgence_data['type']}"
        logging.info(log_msg)
        print(log_msg)
    
        # Message de confirmation avec numéros d'urgence
        numeros_urgence = get_numeros_urgence(context.user_data.get('urgence_type', ''))
        await update.message.reply_text(
            f"\u2705 **URGENCE ENREGISTR\u00c9E ET TRANSMISE !**\n\n"
            f"\ud83d\udea8 L'encadrement a \u00e9t\u00e9 notifi\u00e9 imm\u00e9diatement.\n"
            f"\ud83d\udccd Ta position a \u00e9t\u00e9 transmise.\n\n"
            f"\ud83d\udcde **Num\u00e9ros d'urgence :**\n"
            f"{numeros_urgence}\n\n"
            f"\ud83d\udd04 Reste en contact avec l'encadrement.",
            reply_markup=ReplyKeyboardMarkup(
                [
                    ["Menu principal", "Signaler une autre urgence"],
                    ["Signaler une anomalie", "Envoyer photo en cours de mission"]
                ], resize_keyboard=True
            )
        )
    except Exception as e:
        logging.error(f"[URGENCE] Erreur Firestore: {e}")
        print(f"[URGENCE] Erreur Firestore: {e}")
        await update.message.reply_text(
            "❌ Erreur lors de l'enregistrement de l'urgence. Merci de réessayer ou contacter un admin.",
            reply_markup=ReplyKeyboardMarkup(
                [["Menu principal"]], resize_keyboard=True
            )
        )
        return ConversationHandler.END
    
    return ConversationHandler.END

def get_urgence_wizard_handler():
    return ConversationHandler(
        entry_points=[
            CommandHandler("urgence", start_urgence_wizard),
            MessageHandler(filters.Regex(r"^🛑 URGENCE / INCIDENT$"), start_urgence_wizard)
        ],
        states={
            TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_type)],
            MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_message)],
            GPS: [MessageHandler(filters.LOCATION | filters.TEXT, receive_gps)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_urgence)],
        },
        fallbacks=[]
    ) 