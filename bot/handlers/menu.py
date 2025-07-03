from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from handlers.prise_de_poste import start_prise
from handlers.fin_de_poste import start_fin
from handlers.checklist import start_checklist
from handlers.anomalie import get_anomalie_handler
from handlers.consult_docs import consulter_documents
from handlers.historique import afficher_historique
from handlers.urgence import urgence, hors_voie
from handlers.portail import portail_sncf
from utils.firestore import db
import datetime
import io
from PIL import Image
from pyzbar.pyzbar import decode as decode_qr
import os
from handlers.photo import start_photo

MENU_KEYBOARD = [
    ["📌 Prise de poste", "📷 Envoyer une photo"],
    ["📄 Envoyer bon signé", "🛑 URGENCE / INCIDENT"],
    ["🚧 Portail SNCF / Plan accès", "🔧 Rapport technique machine"],
    ["🗓️ Planning", "📦 Scan Matériel / Retrait PL (à venir)"]
]

async def menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = ReplyKeyboardMarkup(MENU_KEYBOARD, resize_keyboard=True)
    await update.message.reply_text(
        "👋 Bienvenue sur ENCO Bot !\n\n"
        "Voici ce que tu peux faire :\n"
        "📌 Prise de poste : démarre ta journée\n"
        "🖼️ Envoyer une photo : signale un état ou une anomalie\n"
        "🛑 Urgence : déclare un incident immédiat\n"
        "📄 Bon signé : envoie un bon d'attachement\n"
        "🗺️ Planning, QR code, etc.\n\n"
        "Utilise les boutons ci-dessous pour naviguer, ou tape /aide pour plus d'infos.",
        reply_markup=reply_markup
    )

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "📌 Prise de poste":
        await start_prise(update, context)
        await menu_principal(update, context)
    elif text == "📷 Envoyer une photo":
        await start_photo(update, context)
        await menu_principal(update, context)
    elif text == "📄 Envoyer bon signé":
        await start_fin(update, context)
        await menu_principal(update, context)
    elif text == "🛑 URGENCE / INCIDENT":
        await urgence(update, context)
        await menu_principal(update, context)
    elif text == "🚧 Portail SNCF / Plan accès":
        await portail_sncf(update, context)
        await menu_principal(update, context)
    elif text == "🔧 Rapport technique machine":
        await declare_panne_start(update, context)
        await menu_principal(update, context)
    elif text == "🗓️ Planning":
        await planning_handler(update, context)
        await menu_principal(update, context)
    elif text == "📦 Scan Matériel / Retrait PL (à venir)":
        await scan_qr_start(update, context)
        await menu_principal(update, context)
    else:
        await menu_principal(update, context)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["Envoyer une photo", "Partager ma position"],
        ["Checklist sécurité", "Déclencher une urgence"],
        ["Mise hors voie urgente", "Portail d'accès SNCF"],
        ["Fiches techniques", "Aide"],
        ["Historique", "Paramètres"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "👋 *Bienvenue sur le bot ENCO !*\n\n"
        "Utilisez le menu ci-dessous ou tapez une commande (/checklist, /aide, /docs, /historique, etc.) pour accéder aux fonctions :",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def aide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *Aide ENCO*\n\n"
        "• *Prise de poste* : Démarre ta journée, envoie ta position.\n"
        "• *Envoyer une photo* : Pour signaler un problème ou un état machine.\n"
        "• *Urgence* : Déclare un incident immédiat, partage ta position.\n"
        "• *Bon signé* : Envoie un bon d'attachement lié à ta prise.\n"
        "• *Planning* : Récapitulatif de ta journée.\n"
        "• *Scan QR code* : Associe un matériel à ta prise.\n\n"
        "Utilise toujours les boutons, pas de commandes texte !",
        parse_mode="Markdown"
    )

async def welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Message de bienvenue pour tous les messages non-commandes"""
    keyboard = [
        ["Envoyer une photo", "Partager ma position"],
        ["Checklist sécurité", "Déclencher une urgence"],
        ["Mise hors voie urgente", "Portail d'accès SNCF"],
        ["Fiches techniques", "Aide"],
        ["Historique", "Paramètres"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "🚀 *Bienvenue sur ENCO Bot !*\n\n"
        "**Commandes rapides :**\n"
        "• `/prise` - Prise de poste\n"
        "• `/fin` - Fin de poste\n"
        "• `/checklist` - Checklist sécurité\n"
        "• `/anomalie` - Signaler une anomalie\n"
        "• `/docs` - Consulter documents\n"
        "• `/historique` - Voir l'historique\n"
        "• `/aide` - Aide complète\n\n"
        "**Ou utilisez le menu ci-dessous :**",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def planning_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not update.message:
        return
    today = datetime.datetime.now().date().isoformat()
    # 1. Prise de poste du jour
    prise = None
    for doc in db.collection('prises_poste').where('operateur_id', '==', str(user.id)).where('heure', '>=', today).stream():
        prise = doc.to_dict()
        break
    # 2. Photos du jour
    photos = [doc.to_dict() for doc in db.collection('photos').where('operateur_id', '==', str(user.id)).where('createdAt', '>=', today).stream()]
    # 3. Bon signé du jour
    bons = [doc.to_dict() for doc in db.collection('bons_attachement').where('operateur_id', '==', str(user.id)).where('createdAt', '>=', today).stream()]
    # 4. Alertes du jour
    alertes = [doc.to_dict() for doc in db.collection('alertes').where('operateur_id', '==', str(user.id)).where('createdAt', '>=', today).stream()]
    # Format du message
    msg = f"🗓️ Planning du jour pour {getattr(user, 'full_name', 'Utilisateur')}\n"
    if prise:
        msg += f"\n📌 Prise de poste : {prise.get('chantier', '—')} à {prise.get('heure', '—')}"
    else:
        msg += "\n📌 Prise de poste : —"
    msg += f"\n📷 Photos envoyées : {len(photos)}"
    msg += f"\n📄 Bon signé : {'Oui' if bons else 'Non'}"
    msg += f"\n🚨 Alertes : {len(alertes)}"
    await update.message.reply_text(msg)

async def scan_qr_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📦 Envoie une photo du QR code à scanner.")
    context.user_data['awaiting_qr'] = True

async def scan_qr_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('awaiting_qr'):
        return
    user = update.effective_user
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    img_bytes = await file.download_as_bytearray()
    img = Image.open(io.BytesIO(img_bytes))
    qr_results = decode_qr(img)
    if not qr_results:
        await update.message.reply_text("❌ Aucun QR code détecté. Réessaie avec une photo plus nette.")
        return
    qr_content = qr_results[0].data.decode('utf-8')
    # Enregistrement Firestore
    scan_doc = {
        'operateur_id': str(user.id),
        'nom': getattr(user, 'full_name', ''),
        'timestamp': datetime.datetime.now().isoformat(),
        'qr_content': qr_content,
        # 'chantier': ... (à compléter si dispo dans le contexte)
    }
    db.collection('scans_qr').add(scan_doc)
    await update.message.reply_text(f"✅ QR code scanné et enregistré : {qr_content}")
    context.user_data['awaiting_qr'] = False

async def prise_poste_and_scan_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Appelle le handler de prise de poste existant
    await start_prise(update, context)
    # Après la prise de poste, propose le scan QR
    await update.message.reply_text("Veux-tu scanner le QR code de la machine utilisée ?", reply_markup=ReplyKeyboardMarkup([["Oui", "Non"]], one_time_keyboard=True))
    context.user_data['awaiting_qr_after_prise'] = True

async def scan_qr_photo_linked(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('awaiting_qr_after_prise'):
        return
    user = update.effective_user
    # Récupérer la prise de poste du jour
    today = datetime.datetime.now().date().isoformat()
    prise = None
    prise_id = None
    chantier = None
    for doc in db.collection('prises_poste').where('operateur_id', '==', str(user.id)).where('heure', '>=', today).stream():
        prise = doc.to_dict()
        prise_id = doc.id
        chantier = prise.get('chantier', '')
        break
    if not prise_id:
        await update.message.reply_text("❗ Impossible de lier le scan à une prise de poste du jour.")
        context.user_data['awaiting_qr_after_prise'] = False
        return
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    img_bytes = await file.download_as_bytearray()
    img = Image.open(io.BytesIO(img_bytes))
    qr_results = decode_qr(img)
    if not qr_results:
        await update.message.reply_text("❌ Aucun QR code détecté. Réessaie avec une photo plus nette.")
        return
    qr_content = qr_results[0].data.decode('utf-8')
    scan_doc = {
        'operateur_id': str(user.id),
        'nom': getattr(user, 'full_name', ''),
        'timestamp': datetime.datetime.now().isoformat(),
        'qr_content': qr_content,
        'chantier': chantier,
        'prise_poste_id': prise_id
    }
    db.collection('scans_qr').add(scan_doc)
    await update.message.reply_text(f"✅ QR code scanné et lié à ta prise de poste du jour : {qr_content}")
    context.user_data['awaiting_qr_after_prise'] = False

async def declare_panne_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    types = [
        ["Fuite"],
        ["Bruit anormal"],
        ["Bras lent"],
        ["Problème électrique"],
        ["Autre"]
    ]
    await update.message.reply_text("Quel type de panne rencontres-tu ?", reply_markup=ReplyKeyboardMarkup(types, one_time_keyboard=True))
    context.user_data['declare_panne'] = {'step': 'type'}

async def declare_panne_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('declare_panne') or context.user_data['declare_panne'].get('step') != 'type':
        return
    context.user_data['declare_panne']['typeIncident'] = update.message.text
    context.user_data['declare_panne']['step'] = 'photo'
    await update.message.reply_text("Envoie une photo de la panne (ou tape 'Passer' si pas de photo)")

async def declare_panne_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('declare_panne') or context.user_data['declare_panne'].get('step') != 'photo':
        return
    photoURL = None
    if update.message.photo:
        # Upload photo comme pour handle_photo
        user = update.effective_user
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        local_dir = f"bot/photos/{user.id}"
        os.makedirs(local_dir, exist_ok=True)
        file_name = f"{user.id}_panne_{update.message.date.strftime('%Y%m%d_%H%M%S')}.jpg"
        file_path = f"{local_dir}/{file_name}"
        await file.download_to_drive(file_path)
        from PIL import Image
        try:
            with Image.open(file_path) as img:
                img.thumbnail((1024, 1024))
                img.save(file_path, "JPEG")
        except Exception as e:
            print(f"Erreur resize: {e}")
        from utils.firestore import upload_photo_to_storage
        storage_path = f"pannes/{user.id}/{file_name}"
        photoURL = upload_photo_to_storage(file_path, storage_path)
    context.user_data['declare_panne']['photoURL'] = photoURL
    context.user_data['declare_panne']['step'] = 'commentaire'
    await update.message.reply_text("Ajoute un commentaire (ou tape 'Passer')")

async def declare_panne_commentaire(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('declare_panne') or context.user_data['declare_panne'].get('step') != 'commentaire':
        return
    commentaire = update.message.text if update.message.text.lower() != 'passer' else ''
    context.user_data['declare_panne']['commentaire'] = commentaire
    # Récupérer le dernier scan QR du jour pour machineId
    from utils.firestore import db
    import datetime
    user = update.effective_user
    today = datetime.datetime.now().date().isoformat()
    machineId = None
    scans = list(db.collection('scans_qr').where('operateur_id', '==', str(user.id)).where('timestamp', '>=', today).stream())
    if scans:
        machineId = scans[-1].to_dict().get('qr_content')
    # Enregistrement Firestore
    issue_doc = {
        'operatorId': str(user.id),
        'date': datetime.datetime.now().isoformat(),
        'machineId': machineId,
        'typeIncident': context.user_data['declare_panne']['typeIncident'],
        'photoURL': context.user_data['declare_panne'].get('photoURL'),
        'commentaire': commentaire,
        'statut': 'non_resolu'
    }
    db.collection('maintenance_issues').add(issue_doc)
    await update.message.reply_text("✅ Incident enregistré et transmis à la maintenance.")
    context.user_data['declare_panne'] = None

def get_menu_handlers():
    return [
        CommandHandler("start", menu_principal),
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu),
        get_anomalie_handler(),
        MessageHandler(filters.Regex("^Partager ma position$"), start_prise),
        MessageHandler(filters.Regex("^Fin de poste$"), start_fin),
        MessageHandler(filters.Regex("^Checklist sécurité$"), start_checklist),
        MessageHandler(filters.Regex("^Mise hors voie urgente$"), hors_voie),
        MessageHandler(filters.Regex("^Portail d'accès SNCF$"), portail_sncf),
        MessageHandler(filters.Regex("^Fiches techniques$"), consulter_documents),
        MessageHandler(filters.Regex("^Historique$"), afficher_historique),
        MessageHandler(filters.Regex("^Paramètres$"), aide),
        MessageHandler(filters.Regex("^📦 Scanner QR code$"), scan_qr_start),
        MessageHandler(filters.PHOTO, scan_qr_photo),
        MessageHandler(filters.Regex("^Prise de poste$"), prise_poste_and_scan_qr),
        MessageHandler(filters.PHOTO, scan_qr_photo_linked),
        MessageHandler(filters.Regex("^🛠️ Déclarer une panne machine$"), declare_panne_start),
        MessageHandler(filters.TEXT & ~filters.COMMAND, declare_panne_type),
        MessageHandler(filters.PHOTO, declare_panne_photo),
        MessageHandler(filters.TEXT & ~filters.COMMAND, declare_panne_commentaire)
    ] 