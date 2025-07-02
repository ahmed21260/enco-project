from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from handlers.prise_de_poste import start_prise
from handlers.fin_de_poste import start_fin
from handlers.checklist import start_checklist
from handlers.anomalie import get_anomalie_handler
from handlers.consult_docs import consulter_documents
from handlers.historique import afficher_historique
from handlers.urgence import urgence, hors_voie
from handlers.portail import portail_sncf

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
        "• *Envoyer une photo* : Pour signaler un problème ou un état machine.\n"
        "• *Partager ma position* : Pour prise/fin de poste ou urgence.\n"
        "• *Checklist sécurité* : Pour vérifier les points vitaux avant de démarrer.\n"
        "• *Déclencher une urgence* : Pour alerter immédiatement l'encadrement.\n"
        "• *Mise hors voie urgente* : Procédure d'évacuation immédiate.\n"
        "• *Portail d'accès SNCF* : Trouver le portail le plus proche.\n"
        "• *Fiches techniques* : Accéder aux docs machines.\n"
        "• *Historique* : Voir vos actions passées.\n"
        "• *Paramètres* : Gérer vos infos personnelles.\n",
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

def get_menu_handlers():
    return [
        CommandHandler("start", start),
        CommandHandler("aide", aide),
        MessageHandler(filters.Regex("^Aide$"), aide),
        MessageHandler(filters.Regex("^Checklist sécurité$"), start_checklist),
        MessageHandler(filters.Regex("^Déclencher une urgence$"), urgence),
        MessageHandler(filters.Regex("^Mise hors voie urgente$"), hors_voie),
        MessageHandler(filters.Regex("^Portail d'accès SNCF$"), portail_sncf),
        MessageHandler(filters.Regex("^Fiches techniques$"), consulter_documents),
        MessageHandler(filters.Regex("^Historique$"), afficher_historique),
        MessageHandler(filters.Regex("^Paramètres$"), aide),
        get_anomalie_handler(),
        MessageHandler(filters.Regex("^Partager ma position$"), start_prise),
        MessageHandler(filters.Regex("^Fin de poste$"), start_fin),
        MessageHandler(filters.TEXT & ~filters.COMMAND, welcome_message)
    ] 