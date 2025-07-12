#!/usr/bin/env python3
"""
Script de debug pour tester chaque étape du flux du bot
Usage: python debug_flow.py
"""

import os
import json
import logging
from datetime import datetime

# Configuration des logs détaillés
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug_flow.log'),
        logging.StreamHandler()
    ]
)

async def test_telegram_connection():
    """Test 1: Vérifier la connexion Telegram"""
    print("🔍 Test 1: Connexion Telegram")
    print("=" * 50)
    
    from telegram import Bot
    from telegram.error import TelegramError
    
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN non défini")
        return False
    
    try:
        bot = Bot(token=BOT_TOKEN)
        me = await bot.get_me()
        print(f"✅ Bot connecté: @{me.username} (ID: {me.id})")
        print(f"✅ Nom: {me.first_name}")
        return True
    except TelegramError as e:
        print(f"❌ Erreur connexion Telegram: {e}")
        return False

def test_webhook_status():
    """Test 2: Vérifier le statut du webhook"""
    print("\n🔍 Test 2: Statut du webhook")
    print("=" * 50)
    
    import requests
    
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN non défini")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
        response = requests.get(url)
        data = response.json()
        
        if data.get("ok"):
            info = data.get("result", {})
            print(f"✅ URL webhook: {info.get('url', 'Non configuré')}")
            print(f"✅ Updates en attente: {info.get('pending_update_count', 0)}")
            print(f"✅ Dernière erreur: {info.get('last_error_message', 'Aucune')}")
            return True
        else:
            print(f"❌ Erreur API: {data.get('description')}")
            return False
    except Exception as e:
        print(f"❌ Erreur requête webhook: {e}")
        return False

def test_firebase_connection():
    """Test 3: Vérifier la connexion Firebase"""
    print("\n🔍 Test 3: Connexion Firebase")
    print("=" * 50)
    
    try:
        from utils.firestore import db, USE_FIRESTORE
        print(f"✅ Firebase activé: {USE_FIRESTORE}")
        
        if USE_FIRESTORE and db:
            # Test simple de lecture
            test_doc = db.collection('test').document('debug').get()
            print("✅ Connexion Firestore OK")
            return True
        else:
            print("⚠️ Firebase désactivé - mode test local")
            return True
    except Exception as e:
        print(f"❌ Erreur Firebase: {e}")
        return False

def test_save_position_function():
    """Test 4: Tester la fonction save_position"""
    print("\n🔍 Test 4: Fonction save_position")
    print("=" * 50)
    
    try:
        from utils.firestore import save_position
        
        # Données de test
        test_data = {
            'operateur_id': 'test_123',
            'nom': 'Test User',
            'latitude': 48.8566,
            'longitude': 2.3522,
            'timestamp': datetime.now().isoformat(),
            'type': 'test'
        }
        
        print(f"📝 Test save_position avec: {test_data}")
        save_position(test_data)
        print("✅ save_position exécutée sans erreur")
        
        # Vérifier les fichiers locaux
        if os.path.exists('positions_temp.json'):
            print("✅ positions_temp.json créé/mis à jour")
        if os.path.exists('positions_log.jsonl'):
            print("✅ positions_log.jsonl créé/mis à jour")
        
        return True
    except Exception as e:
        print(f"❌ Erreur save_position: {e}")
        return False

async def test_telegram_message_sending():
    """Test 5: Tester l'envoi de message Telegram"""
    print("\n🔍 Test 5: Envoi de message Telegram")
    print("=" * 50)
    
    from telegram import Bot
    from telegram.error import TelegramError
    
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN non défini")
        return False
    
    try:
        bot = Bot(token=BOT_TOKEN)
        
        # Demander le chat_id pour le test
        print("💡 Pour tester l'envoi de message, tu dois:")
        print("1. Envoyer un message au bot sur Telegram")
        print("2. Récupérer ton chat_id avec /start")
        print("3. Entrer le chat_id ici pour le test")
        
        chat_id = input("Chat ID pour le test (ou appuie sur Entrée pour passer): ").strip()
        
        if chat_id:
            message = await bot.send_message(
                chat_id=chat_id,
                text="🧪 Test de debug - Message envoyé par le script de test"
            )
            print(f"✅ Message envoyé avec succès (ID: {message.message_id})")
            return True
        else:
            print("⚠️ Test d'envoi de message ignoré")
            return True
            
    except TelegramError as e:
        print(f"❌ Erreur envoi message: {e}")
        return False

def test_handlers_registration():
    """Test 6: Vérifier l'enregistrement des handlers"""
    print("\n🔍 Test 6: Enregistrement des handlers")
    print("=" * 50)
    
    try:
        from handlers.menu import get_menu_handlers
        from handlers.prise_de_poste import get_handler as prise_handler
        from handlers.fin_de_poste import get_handler as fin_handler
        
        menu_handlers = get_menu_handlers()
        print(f"✅ {len(menu_handlers)} handlers de menu enregistrés")
        
        prise_h = prise_handler()
        print(f"✅ Handler prise de poste: {type(prise_h)}")
        
        fin_h = fin_handler()
        print(f"✅ Handler fin de poste: {type(fin_h)}")
        
        return True
    except Exception as e:
        print(f"❌ Erreur handlers: {e}")
        return False

def generate_debug_report():
    """Générer un rapport de debug complet"""
    print("🔍 RAPPORT DE DEBUG COMPLET")
    print("=" * 60)
    
    tests = [
        ("Connexion Telegram", test_telegram_connection),
        ("Statut Webhook", test_webhook_status),
        ("Connexion Firebase", test_firebase_connection),
        ("Fonction save_position", test_save_position_function),
        ("Envoi message Telegram", test_telegram_message_sending),
        ("Enregistrement handlers", test_handlers_registration)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Erreur dans {test_name}: {e}")
            results[test_name] = False
    
    print("\n📊 RÉSUMÉ DES TESTS")
    print("=" * 30)
    for test_name, result in results.items():
        status = "✅ OK" if result else "❌ ÉCHEC"
        print(f"{test_name}: {status}")
    
    # Recommandations
    print("\n💡 RECOMMANDATIONS")
    print("=" * 20)
    
    if not results.get("Connexion Telegram"):
        print("- Vérifier BOT_TOKEN dans les variables d'environnement")
    
    if not results.get("Statut Webhook"):
        print("- Configurer le webhook avec setup_webhook.py")
    
    if not results.get("Connexion Firebase"):
        print("- Vérifier FIREBASE_SERVICE_ACCOUNT et ENCO_USE_FIRESTORE")
    
    if not results.get("Fonction save_position"):
        print("- Vérifier les permissions d'écriture des fichiers")
    
    if not results.get("Envoi message Telegram"):
        print("- Vérifier que le bot peut envoyer des messages")
    
    if not results.get("Enregistrement handlers"):
        print("- Vérifier l'import des modules handlers")

def main():
    print("🚀 SCRIPT DE DEBUG DU BOT ENCO")
    print("=" * 60)
    
    # Vérifier les variables d'environnement
    print("🔧 Variables d'environnement:")
    required_vars = ['BOT_TOKEN', 'ENCO_USE_FIRESTORE', 'FIREBASE_SERVICE_ACCOUNT']
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if 'TOKEN' in var or 'ACCOUNT' in var:
                print(f"  {var}: {'*' * 10}... (définie)")
            else:
                print(f"  {var}: {value}")
        else:
            print(f"  {var}: ❌ MANQUANTE")
    
    print()
    
    # Lancer tous les tests
    generate_debug_report()
    
    print("\n📝 Logs détaillés sauvegardés dans 'debug_flow.log'")

if __name__ == "__main__":
    main() 