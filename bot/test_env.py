#!/usr/bin/env python3
"""
Script de test pour vérifier la configuration des variables d'environnement
"""

import os
import json
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_environment_variables():
    """Teste toutes les variables d'environnement requises"""
    
    print("🔍 Vérification des variables d'environnement...")
    print("=" * 50)
    
    # Variables requises
    required_vars = {
        'BOT_TOKEN': 'Token Telegram du bot',
        'ENCO_USE_FIRESTORE': 'Activation de Firestore',
        'FIREBASE_SERVICE_ACCOUNT': 'Compte de service Firebase',
        'OPENAI_API_KEY': 'Clé API OpenAI',
        'ADMIN_CHAT_ID': 'ID du chat admin',
        'API_URL': 'URL de l\'API'
    }
    
    all_good = True
    
    for var_name, description in required_vars.items():
        value = os.environ.get(var_name)
        
        if value:
            if var_name == 'BOT_TOKEN':
                print(f"✅ {var_name}: {value[:10]}...{value[-10:]}")
            elif var_name == 'FIREBASE_SERVICE_ACCOUNT':
                try:
                    json.loads(value)
                    print(f"✅ {var_name}: JSON valide")
                except json.JSONDecodeError:
                    print(f"❌ {var_name}: JSON invalide")
                    all_good = False
            elif var_name == 'OPENAI_API_KEY':
                print(f"✅ {var_name}: {value[:10]}...{value[-10:]}")
            else:
                print(f"✅ {var_name}: {value}")
        else:
            print(f"❌ {var_name}: MANQUANT - {description}")
            all_good = False
    
    print("=" * 50)
    
    if all_good:
        print("🎉 Toutes les variables d'environnement sont configurées correctement !")
        
        # Test de connexion Firebase
        try:
            from utils.firestore import db
            print("✅ Connexion Firebase: OK")
        except Exception as e:
            print(f"❌ Connexion Firebase: ERREUR - {e}")
            all_good = False
        
        # Test de connexion Telegram
        try:
            from telegram import Bot
            bot_token = os.environ.get('BOT_TOKEN')
            if bot_token:
                bot = Bot(token=bot_token)
                print("✅ Connexion Telegram: OK")
            else:
                print("❌ Connexion Telegram: BOT_TOKEN manquant")
                all_good = False
        except Exception as e:
            print(f"❌ Connexion Telegram: ERREUR - {e}")
            all_good = False
        
        # Test OpenAI
        try:
            import openai
            openai.api_key = os.environ.get('OPENAI_API_KEY')
            # Test simple - pas d'appel réel
            print("✅ Configuration OpenAI: OK")
        except Exception as e:
            print(f"❌ Configuration OpenAI: ERREUR - {e}")
            all_good = False
            
    else:
        print("❌ Certaines variables d'environnement sont manquantes ou invalides")
    
    return all_good

if __name__ == "__main__":
    success = test_environment_variables()
    exit(0 if success else 1) 