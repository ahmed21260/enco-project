from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from utils.firestore import db
from datetime import datetime
import math

# États du wizard rapport technique
TYPE_RAPPORT, DESCRIPTION, PHOTO, CONFIRM = range(4)

# Types de rapports techniques
RAPPORT_TYPES = [
    ["🔧 Rapport maintenance", "📊 Rapport performance"],
    ["🛠️ Rapport réparation", "📋 Rapport inspection"],
    ["⚙️ Rapport technique général", "Autre type de rapport"]
]

async def start_outils_ferroviaires(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    await update.message.reply_text(
        "🗺️ **OUTILS FERROVIAIRES ENCO**\n\n"
        "Sélectionne l'outil dont tu as besoin :",
        reply_markup=ReplyKeyboardMarkup([
            ["📍 Géoportail SNCF", "📘 Règlement sécurité"],
            ["📄 Procédures d'urgence", "📦 Fiche chantier"],
            ["📋 Rapport technique", "Menu principal"]
        ], resize_keyboard=True)
    )
    return ConversationHandler.END

async def handle_outils_ferroviaires(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    text = update.message.text
    
    if text == "📍 Géoportail SNCF":
        await start_geoportail(update, context)
    elif text == "📘 Règlement sécurité":
        await show_reglement_securite(update, context)
    elif text == "📄 Procédures d'urgence":
        await show_procedures_urgence(update, context)
    elif text == "📦 Fiche chantier":
        await show_fiche_chantier(update, context)
    elif text == "📋 Rapport technique":
        await start_rapport_wizard(update, context)
    elif text == "Menu principal":
        from handlers.menu import start
        await start(update, context)
    else:
        from handlers.menu import start
        await start(update, context)

async def start_geoportail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    await update.message.reply_text(
        "📍 **GÉOPORTAIL SNCF**\n\n"
        "Envoie ta position GPS pour trouver le portail SNCF le plus proche :",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📍 Envoyer ma position", request_location=True)]],
            one_time_keyboard=True, resize_keyboard=True
        )
    )

async def handle_geoportail_gps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    if not update.message.location:
        await update.message.reply_text("❗ Localisation obligatoire pour le géoportail.")
        return
    
    user = update.message.from_user
    if not user:
        await update.message.reply_text("❌ Erreur : utilisateur non trouvé.")
        return
    loc = update.message.location
    
    # Coordonnées des portails SNCF (exemple - à adapter selon les vrais portails)
    portails_sncf = [
        {"nom": "Portail SNCF Paris Nord", "lat": 48.8804, "lng": 2.3553, "url": "https://www.sncf.com/portail-paris-nord"},
        {"nom": "Portail SNCF Lyon Part-Dieu", "lat": 45.7600, "lng": 4.8600, "url": "https://www.sncf.com/portail-lyon"},
        {"nom": "Portail SNCF Marseille", "lat": 43.2965, "lng": 5.3698, "url": "https://www.sncf.com/portail-marseille"},
        {"nom": "Portail SNCF Lille", "lat": 50.6292, "lng": 3.0573, "url": "https://www.sncf.com/portail-lille"},
        {"nom": "Portail SNCF Nantes", "lat": 47.2184, "lng": -1.5536, "url": "https://www.sncf.com/portail-nantes"}
    ]
    
    # Trouver le portail le plus proche
    portail_plus_proche = None
    distance_min = float('inf')
    
    for portail in portails_sncf:
        distance = calculate_distance(loc.latitude, loc.longitude, portail["lat"], portail["lng"])
        if distance < distance_min:
            distance_min = distance
            portail_plus_proche = portail
    
    if portail_plus_proche:
        distance_km = round(distance_min, 1)
        await update.message.reply_text(
            f"📍 **PORTAL SNCF LE PLUS PROCHE**\n\n"
            f"🏢 **{portail_plus_proche['nom']}**\n"
            f"📏 Distance : {distance_km} km\n"
            f"🌐 Lien : {portail_plus_proche['url']}\n\n"
            f"🔗 Accès direct au portail SNCF",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🌐 Ouvrir Géoportail SNCF", url=portail_plus_proche['url'])]
            ])
        )
        
        # Enregistrer l'action dans Firestore
        db.collection('actions_geoportail').add({
            "operatorId": user.id,
            "operatorName": user.full_name,
            "timestamp": datetime.now().isoformat(),
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "portail_suggere": portail_plus_proche['nom'],
            "distance_km": distance_km,
            "type": "geoportail_sncf"
        })
    else:
        await update.message.reply_text("❌ Aucun portail SNCF trouvé à proximité.")

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculer la distance entre deux points GPS (formule de Haversine)"""
    R = 6371  # Rayon de la Terre en km
    
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

async def show_reglement_securite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    await update.message.reply_text(
        "📘 **RÈGLEMENT SÉCURITÉ ENCO/SNCF**\n\n"
        "🔒 **Règles de sécurité ferroviaire :**\n"
        "• Port obligatoire des EPI\n"
        "• Respect des zones de travail\n"
        "• Signalisation obligatoire\n"
        "• Procédures d'évacuation\n\n"
        "📄 **Documents disponibles :**\n"
        "• Règlement sécurité ENCO v2.1\n"
        "• Procédures SNCF\n"
        "• Fiches de poste\n\n"
        "🔗 Accès aux documents :",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📘 Règlement ENCO", url="https://enco-docs.com/reglement-securite")],
            [InlineKeyboardButton("🚨 Procédures SNCF", url="https://sncf.com/procedures-securite")],
            [InlineKeyboardButton("📋 Fiches de poste", url="https://enco-docs.com/fiches-poste")]
        ])
    )

async def show_procedures_urgence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    await update.message.reply_text(
        "📄 **PROCÉDURES D'URGENCE**\n\n"
        "🚨 **Procédures disponibles :**\n"
        "• Évacuation d'urgence\n"
        "• Choc électrique\n"
        "• Incendie\n"
        "• Accident de travail\n\n"
        "📱 **Numéros d'urgence :**\n"
        "🚨 SAMU : 15\n"
        "🚔 Police : 17\n"
        "🚨 Pompiers : 18\n"
        "📞 ENCO Assistance : 06 XX XX XX XX\n\n"
        "🔗 Accès aux procédures :",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📄 Procédure évacuation", url="https://enco-docs.com/evacuation")],
            [InlineKeyboardButton("⚡ Choc électrique", url="https://enco-docs.com/choc-electrique")],
            [InlineKeyboardButton("🔥 Incendie", url="https://enco-docs.com/incendie")]
        ])
    )

async def show_fiche_chantier(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    await update.message.reply_text(
        "📦 **FICHE CHANTIER**\n\n"
        "📋 **Dernière version disponible :**\n"
        "• Fiche chantier ENCO v3.2\n"
        "• Mise à jour : 15/01/2025\n"
        "• Validée par : Direction ENCO\n\n"
        "📄 **Contenu :**\n"
        "• Procédures de sécurité\n"
        "• Plans d'intervention\n"
        "• Contacts d'urgence\n"
        "• Matériel requis\n\n"
        "🔗 Télécharger la fiche :",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📦 Fiche chantier v3.2", url="https://enco-docs.com/fiche-chantier-v3.2")],
            [InlineKeyboardButton("📊 Plan d'intervention", url="https://enco-docs.com/plan-intervention")],
            [InlineKeyboardButton("📞 Contacts chantier", url="https://enco-docs.com/contacts-chantier")]
        ])
    )

# Wizard Rapport technique (intégré dans les outils)
async def start_rapport_wizard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    await update.message.reply_text(
        "📋 **RAPPORT TECHNIQUE**\n\n"
        "Sélectionne le type de rapport :",
        reply_markup=ReplyKeyboardMarkup(RAPPORT_TYPES, one_time_keyboard=True, resize_keyboard=True)
    )
    return TYPE_RAPPORT

async def receive_type_rapport(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    context.user_data['type_rapport'] = update.message.text
    
    await update.message.reply_text(
        f"📋 **{update.message.text}**\n\n"
        f"Décris le rapport technique en détail :\n"
        f"• Observations\n"
        f"• Actions réalisées\n"
        f"• Recommandations\n"
        f"• Problèmes identifiés\n\n"
        f"Tape 'skip' si tu veux passer cette étape."
    )
    return DESCRIPTION

async def receive_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    if update.message.text and update.message.text.lower() == 'skip':
        context.user_data['description'] = ''
    else:
        context.user_data['description'] = update.message.text or ''
    
    await update.message.reply_text(
        "📸 Envoie une photo pour illustrer le rapport (optionnel, tape 'skip' pour passer) :"
    )
    return PHOTO

async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    if update.message.text and update.message.text.lower() == 'skip':
        context.user_data['photo_file_id'] = None
    elif update.message.photo:
        context.user_data['photo_file_id'] = update.message.photo[-1].file_id
    else:
        await update.message.reply_text("❗ Envoie une photo ou tape 'skip' pour passer.")
        return PHOTO
    
    # Récapitulatif
    type_rapport = context.user_data.get('type_rapport', '')
    description = context.user_data.get('description', 'Aucune')
    photo = 'Oui' if context.user_data.get('photo_file_id') else 'Non'
    
    await update.message.reply_text(
        f"📋 **Récapitulatif Rapport Technique**\n\n"
        f"📋 Type : {type_rapport}\n"
        f"📝 Description : {description}\n"
        f"📸 Photo : {photo}\n\n"
        f"✅ Confirme l'envoi du rapport ? (oui/non)"
    )
    return CONFIRM

async def confirm_rapport(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    if not update.message.text:
        await update.message.reply_text("❌ Réponse invalide.")
        return CONFIRM
    if update.message.text.lower() != "oui":
        await update.message.reply_text("❌ Rapport annulé.")
        return ConversationHandler.END
    
    user = update.message.from_user
    if not user:
        await update.message.reply_text("❌ Erreur : utilisateur non trouvé.")
        return ConversationHandler.END
    
    # Données pour Firestore
    rapport_data = {
        "operatorId": user.id,
        "operatorName": user.full_name,
        "timestamp": datetime.now().isoformat(),
        "type_rapport": context.user_data.get('type_rapport', ''),
        "description": context.user_data.get('description', ''),
        "photo_file_id": context.user_data.get('photo_file_id'),
        "type": "rapport_technique",
        "handled": False
    }
    
    try:
        db.collection('rapports_techniques').add(rapport_data)
        await update.message.reply_text(
            "✅ **RAPPORT TECHNIQUE ENREGISTRÉ !**\n\n"
            f"📋 Le rapport a été transmis à l'encadrement.\n"
            f"📝 Description et photo enregistrées.\n"
            f"🔄 Tu seras contacté pour le suivi.",
            reply_markup=ReplyKeyboardMarkup([
                ["Menu principal", "Nouveau rapport technique"],
                ["Déclarer une panne", "URGENCE SNCF"]
            ], resize_keyboard=True)
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur lors de l'enregistrement : {str(e)}")
    
    return ConversationHandler.END

def get_outils_ferroviaires_handler():
    return ConversationHandler(
        entry_points=[
            CommandHandler("outils", start_outils_ferroviaires),
            MessageHandler(filters.Regex("^🗺️ Outils ferroviaires$"), start_outils_ferroviaires)
        ],
        states={
            TYPE_RAPPORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_type_rapport)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_description)],
            PHOTO: [MessageHandler(filters.PHOTO | filters.TEXT & ~filters.COMMAND, receive_photo)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_rapport)],
        },
        fallbacks=[]
    ) 