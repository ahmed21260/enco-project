from telegram import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime

# 📌 MENUS PRINCIPAUX ------------------------------------------------------

MAIN_MENU = [
    ["📌 Prise de poste", "📷 Envoyer une photo"],
    ["📄 Bon d'attachement", "🛑 URGENCE / INCIDENT"],
    ["🔧 Déclarer une panne", "🗺️ Outils ferroviaires"],
    ["🤖 Assistant AI", "📋 Mon planning"]
]
MAIN_MENU_MARKUP = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)

AI_ASSISTANT_MENU = [["💬 Aide IA", "Retour au menu"]]
AI_ASSISTANT_MARKUP = ReplyKeyboardMarkup(AI_ASSISTANT_MENU, resize_keyboard=True)

YES_NO_MENU = [["Oui", "Non"], ["🤖 Aide IA"]]
YES_NO_MARKUP = ReplyKeyboardMarkup(YES_NO_MENU, resize_keyboard=True)


# 📋 CHECKLIST / PHOTOS ----------------------------------------------------

PHOTO_LABELS = [
    "Vue d'ensemble",
    "N° machine",
    "Pression hydraulique",
    "Attelage",
    "Outillage monté",
]

CHECKLIST_QUESTIONS = [
    "Niveau d'huile vérifié ?",
    "Pneus ou chenilles en bon état ?",
    "Feux et avertisseurs OK ?",
    "Document de bord présent ?",
]


# 🚜 MACHINES DISPONIBLES --------------------------------------------------

MACHINES_DISPO = [
    "CAT M323F",
    "Atlas 1604",
    "Mecalac 8MCR",
    "Rail-Route UNAC",
]

MACHINE_KEYBOARD = ReplyKeyboardMarkup(
    [[m] for m in MACHINES_DISPO] + [["Autre machine", "🤖 Aide IA"]],
    resize_keyboard=True, one_time_keyboard=True
)


# 🛠️ ANOMALIES ------------------------------------------------------------

ANOMALIES_HYDRAULIQUE = [
    "Fuite vérin",
    "Flexible abîmé",
    "Mauvaise pression",
    "Mouvement lent ou absent",
]

# Tu peux ajouter ANOMALIES_MOTEUR, ANOMALIES_ELECTRIQUE, etc.


# 📍 CLAVIER GPS -----------------------------------------------------------

def get_gps_keyboard():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("📍 Envoyer ma position", request_location=True)]],
        resize_keyboard=True, one_time_keyboard=True
    )


# 🔁 CLAVIER DE CONFIRMATION / VALIDATION ----------------------------------

CONFIRM_MENU = [["✅ Confirmer", "❌ Annuler"], ["🤖 Aide IA"]]
CONFIRM_MARKUP = ReplyKeyboardMarkup(CONFIRM_MENU, resize_keyboard=True, one_time_keyboard=True)


# ✅ CLAVIER POST-ANOMALIE --------------------------------------------------

POST_ANOMALIE_MENU = [
    ["Menu principal", "Déclarer une autre anomalie"],
    ["URGENCE SNCF", "Envoyer photo en cours de mission"]
]
POST_ANOMALIE_MARKUP = ReplyKeyboardMarkup(POST_ANOMALIE_MENU, resize_keyboard=True)


# 🕐 DATES & HEURES UTILITAIRES --------------------------------------------

def format_date() -> str:
    return datetime.now().strftime("%d/%m/%Y")

def format_heure() -> str:
    return datetime.now().strftime("%H:%M")


# 🧠 VALIDATEURS ------------------------------------------------------------

def validate_yes_no(text: str) -> bool:
    return text.lower() in ["oui", "non"]

def is_valid_photo_label(label: str) -> bool:
    return label in PHOTO_LABELS


# 🔮 HELPER POUR IA ---------------------------------------------------------

def build_ai_prompt(question: str, context: dict = None) -> str:
    base = (
        "Tu es une IA secrétaire, assistante logistique, administrative, technique et support pour un conducteur de machine rail-route. "
        "Tu aides à structurer les informations, répondre aux questions métier, donner des conseils sécurité, logistique, administratif, bricolage, ménage, etc. "
        "Sois proactive, claire, concise, et toujours orientée solution."
    )
    prompt = f"{base}\n\nQuestion de l'utilisateur : {question}"
    if context:
        prompt += f"\n\nContexte métier : {context}"
    return prompt


# 🏁 MENU PRINCIPAL (commande /start ou retour menu) -----------------------

async def menu_principal(update, context):
    await update.message.reply_text(
        "👋 Bienvenue sur ENCO Bot !\n\n"
        "Voici ce que tu peux faire :\n"
        "📌 Prise de poste : démarre ta journée\n"
        "🖼️ Envoyer une photo : signale un état ou une anomalie\n"
        "🛑 URGENCE / INCIDENT : déclare une urgence immédiate\n"
        "🔧 Déclarer une panne : signale une anomalie machine\n"
        "📄 Bon d'attachement : envoie un bon d'attachement\n"
        "🗺️ Outils ferroviaires : géoportail, règlements, procédures\n"
        "🗓️ Planning, etc.\n\n"
        "Utilise les boutons ci-dessous pour naviguer, ou tape /aide pour plus d'infos.",
        reply_markup=MAIN_MENU_MARKUP
    ) 