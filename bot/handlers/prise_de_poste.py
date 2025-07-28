from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters, ContextTypes
from utils.firestore import save_position, db
from services.enco_ai_assistant import ENCOAIAssistant
import logging
from handlers.shared import menu_principal, build_ai_prompt
import os
from dotenv import load_dotenv
load_dotenv()
import firebase_admin
from firebase_admin import credentials
CRED_PATH = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'serviceAccountKey_railway.txt')
BUCKET = os.environ.get('FIREBASE_STORAGE_BUCKET', 'enco-prestarail.firebasestorage.app')
if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.Certificate(CRED_PATH), {'storageBucket': BUCKET})
from PIL import Image
from utils.firestore import upload_photo_to_storage
from datetime import datetime

# Ajout des nouveaux états
GPS, POSTE, POSTE_SAISIE, CHANTIER_CONFIRM, CHANTIER_SAISIE, MACHINE, PHOTOS, CHECKLIST, CONFIRM = range(9)

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
    reply_markup = ReplyKeyboardMarkup([
        [KeyboardButton("📍 Envoyer ma position", request_location=True)],
        ["🤖 Aide IA"]
    ], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "📍 Merci d'envoyer ta localisation GPS pour commencer la prise de poste.",
        reply_markup=reply_markup
    )
    logging.info(f"[PRISE DE POSTE] Demande de localisation pour user {update.effective_user.id}")
    return GPS

async def receive_gps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    if update.message and update.message.text in ["🤖 Aide IA", "💬 Aide IA"]:
        assistant = ENCOAIAssistant()
        prompt = build_ai_prompt("Aide demandée pour l'étape GPS de la prise de poste.", context={"workflow": "prise_de_poste", "etape": "GPS"})
        suggestion = await assistant.generate_railway_response(prompt)
        await update.message.reply_text(f"💡 Suggestion IA : {suggestion}")
        return GPS
    if not update.message.location:
        await update.message.reply_text("❗ Localisation obligatoire pour commencer la prise de poste.")
        return GPS
    context.user_data['gps'] = update.message.location
    # --- AJOUT : récupération du poste habituel ---
    user = update.effective_user
    poste = ''
    try:
        op_doc = db.collection('operateurs').document(str(user.id)).get()
        if op_doc.exists:
            poste = op_doc.to_dict().get('poste', '')
    except Exception as e:
        print(f"Erreur récupération poste opérateur: {e}")
    context.user_data['poste_habituel'] = poste
    if poste:
        reply_markup = ReplyKeyboardMarkup([
            ["Confirmer", "Modifier"],
            ["🤖 Aide IA"]
        ], resize_keyboard=True)
        await update.message.reply_text(f"Ton poste habituel est : {poste}. Veux-tu le confirmer ou le modifier ?", reply_markup=reply_markup)
        return POSTE
    else:
        await update.message.reply_text("Merci de saisir ton poste :", reply_markup=ReplyKeyboardMarkup([["🤖 Aide IA"]], resize_keyboard=True))
        return POSTE_SAISIE

async def receive_poste(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    if update.message.text == "Confirmer":
        context.user_data['poste'] = context.user_data.get('poste_habituel', '')
        # Passe à la confirmation chantier
        chantier = ''
        user = update.effective_user
        try:
            op_doc = db.collection('operateurs').document(str(user.id)).get()
            if op_doc.exists:
                chantier = op_doc.to_dict().get('chantier', '')
        except Exception as e:
            print(f"Erreur récupération chantier opérateur: {e}")
        context.user_data['chantier_habituel'] = chantier
        if chantier:
            reply_markup = ReplyKeyboardMarkup([
                ["Confirmer", "Modifier"],
                ["🤖 Aide IA"]
            ], resize_keyboard=True)
            await update.message.reply_text(f"Ton chantier habituel est : {chantier}. Veux-tu le confirmer ou le modifier ?", reply_markup=reply_markup)
            return CHANTIER_CONFIRM
        else:
            await update.message.reply_text("Merci de saisir ton chantier :", reply_markup=ReplyKeyboardMarkup([["🤖 Aide IA"]], resize_keyboard=True))
            return CHANTIER_SAISIE
    elif update.message.text == "Modifier":
        await update.message.reply_text("Merci de saisir ton poste :", reply_markup=ReplyKeyboardMarkup([["🤖 Aide IA"]], resize_keyboard=True))
        return POSTE_SAISIE
    else:
        await update.message.reply_text("Merci de choisir 'Confirmer' ou 'Modifier'.", reply_markup=ReplyKeyboardMarkup([["Confirmer", "Modifier"], ["🤖 Aide IA"]], resize_keyboard=True))
        return POSTE

async def receive_poste_saisie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    poste = (update.message.text or '').strip()
    if not poste:
        await update.message.reply_text("Merci de saisir un poste valide.")
        return POSTE_SAISIE
    context.user_data['poste'] = poste
    # Passe à la confirmation chantier
    chantier = ''
    user = update.effective_user
    try:
        op_doc = db.collection('operateurs').document(str(user.id)).get()
        if op_doc.exists:
            chantier = op_doc.to_dict().get('chantier', '')
    except Exception as e:
        print(f"Erreur récupération chantier opérateur: {e}")
    context.user_data['chantier_habituel'] = chantier
    if chantier:
        reply_markup = ReplyKeyboardMarkup([
            ["Confirmer", "Modifier"],
            ["🤖 Aide IA"]
        ], resize_keyboard=True)
        await update.message.reply_text(f"Ton chantier habituel est : {chantier}. Veux-tu le confirmer ou le modifier ?", reply_markup=reply_markup)
        return CHANTIER_CONFIRM
    else:
        await update.message.reply_text("Merci de saisir ton chantier :", reply_markup=ReplyKeyboardMarkup([["🤖 Aide IA"]], resize_keyboard=True))
        return CHANTIER_SAISIE

async def receive_chantier_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    if update.message.text == "Confirmer":
        context.user_data['chantier'] = context.user_data.get('chantier_habituel', '')
        return MACHINE
    elif update.message.text == "Modifier":
        await update.message.reply_text("Merci de saisir ton chantier :", reply_markup=ReplyKeyboardMarkup([["🤖 Aide IA"]], resize_keyboard=True))
        return CHANTIER_SAISIE
    else:
        await update.message.reply_text("Merci de choisir 'Confirmer' ou 'Modifier'.", reply_markup=ReplyKeyboardMarkup([["Confirmer", "Modifier"], ["🤖 Aide IA"]], resize_keyboard=True))
        return CHANTIER_CONFIRM

async def receive_chantier_saisie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    chantier = (update.message.text or '').strip()
    if not chantier:
        await update.message.reply_text("Merci de saisir un chantier valide.")
        return CHANTIER_SAISIE
    context.user_data['chantier'] = chantier
    return MACHINE

async def receive_machine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    if update.message and update.message.text in ["🤖 Aide IA", "💬 Aide IA"]:
        assistant = ENCOAIAssistant()
        prompt = build_ai_prompt("Aide demandée pour l'étape Machine de la prise de poste.", context={"workflow": "prise_de_poste", "etape": "MACHINE"})
        suggestion = await assistant.generate_railway_response(prompt)
        await update.message.reply_text(f"💡 Suggestion IA : {suggestion}")
        return MACHINE
    context.user_data['machine'] = update.message.text
    context.user_data['photos'] = []
    context.user_data['photo_index'] = 0
    reply_markup = ReplyKeyboardMarkup([
        ["📸 Prends 4 photos obligatoires :\n1. Avant\n2. Arrière\n3. Côté\n4. Machine\nEnvoie chaque photo une par une."],
        ["🤖 Aide IA"]
    ], resize_keyboard=True)
    await update.message.reply_text(
        "📸 Prends 4 photos obligatoires :\n1. Avant\n2. Arrière\n3. Côté\n4. Machine\nEnvoie chaque photo une par une.",
        reply_markup=reply_markup
    )
    await update.message.reply_text(f"Envoie la {PHOTO_LABELS[0]} :")
    logging.info(f"[PRISE DE POSTE] Machine reçue pour user {update.effective_user.id}")
    return PHOTOS

async def receive_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    if update.message and update.message.text in ["🤖 Aide IA", "💬 Aide IA"]:
        assistant = ENCOAIAssistant()
        prompt = build_ai_prompt("Aide demandée pour l'étape Photos de la prise de poste.", context={"workflow": "prise_de_poste", "etape": "PHOTOS"})
        suggestion = await assistant.generate_railway_response(prompt)
        await update.message.reply_text(f"💡 Suggestion IA : {suggestion}")
        return PHOTOS
    idx = context.user_data.get('photo_index', 0)
    reply_markup = ReplyKeyboardMarkup([
        [f"Envoie la {PHOTO_LABELS[idx]}"] ,
        ["🤖 Aide IA"]
    ], resize_keyboard=True)
    if not update.message.photo:
        await update.message.reply_text(f"❗ Envoie la {PHOTO_LABELS[idx]}.", reply_markup=reply_markup)
        return PHOTOS

    # --- AJOUT : Sauvegarde et upload de la photo ---
    user = update.effective_user
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    local_dir = f"bot/photos/{user.id}"
    os.makedirs(local_dir, exist_ok=True)
    file_name = f"{user.id}_prise_{idx}_{update.message.date.strftime('%Y%m%d_%H%M%S')}.jpg"
    file_path = f"{local_dir}/{file_name}"
    await file.download_to_drive(file_path)

    # Optimisation image (optionnel)
    try:
        with Image.open(file_path) as img:
            img.thumbnail((1024, 1024))
            img.save(file_path, "JPEG")
    except Exception as e:
        print(f"Erreur resize: {e}")

    firebase_path = f"prises_poste/{user.id}/{file_name}"
    photo_url = upload_photo_to_storage(file_path, firebase_path)
    print("DEBUG photo_url uploadée:", photo_url)

    # Stocke le file_id ET l'URL
    context.user_data['photos'].append(photo.file_id)
    # Correction: toujours initialiser photos_urls comme une liste
    if 'photos_urls' not in context.user_data or not isinstance(context.user_data['photos_urls'], list):
        context.user_data['photos_urls'] = []
    if photo_url:
        context.user_data['photos_urls'].append(photo_url)
    print("DEBUG photos_urls après ajout:", context.user_data['photos_urls'])

    photo_doc = {
        "photo_file_id": photo.file_id,
        "url": photo_url,
        "timestamp": update.message.date.isoformat(),
        "type": "prise_de_poste",
        "operatorId": user.id,
        "operatorName": user.full_name,
        "chantier": context.user_data.get('chantier', ''),
        "machine": context.user_data.get('machine', ''),
    }
    db.collection('photos').add(photo_doc)

    idx += 1
    context.user_data['photo_index'] = idx
    if idx < 4:
        await update.message.reply_text(f"Envoie la {PHOTO_LABELS[idx]} :")
        return PHOTOS
    # Toutes les photos reçues
    context.user_data['checklist_answers'] = []
    context.user_data['checklist_index'] = 0
    reply_markup = ReplyKeyboardMarkup([
        ["✅ 4 photos reçues.\nChecklist obligatoire :\n1. Vérification machine effectuée ? (oui/non)\n2. EPI portés ? (oui/non)\n3. Radio testée ? (oui/non)\n4. Signalisation comprise ? (oui/non)\n5. Zone de travail sécurisée ? (oui/non)"],
        ["🤖 Aide IA"]
    ], resize_keyboard=True)
    await update.message.reply_text(
        "✅ 4 photos reçues.\nChecklist obligatoire :\n1. Vérification machine effectuée ? (oui/non)\n2. EPI portés ? (oui/non)\n3. Radio testée ? (oui/non)\n4. Signalisation comprise ? (oui/non)\n5. Zone de travail sécurisée ? (oui/non)",
        reply_markup=reply_markup
    )
    logging.info(f"[PRISE DE POSTE] 4 photos reçues pour user {update.effective_user.id}")
    return CHECKLIST

async def receive_checklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    if update.message and update.message.text in ["🤖 Aide IA", "💬 Aide IA"]:
        assistant = ENCOAIAssistant()
        prompt = build_ai_prompt("Aide demandée pour l'étape Checklist de la prise de poste.", context={"workflow": "prise_de_poste", "etape": "CHECKLIST"})
        suggestion = await assistant.generate_railway_response(prompt)
        await update.message.reply_text(f"💡 Suggestion IA : {suggestion}")
        return CHECKLIST
    idx = context.user_data.get('checklist_index', 0)
    reply_markup = ReplyKeyboardMarkup([
        ["oui", "non"],
        ["🤖 Aide IA"]
    ], resize_keyboard=True)
    if not update.message.text:
        await update.message.reply_text("Merci de répondre par 'oui' ou 'non'.", reply_markup=reply_markup)
        return CHECKLIST
    answer = update.message.text.lower()
    if answer not in ["oui", "non"]:
        await update.message.reply_text("Merci de répondre par 'oui' ou 'non'.", reply_markup=reply_markup)
        return CHECKLIST
    context.user_data['checklist_answers'].append(answer)
    idx += 1
    if idx < len(CHECKLIST_QUESTIONS):
        context.user_data['checklist_index'] = idx
        reply_markup = ReplyKeyboardMarkup([
            [f"{CHECKLIST_QUESTIONS[idx]} (oui/non)"],
            ["🤖 Aide IA"]
        ], resize_keyboard=True)
        await update.message.reply_text(
            f"{CHECKLIST_QUESTIONS[idx]} (oui/non)",
            reply_markup=reply_markup
        )
        return CHECKLIST
    # Toutes les questions répondues
    context.user_data['checklist'] = {
        q: a for q, a in zip(CHECKLIST_QUESTIONS, context.user_data['checklist_answers'])
    }
    reply_markup = ReplyKeyboardMarkup([
        ["✅ Checklist terminée. Confirme la prise de poste ? (oui/non)"],
        ["🤖 Aide IA"]
    ], resize_keyboard=True)
    await update.message.reply_text(
        "✅ Checklist terminée. Confirme la prise de poste ? (oui/non)",
        reply_markup=reply_markup
    )
    logging.info(f"[PRISE DE POSTE] Checklist terminée pour user {update.effective_user.id}")
    return CONFIRM

async def confirm_prise(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    if update.message and update.message.text in ["🤖 Aide IA", "💬 Aide IA"]:
        assistant = ENCOAIAssistant()
        prompt = build_ai_prompt("Aide demandée pour l'étape Confirmation de la prise de poste.", context={"workflow": "prise_de_poste", "etape": "CONFIRM"})
        suggestion = await assistant.generate_railway_response(prompt)
        await update.message.reply_text(f"💡 Suggestion IA : {suggestion}")
        return CONFIRM
    reply_markup = ReplyKeyboardMarkup([
        ["oui", "non"],
        ["🤖 Aide IA"]
    ], resize_keyboard=True)
    if not update.message.text:
        await update.message.reply_text("Merci de répondre par 'oui' pour confirmer la prise de poste.", reply_markup=reply_markup)
        return CONFIRM
    if update.message.text.lower() != "oui":
        await update.message.reply_text("❌ Prise de poste annulée.", reply_markup=reply_markup)
        logging.info(f"[PRISE DE POSTE] Annulée pour user {update.effective_user.id}")
        return ConversationHandler.END
    user = update.message.from_user
    loc = context.user_data.get('gps')
    if not user or not loc:
        await update.message.reply_text("❌ Erreur : informations utilisateur ou localisation manquantes.")
        return ConversationHandler.END
    # --- AJOUT : récupération automatique du poste depuis Firestore ---
    poste = ''
    try:
        op_doc = db.collection('operateurs').document(str(user.id)).get()
        if op_doc.exists:
            poste = op_doc.to_dict().get('poste', '')
    except Exception as e:
        print(f"Erreur récupération poste opérateur: {e}")
    context.user_data['poste'] = poste
    # --- FIN AJOUT ---
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
        "poste": context.user_data.get('poste', ''),
        "photos_file_ids": context.user_data.get('photos', []),
        "photos_urls": context.user_data.get('photos_urls', []),
        "actif": True,
        "checklist": context.user_data.get('checklist', {}),
        "checklistEffectuee": True
    }
    save_position(position_data)
    # Patch: garantir la synchronisation et la présence de photos_urls
    photos_urls = context.user_data.get('photos_urls')
    if not isinstance(photos_urls, list):
        photos_urls = []
    print("DEBUG photos_urls juste avant Firestore:", photos_urls)
    db.collection('prises_poste').add({
        "operatorId": user.id,
        "nom": user.full_name,
        "timestamp": update.message.date.isoformat(),
        "latitude": loc.latitude,
        "longitude": loc.longitude,
        "chantier": context.user_data.get('chantier', ''),
        "machine": context.user_data.get('machine', ''),
        "poste": context.user_data.get('poste', ''),
        "photos_file_ids": context.user_data.get('photos', []),
        "photos_urls": photos_urls,
        "type": "prise_de_poste",
        "checklist": context.user_data.get('checklist', {}),
        "checklistEffectuee": True
    })
    logging.info(f"[PRISE DE POSTE] Enregistrée pour user {user.id}")
    await update.message.reply_text("✅ Prise de poste enregistrée. Prudence et bon courage !", reply_markup=ReplyKeyboardMarkup([["👍"], ["🤖 Aide IA"]], resize_keyboard=True))
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
            MessageHandler(filters.Regex(r"^📌 Prise de poste$"), start_prise_wizard)
        ],
        states={
            GPS: [MessageHandler(filters.LOCATION | filters.TEXT & ~filters.COMMAND, receive_gps)],
            POSTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_poste)],
            POSTE_SAISIE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_poste_saisie)],
            CHANTIER_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_chantier_confirm)],
            CHANTIER_SAISIE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_chantier_saisie)],
            MACHINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_machine)],
            PHOTOS: [MessageHandler(filters.PHOTO | filters.TEXT & ~filters.COMMAND, receive_photos)],
            CHECKLIST: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_checklist)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_prise)],
        },
        fallbacks=[]
    ) 