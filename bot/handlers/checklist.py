from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from utils.firestore import save_checklist

Q1, Q2, Q3 = range(3)

async def start_checklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['checklist'] = {}
    await update.message.reply_text(
        "✅ *Checklist sécurité ENCO*\n\n1. Freinage OK ? (oui/non)",
        parse_mode="Markdown"
    )
    return Q1

async def q1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['checklist']['freinage'] = update.message.text
    await update.message.reply_text("2. Signalisation OK ? (oui/non)")
    return Q2

async def q2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['checklist']['signalisation'] = update.message.text
    await update.message.reply_text("3. Accessoires montés OK ? (oui/non)")
    return Q3

async def q3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['checklist']['accessoires'] = update.message.text
    save_checklist(update.message.from_user.id, context.user_data['checklist'])
    await update.message.reply_text(
        "✅ Checklist enregistrée !\n\n"
        f"- Freinage : {context.user_data['checklist']['freinage']}\n"
        f"- Signalisation : {context.user_data['checklist']['signalisation']}\n"
        f"- Accessoires : {context.user_data['checklist']['accessoires']}\n"
        "Merci pour votre vigilance !"
    )
    return ConversationHandler.END

def get_checklist_handler():
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^Checklist sécurité$"), start_checklist),
            MessageHandler(filters.Regex("^✅ Remplir une checklist$"), start_checklist),
            CommandHandler("checklist", start_checklist)
        ],
        states={
            Q1: [MessageHandler(filters.TEXT & ~filters.COMMAND, q1)],
            Q2: [MessageHandler(filters.TEXT & ~filters.COMMAND, q2)],
            Q3: [MessageHandler(filters.TEXT & ~filters.COMMAND, q3)],
        },
        fallbacks=[]
    ) 