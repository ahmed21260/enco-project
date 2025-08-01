from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from handlers.prise_de_poste import start_prise_wizard
from handlers.fin_de_poste import start_fin_wizard
from handlers.checklist import start_checklist
from handlers.anomalie import start_anomalie_wizard
from handlers.bons_attachement import start_bon_wizard
from handlers.outils_ferroviaires import start_outils_ferroviaires, handle_outils_ferroviaires
from handlers.consult_docs import consulter_documents
from handlers.historique import afficher_historique
from handlers.urgence import start_urgence_wizard
from handlers.portail import portail_sncf
from handlers.planning import start_planning_wizard
from utils.firestore import db
import datetime
import io
from PIL import Image
# SUPPRESSION: from pyzbar.pyzbar import decode as decode_qr
import os
from handlers.photo import start_photo
import requests
from handlers.shared import menu_principal, MAIN_MENU, MAIN_MENU_MARKUP

# Suppression du MENU_KEYBOARD dupliqué - utilisation de celui de shared.py

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return
    
    # Vérifier si l'utilisateur est dans un ConversationHandler
    if hasattr(context, 'user_data') and context.user_data and context.user_data.get('_conversation_state'):
        # L'utilisateur est dans un ConversationHandler, ne pas interférer
        return
    
    text = update.message.text
    if text in ["📌 Prise de poste", "/prise"]:
        await start_prise_wizard(update, context)
    elif text == "Fin de poste / Bon papier" or text == "Fin de poste":
        await start_fin_wizard(update, context)
    elif text in ["🛑 URGENCE / INCIDENT", "/urgence"]:
        await start_urgence_wizard(update, context)
    elif text in ["🔧 Déclarer une panne", "/anomalie"]:
        await start_anomalie_wizard(update, context)
    elif text in ["✅ Remplir une checklist", "/checklist"]:
        await start_checklist(update, context)
    elif text in ["📄 Bon d'attachement", "/bon"]:
        await start_bon_wizard(update, context)
    elif text in ["🗺️ Outils ferroviaires", "/outils"]:
        await start_outils_ferroviaires(update, context)
    elif text in ["📷 Envoyer une photo", "/photo"]:
        await start_photo(update, context)
    elif text in ["🤖 Assistant AI", "/ai"]:
        from handlers.ai_assistant import start_ai_assistant
        await start_ai_assistant(update, context)
    elif text in ["🗓️ Planning", "/planning"]:
        await start_planning_wizard(update, context)
    elif text in ["📋 Mon planning", "/monplanning"]:
        # Envoi direct du planning de l'opérateur
        user = update.effective_user
        if user:
            from handlers.planning import get_operator_planning
            planning_data = await get_operator_planning(user.id)
            
            if planning_data.get('planning_jour'):
                message = f"🗓️ **PLANNING - {user.full_name}**\n\n"
                message += f"📅 **Date :** {datetime.datetime.now().strftime('%d/%m/%Y')}\n\n"
                
                planning_jour = planning_data['planning_jour']
                message += "🌅 **PLANNING DU JOUR :**\n"
                message += f"🕗 **Début :** {planning_jour.get('debut', '07:00')}\n"
                message += f"🕕 **Fin :** {planning_jour.get('fin', '17:00')}\n"
                message += f"🏗️ **Chantier :** {planning_jour.get('chantier', 'À confirmer')}\n"
                message += f"🚜 **Machine :** {planning_jour.get('machine', 'À confirmer')}\n"
                message += f"📋 **Tâches :** {planning_jour.get('taches', 'Maintenance préventive')}\n"
                message += f"👷 **Équipe :** {planning_jour.get('equipe', 'Équipe 1')}\n\n"
                
                message += "✅ **Planning confirmé par l'encadrement**\n"
                message += "📞 Contactez l'encadrement en cas de question."
                
                await update.message.reply_text(message)
            else:
                await update.message.reply_text(
                    "🗓️ **PLANNING**\n\n"
                    "⚠️ Aucun planning défini pour aujourd'hui.\n"
                    "📞 Contactez l'encadrement pour plus d'informations."
                )
    elif text in ["Menu principal", "/start"]:
        await start(update, context)
    else:
        # Pour tout texte non reconnu, retour à l'accueil immersif
        await start(update, context)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 *Bienvenue sur ENCO, l'outil des opérateurs ferroviaires !*\n\n"
        "Voici ce que tu peux faire :\n"
        "• 📌 *Prise de poste* (déclare ta présence et ta position)\n"
        "• 🛑 *Déclarer une urgence* (incident grave, sécurité)\n"
        "• 🛠️ *Déclarer une anomalie* (problème technique)\n"
        "• ✅ *Remplir une checklist* (sécurité, matériel)\n"
        "• 📄 *Consulter les documents* (règlement, procédures)\n\n"
        "_Tout est synchronisé en temps réel avec le dashboard ENCO._"
    )
    await update.message.reply_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=MAIN_MENU_MARKUP
    )

async def aide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *Aide ENCO*\n\n"
        "• *Prise de poste* : Démarre ta journée, envoie ta position.\n"
        "• *Envoyer une photo* : Pour signaler un problème ou un état machine.\n"
        "• *Urgence* : Déclare un incident immédiat, partage ta position.\n"
        "• *Bon signé* : Envoie un bon d'attachement lié à ta prise.\n"
        "• *Planning* : Récapitulatif de ta journée.\n"
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

# SUPPRESSION: async def scan_qr_start, scan_qr_photo, scan_qr_photo_linked, prise_poste_and_scan_qr

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

async def apitest_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api_url = os.getenv("API_URL", "https://believable-motivation-production.up.railway.app/api/positions")
    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            msg = f"✅ Connexion API OK\nNombre de positions: {len(data) if isinstance(data, list) else 'inconnu'}"
        else:
            msg = f"❌ Erreur API: {response.status_code} - {response.text[:100]}"
    except Exception as e:
        msg = f"❌ Exception lors de la requête API: {e}"
    await update.message.reply_text(msg)

def get_menu_handlers():
    return [
        MessageHandler(filters.Regex("^Fin de poste$"), start_fin_wizard),
        MessageHandler(filters.Regex("^Checklist sécurité$"), start_checklist),
        # MessageHandler(filters.Regex("^Mise hors voie urgente$"), hors_voie),
        MessageHandler(filters.Regex("^Portail d'accès SNCF$"), portail_sncf),
        MessageHandler(filters.Regex("^Fiches techniques$"), consulter_documents),
        MessageHandler(filters.Regex("^Historique$"), afficher_historique),
        MessageHandler(filters.Regex("^Paramètres$"), aide),
        MessageHandler(filters.Regex("^🛠️ Déclarer une panne machine$"), declare_panne_start),
        CommandHandler("apitest", apitest_handler)
    ] 