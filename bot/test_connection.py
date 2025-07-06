#!/usr/bin/env python3
"""
Script de test pour diagnostiquer les problèmes de connectivité
"""

import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Bot
import firebase_admin
from firebase_admin import credentials, firestore
import json

# Configuration logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def test_telegram():
    """Test de connectivité Telegram"""
    print("🔍 Test de connectivité Telegram...")
    
    BOT_TOKEN = os.environ.get("BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN")
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN non défini")
        return False
    
    try:
        bot = Bot(token=BOT_TOKEN)
        me = await bot.get_me()
        print(f"✅ Bot connecté: {me.first_name} (@{me.username})")
        return True
    except Exception as e:
        print(f"❌ Erreur Telegram: {e}")
        return False

def test_firebase():
    """Test de connectivité Firebase"""
    print("🔍 Test de connectivité Firebase...")
    
    try:
        if os.getenv('ENCO_USE_FIRESTORE', '0') == '1':
            if os.getenv("FIREBASE_SERVICE_ACCOUNT"):
                cred = credentials.Certificate(json.loads(os.environ["FIREBASE_SERVICE_ACCOUNT"]))
            else:
                cred_file = "firebase_credentials.json" if os.path.exists("firebase_credentials.json") else "serviceAccountKey.json"
                cred = credentials.Certificate(cred_file)

            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred, {
                    'storageBucket': os.getenv("FIREBASE_STORAGE_BUCKET", "enco-prestarail.appspot.com")
                })
            
            db = firestore.client()
            
            # Test d'écriture
            test_doc = db.collection('test').document('connection_test')
            test_doc.set({
                'timestamp': '2025-01-01T00:00:00',
                'test': True
            })
            
            # Test de lecture
            doc = test_doc.get()
            if doc.exists:
                print("✅ Firebase connecté et fonctionnel")
                # Nettoyer le test
                test_doc.delete()
                return True
            else:
                print("❌ Erreur lecture Firebase")
                return False
        else:
            print("⚠️ Firebase désactivé (ENCO_USE_FIRESTORE != 1)")
            return False
    except Exception as e:
        print(f"❌ Erreur Firebase: {e}")
        return False

def test_openai():
    """Test de connectivité OpenAI"""
    print("🔍 Test de connectivité OpenAI...")
    
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY non définie")
        return False
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Test simple
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Test de connexion"}],
            max_tokens=10
        )
        
        if response.choices[0].message.content:
            print("✅ OpenAI connecté et fonctionnel")
            return True
        else:
            print("❌ Réponse OpenAI vide")
            return False
    except Exception as e:
        print(f"❌ Erreur OpenAI: {e}")
        return False

def test_env_vars():
    """Test des variables d'environnement"""
    print("🔍 Test des variables d'environnement...")
    
    required_vars = [
        "BOT_TOKEN",
        "TELEGRAM_TOKEN", 
        "OPENAI_API_KEY",
        "ENCO_USE_FIRESTORE"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Variables manquantes: {missing_vars}")
        return False
    else:
        print("✅ Toutes les variables d'environnement sont définies")
        return True

def test_logging():
    """Test du système de logging"""
    print("🔍 Test du système de logging...")
    
    try:
        logger.info("Test de logging INFO")
        logger.warning("Test de logging WARNING")
        logger.error("Test de logging ERROR")
        print("✅ Logging fonctionnel")
        return True
    except Exception as e:
        print(f"❌ Erreur logging: {e}")
        return False

async def main():
    """Test complet du système"""
    print("🚀 Démarrage des tests de connectivité...")
    print("=" * 50)
    
    # Charger les variables d'environnement
    load_dotenv()
    
    # Tests
    tests = [
        ("Variables d'environnement", test_env_vars),
        ("Logging", test_logging),
        ("Firebase", test_firebase),
        ("OpenAI", test_openai),
        ("Telegram", test_telegram),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ Erreur lors du test {test_name}: {e}")
            results[test_name] = False
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 50)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"\n🎯 Résultat: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Tous les tests sont passés ! Le système est prêt.")
    else:
        print("⚠️ Certains tests ont échoué. Vérifiez la configuration.")
        
        # Suggestions de diagnostic
        if not results.get("Variables d'environnement"):
            print("\n💡 SUGGESTIONS:")
            print("- Vérifiez que le fichier .env existe et contient les bonnes variables")
            print("- En production (Railway), vérifiez les variables d'environnement dans le dashboard")
        
        if not results.get("Firebase"):
            print("\n💡 SUGGESTIONS:")
            print("- Vérifiez ***REMOVED***")
            print("- Vérifiez FIREBASE_SERVICE_ACCOUNT ou serviceAccountKey.json")
        
        if not results.get("Telegram"):
            print("\n💡 SUGGESTIONS:")
            print("- Vérifiez BOT_TOKEN ou TELEGRAM_TOKEN")
            print("- Vérifiez que le token est valide avec @BotFather")
        
        if not results.get("OpenAI"):
            print("\n💡 SUGGESTIONS:")
            print("- Vérifiez OPENAI_API_KEY")
            print("- Vérifiez que la clé API est valide et a des crédits")

if __name__ == "__main__":
    asyncio.run(main()) 