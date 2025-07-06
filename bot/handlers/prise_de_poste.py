from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters, ContextTypes
from utils.firestore import save_position, db
from services.enco_ai_assistant import ENCOAIAssistant
import logging
from handlers.shared import menu_principal

GPS, CHANTIER, MACHINE, PHOTOS, CHECKLIST, CONFIRM = range(6)

PHOTO_LABELS = ["Photo avant", "Photo arrière", "Photo côté", "Photo machine"]
CHECKLIST_QUESTIONS = [
    "Vérification machine effectuée ?",
    "EPI portés ?",
    "Radio testée ?",
    "Signalisation comprise ?",
    "Zone de travail sécurisée ?"
]

async def start_prise_wizard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    await update.message.reply_text(
        "📍 Merci d'envoyer ta localisation GPS pour commencer la prise de poste.",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📍 Envoyer ma position", request_location=True)]],
            one_time_keyboard=True, resize_keyboard=True
        )
    )
    logging.info(f"[PRISE DE POSTE] Demande de localisation pour user {update.effective_user.id}")
    return GPS

async def receive_gps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    if not update.message.location:
        await update.message.reply_text("❗ Localisation obligatoire pour commencer la prise de poste.")
        return GPS
    context.user_data['gps'] = update.message.location
    await update.message.reply_text("🏗 Indique le chantier (ou scanne le QR code chantier) :")
    logging.info(f"[PRISE DE POSTE] Localisation reçue pour user {update.effective_user.id}")
    return CHANTIER

async def receive_chantier(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    context.user_data['chantier'] = update.message.text
    await update.message.reply_text("🚜 Scanne le QR code machine ou saisis l'ID machine :")
    logging.info(f"[PRISE DE POSTE] Chantier reçu pour user {update.effective_user.id}")
    return MACHINE

async def receive_machine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    context.user_data['machine'] = update.message.text
    context.user_data['photos'] = []
    context.user_data['photo_index'] = 0
    await update.message.reply_text(f"📸 Prends 4 photos obligatoires :\n1. Avant\n2. Arrière\n3. Côté\n4. Machine\nEnvoie chaque photo une par une.")
    await update.message.reply_text(f"Envoie la {PHOTO_LABELS[0]} :")
    logging.info(f"[PRISE DE POSTE] Machine reçue pour user {update.effective_user.id}")
    return PHOTOS

async def receive_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    idx = context.user_data.get('photo_index', 0)
    if not update.message.photo:
        await update.message.reply_text(f"❗ Envoie la {PHOTO_LABELS[idx]}.")
        return PHOTOS
    context.user_data['photos'].append(update.message.photo[-1].file_id)
    idx += 1
    context.user_data['photo_index'] = idx
    if idx < 4:
        await update.message.reply_text(f"Envoie la {PHOTO_LABELS[idx]} :")
        return PHOTOS
    # Toutes les photos reçues
    context.user_data['checklist_answers'] = []
    context.user_data['checklist_index'] = 0
    await update.message.reply_text(f"✅ 4 photos reçues.\nChecklist obligatoire :\n{CHECKLIST_QUESTIONS[0]} (oui/non)")
    logging.info(f"[PRISE DE POSTE] 4 photos reçues pour user {update.effective_user.id}")
    return CHECKLIST

async def receive_checklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    idx = context.user_data.get('checklist_index', 0)
    if not update.message.text:
        await update.message.reply_text("Merci de répondre par 'oui' ou 'non'.")
        return CHECKLIST
    answer = update.message.text.lower()
    if answer not in ["oui", "non"]:
        await update.message.reply_text("Merci de répondre par 'oui' ou 'non'.")
        return CHECKLIST
    context.user_data['checklist_answers'].append(answer)
    idx += 1
    if idx < len(CHECKLIST_QUESTIONS):
        context.user_data['checklist_index'] = idx
        await update.message.reply_text(f"{CHECKLIST_QUESTIONS[idx]} (oui/non)")
        return CHECKLIST
    # Toutes les questions répondues
    context.user_data['checklist'] = {
        q: a for q, a in zip(CHECKLIST_QUESTIONS, context.user_data['checklist_answers'])
    }
    await update.message.reply_text("✅ Checklist terminée. Confirme la prise de poste ? (oui/non)")
    logging.info(f"[PRISE DE POSTE] Checklist terminée pour user {update.effective_user.id}")
    return CONFIRM

async def confirm_prise(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    if not update.message.text:
        await update.message.reply_text("Merci de répondre par 'oui' pour confirmer la prise de poste.")
        return CONFIRM
    if update.message.text.lower() != "oui":
        await update.message.reply_text("❌ Prise de poste annulée.")
        logging.info(f"[PRISE DE POSTE] Annulée pour user {update.effective_user.id}")
        return ConversationHandler.END
    user = update.message.from_user
    loc = context.user_data.get('gps')
    if not user or not loc:
        await update.message.reply_text("❌ Erreur : informations utilisateur ou localisation manquantes.")
        return ConversationHandler.END
    position_data = {
        "operateur_id": user.id,
        "operatorId": user.id,
        "nom": user.full_name,
        "timestamp": update.message.date.isoformat(),
        "latitude": loc.latitude,
        "longitude": loc.longitude,
        "type": "prise_de_poste",
        "chantier": context.user_data.get('chantier', ''),
        "machine": context.user_data.get('machine', ''),
        "photos_file_ids": context.user_data.get('photos', []),
        "actif": True,
        "checklist": context.user_data.get('checklist', {}),
        "checklistEffectuee": True
    }
    save_position(position_data)
    db.collection('prises_poste').add({
        "operatorId": user.id,
        "nom": user.full_name,
        "timestamp": update.message.date.isoformat(),
        "latitude": loc.latitude,
        "longitude": loc.longitude,
        "chantier": context.user_data.get('chantier', ''),
        "machine": context.user_data.get('machine', ''),
        "photos_file_ids": context.user_data.get('photos', []),
        "type": "prise_de_poste",
        "checklist": context.user_data.get('checklist', {}),
        "checklistEffectuee": True
    })
    logging.info(f"[PRISE DE POSTE] Enregistrée pour user {user.id}")
    await update.message.reply_text("✅ Prise de poste enregistrée. Prudence et bon courage !")
    # Appel IA pour suggestion ou feedback
    try:
        assistant = ENCOAIAssistant()
        prompt = f"Prise de poste opérateur :\nChantier : {context.user_data.get('chantier', '')}\nMachine : {context.user_data.get('machine', '')}\nChecklist : {context.user_data.get('checklist', {})}"
        suggestion = await assistant.generate_railway_response(prompt)
        if suggestion:
            await update.message.reply_text(f"💡 Suggestion IA : {suggestion}")
            logging.info(f"[PRISE DE POSTE] Suggestion IA envoyée à user {user.id}")
    except Exception as e:
        logging.error(f"[PRISE DE POSTE] Erreur appel IA : {e}")
    # Affiche le menu principal classique
    await menu_principal(update, context)
    return ConversationHandler.END

def get_prise_wizard_handler():
    return ConversationHandler(
        entry_points=[
            CommandHandler("prise", start_prise_wizard),
            MessageHandler(filters.Regex("^Commencer ma prise de poste$"), start_prise_wizard)
        ],
        states={
            GPS: [MessageHandler(filters.LOCATION, receive_gps)],
            CHANTIER: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_chantier)],
            MACHINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_machine)],
            PHOTOS: [MessageHandler(filters.PHOTO, receive_photos)],
            CHECKLIST: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_checklist)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_prise)],
        },
        fallbacks=[]
    ) 