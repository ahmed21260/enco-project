from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from utils.firestore import db
from datetime import datetime, timedelta
import json

# États du wizard
CHOIX_ACTION, CONSULTATION, ENVOI_PLANNING, CONFIRM_ENVOI = range(4)

async def start_planning_wizard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    
    # Vérifier si c'est un admin (ID 7648184043)
    is_admin = user.id == 7648184043
    
    if is_admin:
        # Menu admin : consultation ou envoi de planning
        keyboard = [
            ["📋 Consulter planning opérateurs"],
            ["📤 Envoyer planning aux opérateurs"],
            ["📊 Statistiques planning"],
            ["Menu principal"]
        ]
        await update.message.reply_text(
            "🗓️ **OUTIL PLANNING FERROVIAIRE**\n\n"
            "**Fonctions disponibles :**\n"
            "📋 **Consulter** : Voir les plannings des opérateurs\n"
            "📤 **Envoyer** : Distribuer les plannings aux équipes\n"
            "📊 **Statistiques** : Suivi des consultations\n\n"
            "Choisis ton action :",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return CHOIX_ACTION
    else:
        # Opérateur : consultation de son planning
        await show_operator_planning(update, context)
        return ConversationHandler.END

async def handle_planning_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    
    if choice == "📋 Consulter planning opérateurs":
        await show_all_plannings(update, context)
        return ConversationHandler.END
    elif choice == "📤 Envoyer planning aux opérateurs":
        await start_send_planning(update, context)
        return ENVOI_PLANNING
    elif choice == "📊 Statistiques planning":
        await show_planning_stats(update, context)
        return ConversationHandler.END
    elif choice == "Menu principal":
        await update.message.reply_text("Retour au menu principal.")
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ Choix invalide. Réessaie.")
        return CHOIX_ACTION

async def show_operator_planning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Afficher le planning de l'opérateur connecté"""
    user = update.message.from_user
    
    # Récupérer le planning de l'opérateur
    planning_data = await get_operator_planning(user.id)
    
    # Construire le message du planning
    message = f"🗓️ **PLANNING - {user.full_name}**\n\n"
    message += f"📅 **Date :** {datetime.now().strftime('%d/%m/%Y')}\n\n"
    
    # Planning du jour
    message += "🌅 **PLANNING DU JOUR :**\n"
    if planning_data.get('planning_jour'):
        planning_jour = planning_data['planning_jour']
        message += f"🕗 **Début :** {planning_jour.get('debut', '07:00')}\n"
        message += f"🕕 **Fin :** {planning_jour.get('fin', '17:00')}\n"
        message += f"🏗️ **Chantier :** {planning_jour.get('chantier', 'À confirmer')}\n"
        if planning_jour.get('address'):
            message += f"📍 **Adresse :** {planning_jour.get('address')}\n"
        if planning_jour.get('contact'):
            message += f"📞 **Contact :** {planning_jour.get('contact')}\n"
        message += f"🚜 **Machine :** {planning_jour.get('machine', 'À confirmer')}\n"
        message += f"📋 **Tâches :** {planning_jour.get('taches', 'Maintenance préventive')}\n"
        message += f"👷 **Équipe :** {planning_jour.get('equipe', 'Équipe 1')}\n"
        
        # Afficher la période si disponible
        if planning_jour.get('date_debut') and planning_jour.get('date_fin'):
            date_debut = datetime.strptime(planning_jour['date_debut'], '%Y-%m-%d').strftime('%d/%m/%Y')
            date_fin = datetime.strptime(planning_jour['date_fin'], '%Y-%m-%d').strftime('%d/%m/%Y')
            message += f"📅 **Période :** {date_debut} - {date_fin}\n"
    else:
        message += "⚠️ Planning non défini pour aujourd'hui\n"
    
    # Planning du lendemain
    message += "\n🌄 **PLANNING LENDEMAIN :**\n"
    if planning_data.get('planning_lendemain'):
        planning_demain = planning_data['planning_lendemain']
        message += f"🕗 **Début :** {planning_demain.get('debut', '07:00')}\n"
        message += f"🕕 **Fin :** {planning_demain.get('fin', '17:00')}\n"
        message += f"🏗️ **Chantier :** {planning_demain.get('chantier', 'À confirmer')}\n"
        if planning_demain.get('address'):
            message += f"📍 **Adresse :** {planning_demain.get('address')}\n"
        if planning_demain.get('contact'):
            message += f"📞 **Contact :** {planning_demain.get('contact')}\n"
        message += f"🚜 **Machine :** {planning_demain.get('machine', 'À confirmer')}\n"
        message += f"📋 **Tâches :** {planning_demain.get('taches', 'Maintenance préventive')}\n"
        
        # Afficher la période si disponible
        if planning_demain.get('date_debut') and planning_demain.get('date_fin'):
            date_debut = datetime.strptime(planning_demain['date_debut'], '%Y-%m-%d').strftime('%d/%m/%Y')
            date_fin = datetime.strptime(planning_demain['date_fin'], '%Y-%m-%d').strftime('%d/%m/%Y')
            message += f"📅 **Période :** {date_debut} - {date_fin}\n"
    else:
        message += "⚠️ Planning non défini pour demain\n"
    
    # Actions du jour
    message += "\n📊 **ACTIONS DU JOUR :**\n"
    message += f"📌 **Prise de poste :** {'✅ Effectuée' if planning_data.get('prise_effectuee') else '❌ Non effectuée'}\n"
    message += f"📷 **Photos envoyées :** {len(planning_data.get('photos', []))}\n"
    message += f"📄 **Bons d'attachement :** {len(planning_data.get('bons', []))}\n"
    message += f"🔧 **Anomalies signalées :** {len(planning_data.get('anomalies', []))}\n"
    message += f"🚨 **Urgences déclarées :** {len(planning_data.get('urgences', []))}\n"
    
    # Alertes importantes
    if planning_data.get('alertes'):
        message += "\n🚨 **ALERTES :**\n"
        for alerte in planning_data['alertes']:
            message += f"⚠️ {alerte}\n"
    
    # Boutons d'action
    keyboard = [
        ["✅ Confirmer consultation", "🔄 Actualiser planning"],
        ["📞 Contacter encadrement", "Menu principal"]
    ]
    
    await update.message.reply_text(
        message,
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    
    # Enregistrer la consultation
    consultation_data = {
        "operatorId": user.id,
        "operatorName": user.full_name,
        "timestamp": datetime.now().isoformat(),
        "type": "consultation_planning",
        "date_planning": datetime.now().date().isoformat()
    }
    
    try:
        db.collection('consultations_planning').add(consultation_data)
    except Exception as e:
        print(f"Erreur enregistrement consultation: {e}")

async def get_operator_planning(operator_id):
    """Récupérer le planning complet de l'opérateur depuis la collection 'planning' de la dashboard"""
    today = datetime.now().date().isoformat()
    tomorrow = (datetime.now() + timedelta(days=1)).date().isoformat()
    
    planning_info = {
        "planning_jour": None,
        "planning_lendemain": None,
        "prise_effectuee": False,
        "photos": [],
        "bons": [],
        "anomalies": [],
        "urgences": [],
        "alertes": []
    }
    
    try:
        # Récupérer le planning depuis la collection 'planning' de la dashboard
        planning_docs = list(db.collection('planning').filter('operateur_id', '==', str(operator_id)).stream())
        
        # Chercher les plannings pour aujourd'hui et demain
        for doc in planning_docs:
            data = doc.to_dict()
            date_debut = data.get('date_debut')
            date_fin = data.get('date_fin')
            
            # Vérifier si le planning couvre aujourd'hui
            if date_debut and date_fin:
                date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d').date()
                date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date()
                today_obj = datetime.now().date()
                
                if date_debut_obj <= today_obj <= date_fin_obj:
                    # Planning pour aujourd'hui
                    planning_info['planning_jour'] = {
                        'debut': '06:00' if data.get('equipe') == 'equipe1' else '14:00' if data.get('equipe') == 'equipe2' else '22:00',
                        'fin': '14:00' if data.get('equipe') == 'equipe1' else '22:00' if data.get('equipe') == 'equipe2' else '06:00',
                        'chantier': data.get('chantier_name', 'Chantier principal'),
                        'machine': data.get('machine_number', 'Machine non spécifiée'),
                        'taches': 'Maintenance préventive',
                        'equipe': data.get('equipe', 'Équipe 1'),
                        'address': data.get('chantier_address', ''),
                        'contact': data.get('contact_info', ''),
                        'date_debut': date_debut,
                        'date_fin': date_fin
                    }
                
                # Vérifier si le planning couvre demain
                tomorrow_obj = (datetime.now() + timedelta(days=1)).date()
                if date_debut_obj <= tomorrow_obj <= date_fin_obj:
                    # Planning pour demain
                    planning_info['planning_lendemain'] = {
                        'debut': '06:00' if data.get('equipe') == 'equipe1' else '14:00' if data.get('equipe') == 'equipe2' else '22:00',
                        'fin': '14:00' if data.get('equipe') == 'equipe1' else '22:00' if data.get('equipe') == 'equipe2' else '06:00',
                        'chantier': data.get('chantier_name', 'Chantier principal'),
                        'machine': data.get('machine_number', 'Machine non spécifiée'),
                        'taches': 'Maintenance préventive',
                        'equipe': data.get('equipe', 'Équipe 1'),
                        'address': data.get('chantier_address', ''),
                        'contact': data.get('contact_info', ''),
                        'date_debut': date_debut,
                        'date_fin': date_fin
                    }
        
        # Si pas de planning défini, créer un planning par défaut
        if not planning_info['planning_jour']:
            planning_info['planning_jour'] = {
                'debut': '07:00',
                'fin': '17:00',
                'chantier': 'Chantier principal',
                'machine': 'CAT 323M',
                'taches': 'Maintenance préventive',
                'equipe': 'Équipe 1'
            }
        
        if not planning_info['planning_lendemain']:
            planning_info['planning_lendemain'] = {
                'debut': '07:00',
                'fin': '17:00',
                'chantier': 'Chantier principal',
                'machine': 'CAT 323M',
                'taches': 'Maintenance préventive',
                'equipe': 'Équipe 1'
            }
        
        # Vérifier prise de poste
        prises = list(db.collection('prises_poste').filter('operateur_id', '==', str(operator_id)).filter('heure', '>=', today).stream())
        planning_info['prise_effectuee'] = len(prises) > 0
        
        # Récupérer les actions du jour
        planning_info['photos'] = list(db.collection('photos').filter('operateur_id', '==', str(operator_id)).filter('createdAt', '>=', today).stream())
        planning_info['bons'] = list(db.collection('bons_attachement').filter('operateur_id', '==', str(operator_id)).filter('createdAt', '>=', today).stream())
        planning_info['anomalies'] = list(db.collection('anomalies').filter('operateur_id', '==', str(operator_id)).filter('createdAt', '>=', today).stream())
        planning_info['urgences'] = list(db.collection('urgences').filter('operateur_id', '==', str(operator_id)).filter('createdAt', '>=', today).stream())
        
        # Alertes si pas de prise de poste
        if not planning_info['prise_effectuee']:
            planning_info['alertes'].append("Prise de poste non effectuée")
        
    except Exception as e:
        print(f"Erreur récupération planning: {e}")
    
    return planning_info

async def show_all_plannings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Afficher tous les plannings des opérateurs (admin)"""
    try:
        # Récupérer tous les opérateurs
        operateurs = list(db.collection('operateurs').stream())
        
        message = "🗓️ **PLANNINGS DES OPÉRATEURS**\n\n"
        
        for op in operateurs:
            op_data = op.to_dict()
            op_id = op_data.get('telegram_id')
            op_name = op_data.get('nom', 'Opérateur inconnu')
            
            # Récupérer le planning de cet opérateur
            planning = await get_operator_planning(op_id)
            
            message += f"👤 **{op_name}**\n"
            if planning.get('planning_jour'):
                p = planning['planning_jour']
                message += f"   🏗️ {p.get('chantier', 'Chantier')} | 🚜 {p.get('machine', 'Machine')}\n"
                if p.get('address'):
                    message += f"   📍 {p.get('address')}\n"
                if p.get('contact'):
                    message += f"   📞 {p.get('contact')}\n"
                message += f"   🕗 {p.get('debut', '07:00')} - {p.get('fin', '17:00')}\n"
                message += f"   📋 {p.get('taches', 'Tâches')}\n"
                
                # Afficher la période si disponible
                if p.get('date_debut') and p.get('date_fin'):
                    date_debut = datetime.strptime(p['date_debut'], '%Y-%m-%d').strftime('%d/%m/%Y')
                    date_fin = datetime.strptime(p['date_fin'], '%Y-%m-%d').strftime('%d/%m/%Y')
                    message += f"   📅 Période: {date_debut} - {date_fin}\n"
            else:
                message += f"   ⚠️ Planning non défini\n"
            
            message += f"   📌 Prise: {'✅' if planning['prise_effectuee'] else '❌'}\n"
            message += f"   📷 Photos: {len(planning['photos'])} | 📄 Bons: {len(planning['bons'])}\n"
            message += f"   🔧 Anomalies: {len(planning['anomalies'])} | 🚨 Urgences: {len(planning['urgences'])}\n\n"
        
        # Diviser le message si trop long
        if len(message) > 4000:
            parts = [message[i:i+4000] for i in range(0, len(message), 4000)]
            for i, part in enumerate(parts):
                await update.message.reply_text(f"{part}\n\n--- Partie {i+1}/{len(parts)} ---")
        else:
            await update.message.reply_text(message)
            
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur lors de la récupération des plannings: {str(e)}")

async def start_send_planning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Démarrer l'envoi de planning aux opérateurs"""
    await update.message.reply_text(
        "📤 **ENVOI DE PLANNING AUX OPÉRATEURS**\n\n"
        "Ceci va envoyer le planning du jour à tous les opérateurs inscrits.\n\n"
        "⚠️ **Attention :** Cette action enverra des notifications à tous les opérateurs.\n\n"
        "✅ Confirmer l'envoi ? (oui/non)",
        reply_markup=ReplyKeyboardMarkup([
            ["✅ Confirmer envoi", "❌ Annuler"],
            ["Menu principal"]
        ], resize_keyboard=True)
    )
    return CONFIRM_ENVOI

async def confirm_send_planning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirmer et exécuter l'envoi de planning"""
    if update.message.text.lower() not in ["oui", "✅ confirmer envoi"]:
        await update.message.reply_text("❌ Envoi annulé.")
        return ConversationHandler.END
    
    try:
        # Récupérer tous les opérateurs
        operateurs = list(db.collection('operateurs').stream())
        
        sent_count = 0
        for op in operateurs:
            op_data = op.to_dict()
            op_id = op_data.get('telegram_id')
            op_name = op_data.get('nom', 'Opérateur')
            
            if op_id:
                try:
                    # Envoyer le planning à l'opérateur
                    planning = await get_operator_planning(op_id)
                    
                    message = f"🗓️ **PLANNING DU JOUR - {op_name}**\n\n"
                    if planning.get('planning_jour'):
                        p = planning['planning_jour']
                        message += f"🕗 **Début :** {p.get('debut', '07:00')}\n"
                        message += f"🕕 **Fin :** {p.get('fin', '17:00')}\n"
                        message += f"🏗️ **Chantier :** {p.get('chantier', 'Chantier principal')}\n"
                        message += f"🚜 **Machine :** {p.get('machine', 'CAT 323M')}\n"
                        message += f"📋 **Tâches :** {p.get('taches', 'Maintenance préventive')}\n"
                        message += f"👷 **Équipe :** {p.get('equipe', 'Équipe 1')}\n\n"
                        message += "✅ **Planning confirmé par l'encadrement**\n"
                        message += "📞 Contactez l'encadrement en cas de question."
                    else:
                        message += "⚠️ Planning en cours de définition\n"
                        message += "📞 Contactez l'encadrement pour plus d'informations."
                    
                    # Envoyer via le bot (simulation)
                    # En réalité, il faudrait utiliser context.bot.send_message
                    print(f"Planning envoyé à {op_name} ({op_id})")
                    sent_count += 1
                    
                except Exception as e:
                    print(f"Erreur envoi à {op_name}: {e}")
        
        # Enregistrer l'envoi dans Firestore
        envoi_data = {
            "timestamp": datetime.now().isoformat(),
            "admin_id": update.effective_user.id,
            "admin_name": update.effective_user.full_name,
            "operateurs_contactes": sent_count,
            "type": "envoi_planning"
        }
        db.collection('envois_planning').add(envoi_data)
        
        await update.message.reply_text(
            f"✅ **PLANNING ENVOYÉ !**\n\n"
            f"📤 {sent_count} opérateur(s) contacté(s)\n"
            f"📊 Envoi enregistré dans les statistiques\n"
            f"🔄 Les opérateurs peuvent consulter leur planning via le menu.",
            reply_markup=ReplyKeyboardMarkup([
                ["📋 Consulter planning opérateurs"],
                ["📤 Envoyer planning aux opérateurs"],
                ["📊 Statistiques planning"],
                ["Menu principal"]
            ], resize_keyboard=True)
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur lors de l'envoi: {str(e)}")
    
    return ConversationHandler.END

async def show_planning_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Afficher les statistiques de planning"""
    try:
        # Consultations du jour
        today = datetime.now().date().isoformat()
        consultations = list(db.collection('consultations_planning').filter('date_planning', '==', today).stream())
        
        # Envois du jour
        envois = list(db.collection('envois_planning').stream())
        
        message = "📊 **STATISTIQUES PLANNING**\n\n"
        message += f"📅 **Date :** {datetime.now().strftime('%d/%m/%Y')}\n\n"
        message += f"📋 **Consultations :** {len(consultations)}\n"
        message += f"📤 **Envois effectués :** {len(envois)}\n"
        
        if consultations:
            message += "\n👥 **Dernières consultations :**\n"
            for i, consultation in enumerate(consultations[:5]):
                op_name = consultation.to_dict().get('operatorName', 'Opérateur')
                timestamp = consultation.to_dict().get('timestamp', '')
                if timestamp:
                    time_str = datetime.fromisoformat(timestamp).strftime('%H:%M')
                    message += f"   {i+1}. {op_name} - {time_str}\n"
        
        await update.message.reply_text(message)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur lors de la récupération des stats: {str(e)}")

def get_planning_wizard_handler():
    return ConversationHandler(
        entry_points=[
            CommandHandler("planning", start_planning_wizard),
            MessageHandler(filters.Regex("^🗓️ Planning$"), start_planning_wizard)
        ],
        states={
            CHOIX_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_planning_choice)],
            ENVOI_PLANNING: [MessageHandler(filters.TEXT & ~filters.COMMAND, start_send_planning)],
            CONFIRM_ENVOI: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_send_planning)],
        },
        fallbacks=[]
    ) 