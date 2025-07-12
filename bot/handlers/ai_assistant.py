#!/usr/bin/env python3
"""
Handler pour l'assistant AI ENCO
Intégré dans le bot Telegram pour aider les opérateurs
"""

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from services.enco_ai_assistant import (
    ai_assistant,
    analyze_similar_anomalies,
    suggest_resolution,
    get_operator_help
)
import logging

# États de conversation
WAITING_QUESTION = 1
WAITING_ANOMALIE_DESCRIPTION = 2

async def start_ai_assistant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Démarre l'assistant AI"""
    if not ai_assistant.client:
        await update.message.reply_text(
            "❌ Assistant AI temporairement indisponible.\n"
            "Contactez l'administrateur pour plus d'informations."
        )
        return ConversationHandler.END
    
    keyboard = [
        ["🔍 Analyser une anomalie", "💡 Demander de l'aide"],
        ["📊 Anomalies similaires", "🔙 Retour au menu"]
    ]
    
    await update.message.reply_text(
        "🤖 **Assistant AI ENCO**\n\n"
        "Je peux vous aider avec :\n"
        "• 🔍 Analyser et catégoriser vos anomalies\n"
        "• 💡 Répondre à vos questions techniques\n"
        "• 📊 Trouver des anomalies similaires\n"
        "• 🎯 Suggérer des résolutions\n\n"
        "Que souhaitez-vous faire ?",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        parse_mode="Markdown"
    )
    
    return WAITING_QUESTION

async def handle_ai_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère le choix de l'utilisateur dans l'assistant AI"""
    choice = update.message.text
    
    if choice == "🔍 Analyser une anomalie":
        await update.message.reply_text(
            "📝 **Analyse d'anomalie**\n\n"
            "Décrivez l'anomalie que vous observez.\n"
            "Je vais :\n"
            "• Catégoriser automatiquement\n"
            "• Évaluer la priorité\n"
            "• Suggérer une résolution\n\n"
            "Décrivez l'anomalie :",
            reply_markup=ReplyKeyboardMarkup([["🔙 Retour"]], resize_keyboard=True),
            parse_mode="Markdown"
        )
        return WAITING_ANOMALIE_DESCRIPTION
    
    elif choice == "💡 Demander de l'aide":
        await update.message.reply_text(
            "💡 **Assistant technique**\n\n"
            "Posez votre question technique.\n"
            "Exemples :\n"
            "• Comment vérifier les freins ?\n"
            "• Procédure en cas de panne\n"
            "• Normes de sécurité\n\n"
            "Votre question :",
            reply_markup=ReplyKeyboardMarkup([["🔙 Retour"]], resize_keyboard=True),
            parse_mode="Markdown"
        )
        return WAITING_QUESTION
    
    elif choice == "📊 Anomalies similaires":
        await update.message.reply_text(
            "📊 **Recherche d'anomalies similaires**\n\n"
            "Décrivez l'anomalie pour trouver des cas similaires dans l'historique.\n"
            "Cela peut aider à identifier des patterns ou des solutions déjà testées.\n\n"
            "Description de l'anomalie :",
            reply_markup=ReplyKeyboardMarkup([["🔙 Retour"]], resize_keyboard=True),
            parse_mode="Markdown"
        )
        return WAITING_ANOMALIE_DESCRIPTION
    
    elif choice == "🔙 Retour au menu":
        from handlers.menu import start
        return await start(update, context)
    
    else:
        await update.message.reply_text(
            "❓ Je n'ai pas compris votre choix.\n"
            "Utilisez les boutons ci-dessous :"
        )
        return WAITING_QUESTION

async def analyze_anomalie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Analyse une anomalie avec l'IA"""
    description = update.message.text
    
    if description == "🔙 Retour":
        return await start_ai_assistant(update, context)
    
    try:
        # Catégorisation
        category = ai_assistant.categorize_anomalie(description)
        
        # Évaluation priorité
        priority_info = ai_assistant.prioritize_urgence(description)
        
        # Suggestion de résolution
        resolution = suggest_resolution(description)
        
        # Construction de la réponse
        response = f"🔍 **ANALYSE D'ANOMALIE**\n\n"
        response += f"📝 **Description :** {description}\n\n"
        
        if category:
            response += f"🏷️ **Catégorie :** {category}\n"
        
        response += f"⚠️ **Priorité :** {priority_info['priority'].upper()}\n"
        response += f"📋 **Raison :** {priority_info['reason']}\n"
        
        if priority_info.get('immediate_action'):
            response += "🚨 **ACTION IMMÉDIATE REQUISE**\n"
        
        if resolution:
            response += f"\n💡 **Suggestion de résolution :**\n{resolution}\n"
        
        # Recherche d'anomalies similaires
        similar = analyze_similar_anomalies(description)
        if similar:
            response += f"\n📊 **Anomalies similaires trouvées :** {len(similar)}\n"
            for i, anomaly in enumerate(similar[:3], 1):
                response += f"{i}. {anomaly['description'][:50]}... (Score: {anomaly['similarity_score']:.2f})\n"
        
        keyboard = [
            ["🔍 Analyser une autre anomalie", "💡 Demander de l'aide"],
            ["📊 Anomalies similaires", "🔙 Retour au menu"]
        ]
        
        await update.message.reply_text(
            response,
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
            parse_mode="Markdown"
        )
        
        return WAITING_QUESTION
        
    except Exception as e:
        logging.error(f"❌ Erreur analyse anomalie: {e}")
        await update.message.reply_text(
            "❌ Erreur lors de l'analyse.\n"
            "Veuillez réessayer ou contacter l'administrateur."
        )
        return WAITING_QUESTION

async def handle_operator_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Répond aux questions techniques des opérateurs"""
    question = update.message.text
    
    if question == "🔙 Retour":
        return await start_ai_assistant(update, context)
    
    try:
        # Contexte de l'opérateur (peut être enrichi plus tard)
        operator_context = {
            "user_id": update.message.from_user.id,
            "username": update.message.from_user.username
        }
        
        # Obtenir l'aide
        help_response = get_operator_help(question, operator_context)
        
        if help_response:
            response = f"💡 **ASSISTANCE TECHNIQUE**\n\n"
            response += f"❓ **Question :** {question}\n\n"
            response += f"🤖 **Réponse :** {help_response}\n\n"
            response += "💡 *Cette réponse est générée par IA. Vérifiez toujours les procédures officielles.*"
        else:
            response = "❌ Désolé, je n'ai pas pu générer une réponse.\n"
            response += "Veuillez reformuler votre question ou contacter votre superviseur."
        
        keyboard = [
            ["🔍 Analyser une anomalie", "💡 Demander de l'aide"],
            ["📊 Anomalies similaires", "🔙 Retour au menu"]
        ]
        
        await update.message.reply_text(
            response,
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
            parse_mode="Markdown"
        )
        
        return WAITING_QUESTION
        
    except Exception as e:
        logging.error(f"❌ Erreur assistance opérateur: {e}")
        await update.message.reply_text(
            "❌ Erreur lors de l'assistance.\n"
            "Veuillez réessayer ou contacter l'administrateur."
        )
        return WAITING_QUESTION

async def cancel_ai_assistant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Annule l'assistant AI"""
    from handlers.menu import start
    await update.message.reply_text(
        "🔙 Retour au menu principal",
        reply_markup=ReplyKeyboardRemove()
    )
    return await start(update, context)

def get_ai_assistant_handler():
    """Retourne le handler pour l'assistant AI"""
    return ConversationHandler(
        entry_points=[
            CommandHandler('ai', start_ai_assistant),
            MessageHandler(filters.Regex("^🤖 Assistant AI$"), start_ai_assistant)
        ],
        states={
            WAITING_QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ai_choice)
            ],
            WAITING_ANOMALIE_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, analyze_anomalie)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel_ai_assistant)]
    ) 