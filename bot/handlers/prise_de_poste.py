from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters, ContextTypes
from utils.firestore import save_position, db

GPS, CHANTIER, MACHINE, PHOTOS, CHECKLIST, CONFIRM = range(6)

# Questions checklist standard
CHECKLIST_QUESTIONS = [
    "Vérification machine effectuée ?",
    "EPI portés ?",
    "Radio testée ?",
    "Signalisation comprise ?",
    "Zone de travail sécurisée ?"
]

async def start_prise_wizard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📍 Merci d'envoyer ta localisation GPS pour commencer la prise de poste.",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📍 Envoyer ma position", request_location=True)]],
            one_time_keyboard=True, resize_keyboard=True
        )
    )
    return GPS

async def receive_gps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.location:
        await update.message.reply_text("❗ Localisation obligatoire pour commencer la prise de poste.")
        return GPS
    context.user_data['gps'] = update.message.location
    await update.message.reply_text("🏗 Indique le chantier (ou scanne le QR code chantier) :")
    return CHANTIER

async def receive_chantier(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['chantier'] = update.message.text
    await update.message.reply_text("🚜 Scanne le QR code machine ou saisis l'ID machine :")
    return MACHINE

async def receive_machine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['machine'] = update.message.text
    context.user_data['photos'] = []
    await update.message.reply_text("📸 Prends des photos de la machine et de la zone de travail (obligatoire).\nEnvoie plusieurs photos si nécessaire, puis tape 'Terminer photos' quand tu as fini.")
    return PHOTOS

async def receive_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text and update.message.text.lower() == "terminer photos":
        if not context.user_data.get('photos'):
            await update.message.reply_text("❗ Au moins une photo est obligatoire pour valider la prise de poste.")
            return PHOTOS
        # Démarrer la checklist
        context.user_data['checklist_answers'] = []
        context.user_data['checklist_index'] = 0
        await update.message.reply_text(f"✅ Photos reçues ({len(context.user_data['photos'])} photo(s)).\n\nChecklist obligatoire :\n{CHECKLIST_QUESTIONS[0]} (oui/non)")
        return CHECKLIST
    
    if not update.message.photo:
        await update.message.reply_text("❗ Envoie une photo ou tape 'Terminer photos'.")
        return PHOTOS
    
    context.user_data['photos'].append(update.message.photo[-1].file_id)
    await update.message.reply_text(f"✅ Photo {len(context.user_data['photos'])} reçue. Envoie une autre photo ou tape 'Terminer photos'.")
    return PHOTOS

async def receive_checklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idx = context.user_data.get('checklist_index', 0)
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
    return CONFIRM

async def confirm_prise(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.lower() != "oui":
        await update.message.reply_text("❌ Prise de poste annulée.")
        return ConversationHandler.END
    user = update.message.from_user
    loc = context.user_data['gps']
    # Firestore : positions_operateurs (unique), positions_log (historique), prises_poste (historique détaillé)
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
    # Historique détaillé
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
    await update.message.reply_text("✅ Prise de poste enregistrée !", reply_markup=ReplyKeyboardMarkup(
        [
            ["Voir ma localisation & infos", "Déclarer une panne"],
            ["URGENCE SNCF", "Envoyer photo en cours de mission"],
            ["Fin de poste / Bon papier", "Coffre-fort machine"],
            ["Outils ferroviaires / Géoportail SNCF", "Modifier ma machine / chantier"],
            ["Voir mes stats", "Clôturer ma session"]
        ], resize_keyboard=True
    ))
    await update.message.reply_text("✅ Poste terminé.\nMerci pour ton travail aujourd'hui 💪\nTon bon est bien enregistré. À demain !")
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
            PHOTOS: [MessageHandler(filters.PHOTO | filters.TEXT, receive_photos)],
            CHECKLIST: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_checklist)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_prise)],
        },
        fallbacks=[]
    ) 