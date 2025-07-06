from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters, ContextTypes
from utils.firestore import save_anomalie, db
from datetime import datetime
from services.enco_ai_assistant import ENCOAIAssistant
import logging

MACHINE, TYPE_ANOMALIE, DESCRIPTION, PHOTO, GPS, CONFIRM = range(6)

# Types de machines
MACHINES = [
    ["🚜 CAT 323 M", "🚛 D2R"],
    ["🏗️ ATLAS 1404", "🔧 MECALAC"],
    ["Autre machine"]
]

# Types d'anomalies spécifiques par catégorie
ANOMALIES_HYDRAULIQUE = [
    ["💧 Fuite hydraulique", "🔧 Pression faible"],
    ["⚙️ Pompe hydraulique", "🔄 Circuit bouché"],
    ["Autre anomalie hydraulique"]
]

ANOMALIES_MOTEUR = [
    ["🔥 Surchauffe moteur", "💨 Fumée moteur"],
    ["🔊 Bruit anormal", "⚡ Démarrage difficile"],
    ["⛽ Consommation excessive", "Autre anomalie moteur"]
]

ANOMALIES_BALISE = [
    ["📡 Balise défaillante", "🔌 Connexion balise"],
    ["📶 Signal faible", "🔄 Synchronisation"],
    ["Autre anomalie balise"]
]

ANOMALIES_ELECTRIQUE = [
    ["⚡ Panne électrique", "💡 Éclairage défaillant"],
    ["🔋 Batterie faible", "🔌 Connecteurs"],
    ["Autre anomalie électrique"]
]

ANOMALIES_MECANIQUE = [
    ["🔧 Bras lent", "⚙️ Engrenages"],
    ["🛞 Roues / Chenilles", "🔗 Articulations"],
    ["Autre anomalie mécanique"]
]

async def start_anomalie_wizard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"[ANOMALIE] Wizard lancé par: {update.message.text if update.message else 'N/A'} | user: {update.effective_user.id if update.effective_user else 'N/A'}")
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    await update.message.reply_text(
        "🔧 **DÉCLARATION DE PANNE**\n\nSélectionne la machine concernée :",
        reply_markup=ReplyKeyboardMarkup(MACHINES, one_time_keyboard=True, resize_keyboard=True)
    )
    return MACHINE

async def receive_machine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    # Filet de sécurité IA : vérifier si la machine est attendue
    machine_text = update.message.text
    machines_flat = [item for sublist in MACHINES for item in sublist]
    if machine_text not in machines_flat:
        # Appel IA pour aider l'opérateur
        assistant = ENCOAIAssistant()
        suggestion = await assistant.generate_railway_response(
            f"L'utilisateur a répondu '{machine_text}' à la question 'Sélectionne la machine concernée'. Propose une reformulation ou une aide pour cette étape métier ferroviaire.")
        await update.message.reply_text(f"🤖 Suggestion IA : {suggestion}")
        return MACHINE
    context.user_data['machine'] = machine_text
    
    await update.message.reply_text(
        f"🔧 **{machine_text}**\n\nSélectionne le type d'anomalie :",
        reply_markup=ReplyKeyboardMarkup([
            ["🔧 Hydraulique", "🔥 Moteur"],
            ["📡 Balise / Signalisation", "⚡ Électrique"],
            ["⚙️ Mécanique", "Autre anomalie"]
        ], one_time_keyboard=True, resize_keyboard=True)
    )
    logging.info(f"[ANOMALIE] Machine sélectionnée: {machine_text} pour user {update.effective_user.id}")
    return TYPE_ANOMALIE

async def receive_type_anomalie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    type_anomalie = update.message.text
    # Filet de sécurité IA : vérifier si le type est attendu
    types_attendus = ["🔧 Hydraulique", "🔥 Moteur", "📡 Balise / Signalisation", "⚡ Électrique", "⚙️ Mécanique", "Autre anomalie"]
    if type_anomalie not in types_attendus:
        assistant = ENCOAIAssistant()
        suggestion = await assistant.generate_railway_response(
            f"L'utilisateur a répondu '{type_anomalie}' à la question 'Sélectionne le type d'anomalie'. Propose une reformulation ou une aide pour cette étape métier ferroviaire.")
        await update.message.reply_text(f"🤖 Suggestion IA : {suggestion}")
        return TYPE_ANOMALIE
    context.user_data['type_anomalie'] = type_anomalie
    
    # Sélectionner la liste d'anomalies selon le type
    if type_anomalie and "Hydraulique" in type_anomalie:
        anomalies_list = ANOMALIES_HYDRAULIQUE
    elif type_anomalie and "Moteur" in type_anomalie:
        anomalies_list = ANOMALIES_MOTEUR
    elif type_anomalie and "Balise" in type_anomalie:
        anomalies_list = ANOMALIES_BALISE
    elif type_anomalie and "Électrique" in type_anomalie:
        anomalies_list = ANOMALIES_ELECTRIQUE
    elif type_anomalie and "Mécanique" in type_anomalie:
        anomalies_list = ANOMALIES_MECANIQUE
    else:
        # Pour "Autre anomalie", passer directement à la description
        await update.message.reply_text("📝 Décris l'anomalie rencontrée :")
        logging.info(f"[ANOMALIE] Type sélectionné: {type_anomalie} pour user {update.effective_user.id}")
        return DESCRIPTION
    
    await update.message.reply_text(
        f"🔧 **{type_anomalie}**\n\n"
        f"Sélectionne l'anomalie spécifique :",
        reply_markup=ReplyKeyboardMarkup(anomalies_list, one_time_keyboard=True, resize_keyboard=True)
    )
    logging.info(f"[ANOMALIE] Type sélectionné: {type_anomalie} pour user {update.effective_user.id}")
    return DESCRIPTION

async def receive_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    # Si on vient de la sélection d'anomalie spécifique
    if context.user_data.get('type_anomalie') and not context.user_data.get('anomalie_specifique'):
        context.user_data['anomalie_specifique'] = update.message.text
        await update.message.reply_text("📝 Ajoute des détails sur l'anomalie (optionnel, tape 'skip' pour passer) :")
        logging.info(f"[ANOMALIE] Anomalie spécifique: {update.message.text} pour user {update.effective_user.id}")
        return DESCRIPTION
    
    # Sinon, c'est la description libre
    if update.message.text and update.message.text.lower() == 'skip':
        context.user_data['description'] = ''
    else:
        context.user_data['description'] = update.message.text or ''
    
    await update.message.reply_text("📸 Prends une photo de l'anomalie (obligatoire) :")
    logging.info(f"[ANOMALIE] Description ajoutée pour user {update.effective_user.id}")
    return PHOTO

async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    if not update.message.photo:
        await update.message.reply_text("❗ Photo obligatoire pour signaler une anomalie.")
        return PHOTO
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    context.user_data['photo'] = update.message.photo[-1].file_id
    await update.message.reply_text(
        "📍 Envoie ta localisation GPS (obligatoire) :",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📍 Envoyer ma position", request_location=True)]],
            one_time_keyboard=True, resize_keyboard=True
        )
    )
    logging.info(f"[ANOMALIE] Photo reçue pour user {update.effective_user.id}")
    return GPS

async def receive_gps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    if not update.message.location:
        await update.message.reply_text("❗ Localisation obligatoire pour signaler une anomalie.")
        return GPS
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    context.user_data['gps'] = update.message.location
    
    # Récapitulatif
    machine = context.user_data.get('machine', '')
    type_anomalie = context.user_data.get('type_anomalie', '')
    anomalie_specifique = context.user_data.get('anomalie_specifique', '')
    description = context.user_data.get('description', 'Aucune')
    
    await update.message.reply_text(
        f"🔧 **Récapitulatif Anomalie**\n\n"
        f"🚜 Machine : {machine}\n"
        f"🔧 Type : {type_anomalie}\n"
        f"📋 Anomalie : {anomalie_specifique}\n"
        f"📝 Détails : {description}\n"
        f"📍 Position : {update.message.location.latitude:.4f}, {update.message.location.longitude:.4f}\n\n"
        f"✅ Confirme l'envoi de l'anomalie ? (oui/non)"
    )
    logging.info(f"[ANOMALIE] Localisation reçue pour user {update.effective_user.id}")
    return CONFIRM

async def confirm_anomalie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    if not update.message.text:
        await update.message.reply_text("Merci de répondre par 'oui' pour confirmer l'anomalie.")
        return CONFIRM
    if update.message.text.lower() != "oui":
        await update.message.reply_text("❌ Signalement annulé.")
        logging.info(f"[ANOMALIE] Annulée pour user {update.effective_user.id}")
        return ConversationHandler.END
    
    user = update.message.from_user
    loc = context.user_data.get('gps')
    if not user or not loc:
        await update.message.reply_text("❌ Erreur : informations utilisateur ou localisation manquantes.")
        return ConversationHandler.END
    
    # Données pour Firestore
    anomalie_data = {
        "operateur_id": user.id,
        "operatorId": user.id,
        "nom": user.full_name,
        "timestamp": datetime.now().isoformat(),
        "machine": context.user_data.get('machine', ''),
        "type_anomalie": context.user_data.get('type_anomalie', ''),
        "anomalie_specifique": context.user_data.get('anomalie_specifique', ''),
        "description": context.user_data.get('description', ''),
        "latitude": loc.latitude,
        "longitude": loc.longitude,
        "photo_file_id": context.user_data.get('photo'),
        "handled": False,
        "urgence_level": "NORMAL"
    }
    
    # Enrichissement IA si possible
    ai_feedback = ""
    try:
        assistant = ENCOAIAssistant()
        if assistant.client:
            ai_category = assistant.categorize_anomalie(anomalie_data["description"])
            ai_priority = assistant.prioritize_urgence(anomalie_data["description"])
            ai_suggestion = assistant.suggest_anomalie_resolution(anomalie_data["description"])
            anomalie_data["ai_category"] = ai_category
            anomalie_data["ai_priority"] = ai_priority.get('priority')
            anomalie_data["ai_reason"] = ai_priority.get('reason')
            anomalie_data["ai_immediate_action"] = ai_priority.get('immediate_action')
            anomalie_data["ai_suggestion"] = ai_suggestion
            ai_feedback = f"\n\n🏷️ Catégorie IA : {ai_category or 'Non catégorisée'}\n⚠️ Priorité IA : {ai_priority.get('priority', 'N/A').upper()}\n💡 Suggestion IA : {ai_suggestion or 'Aucune'}"
            logging.info(f"[ANOMALIE] Enrichissement IA effectué pour user {user.id}")
    except Exception as e:
        logging.error(f"[ANOMALIE] Erreur enrichissement IA: {e}")
    
    save_anomalie(anomalie_data)
    logging.info(f"[ANOMALIE] Enregistrée pour user {user.id}")
    
    await update.message.reply_text(
        f"\u2705 **ANOMALIE ENREGISTR\u00c9E !**\n\n"
        f"\ud83d\udd27 L'anomalie a \u00e9t\u00e9 transmise \u00e0 l'encadrement.\n"
        f"\ud83d\udcf8 Photo et position enregistr\u00e9es.\n"
        f"\ud83d\udd04 Tu seras contact\u00e9 pour le suivi."
        f"{ai_feedback}",
        reply_markup=ReplyKeyboardMarkup(
            [
                ["Menu principal", "D\u00e9clarer une autre anomalie"],
                ["URGENCE SNCF", "Envoyer photo en cours de mission"]
            ], resize_keyboard=True
        )
    )
    return ConversationHandler.END

def get_anomalie_wizard_handler():
    return ConversationHandler(
        entry_points=[
            CommandHandler("anomalie", start_anomalie_wizard),
            MessageHandler(filters.Regex("^Déclarer une anomalie$"), start_anomalie_wizard),
            MessageHandler(filters.Regex("^Déclarer une panne$"), start_anomalie_wizard),
            MessageHandler(filters.Regex("^Déclarer une autre anomalie$"), start_anomalie_wizard)
        ],
        states={
            MACHINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_machine)],
            TYPE_ANOMALIE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_type_anomalie)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_description)],
            PHOTO: [MessageHandler(filters.PHOTO, receive_photo)],
            GPS: [MessageHandler(filters.LOCATION, receive_gps)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_anomalie)],
        },
        fallbacks=[]
    )