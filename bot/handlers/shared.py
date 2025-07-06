from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime

# 🧭 Menus et claviers communs
MENU_KEYBOARD = [
    ["Prise de poste", "Fin de poste"],
    ["Checklist", "Anomalie"]
]
MENU_MARKUP = ReplyKeyboardMarkup(MENU_KEYBOARD, resize_keyboard=True)

YES_NO_KEYBOARD = [["Oui", "Non"]]
YES_NO_MARKUP = ReplyKeyboardMarkup(YES_NO_KEYBOARD, resize_keyboard=True)

AI_ASSISTANT_KEYBOARD = [["💬 Aide IA", "Retour au menu"]]
AI_ASSISTANT_MARKUP = ReplyKeyboardMarkup(AI_ASSISTANT_KEYBOARD, resize_keyboard=True)

# 📌 Constantes métier partagées
PHOTO_LABELS = [
    "Vue d’ensemble",
    "N° machine",
    "Pression hydraulique",
    "Attelage",
    "Outillage monté",
]

CHECKLIST_QUESTIONS = [
    "Niveau d’huile vérifié ?",
    "Pneus ou chenilles en bon état ?",
    "Feux et avertisseurs OK ?",
    "Document de bord présent ?",
]

ANOMALIES_HYDRAULIQUE = [
    "Fuite vérin",
    "Flexible abîmé",
    "Mauvaise pression",
    "Mouvement lent ou absent",
]

MACHINES_DISPO = [
    "CAT M323F",
    "Atlas 1604",
    "Mecalac 8MCR",
    "Rail-Route UNAC",
]

# 🧼 Helpers utilitaires

def format_date():
    return datetime.now().strftime("%d/%m/%Y")

def format_heure():
    return datetime.now().strftime("%H:%M")

def validate_yes_no(text: str) -> bool:
    return text.lower() in ["oui", "non"]

def is_valid_photo_label(label: str) -> bool:
    return label in PHOTO_LABELS

# 🧠 Helpers IA (exemple)
def build_ai_prompt(question: str, context: dict = None) -> str:
    prompt = f"Réponds en tant qu’assistant de sécurité ferroviaire :\n\nQuestion : {question}"
    if context:
        prompt += f"\n\nContexte : {context}"
    return prompt 

async def menu_principal(update, context):
    reply_markup = ReplyKeyboardMarkup(MENU_KEYBOARD, resize_keyboard=True)
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
        reply_markup=reply_markup
    ) 