#!/usr/bin/env python3
"""
Script de test pour le chatbot Firestore ENCO
Démarre l'écouteur et permet de tester les messages
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# Ajouter le répertoire bot au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.enco_ai_assistant import ENCOAIAssistant
from utils.firestore import db

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def test_firestore_chatbot():
    """Test du chatbot Firestore"""
    
    print("🚂 Test du Chatbot Firestore ENCO")
    print("=" * 50)
    
    # Initialiser l'assistant
    assistant = ENCOAIAssistant()
    
    if not assistant.client:
        print("❌ Assistant AI non disponible - vérifiez OPENAI_API_KEY")
        return
    
    if not db:
        print("❌ Firestore non initialisé - vérifiez la configuration Firebase")
        return
    
    print("✅ Assistant AI et Firestore initialisés")
    
    # Démarrer l'écouteur
    print("🔄 Démarrage de l'écouteur Firestore...")
    watch = assistant.start_firestore_listener()
    
    if not watch:
        print("❌ Impossible de démarrer l'écouteur")
        return
    
    print("✅ Écouteur démarré - en attente de messages...")
    
    # Test avec un message
    test_uid = "test_user_123"
    test_prompt = "J'ai une anomalie sur la signalisation à la gare centrale, que faire ?"
    
    print(f"\n📝 Ajout d'un message de test...")
    success = assistant.add_test_message(test_uid, test_prompt)
    
    if success:
        print(f"✅ Message de test ajouté: {test_prompt}")
        print("⏳ Attente de la réponse...")
    else:
        print("❌ Erreur lors de l'ajout du message de test")
    
    # Attendre un peu pour voir la réponse
    print("\n⏰ Attente de 10 secondes pour voir la réponse...")
    await asyncio.sleep(10)
    
    # Vérifier la réponse
    try:
        messages_ref = db.collection(f'users/{test_uid}/messages')
        messages = messages_ref.order_by('timestamp', direction='DESCENDING').limit(1).stream()
        
        for message in messages:
            data = message.to_dict()
            print(f"\n📨 Message original: {data.get('prompt', 'N/A')}")
            print(f"🤖 Réponse IA: {data.get('response', 'En cours...')}")
            print(f"📊 Statut: {data.get('status', {}).get('state', 'N/A')}")
            break
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
    
    print("\n🔄 L'écouteur continue de fonctionner...")
    print("Appuyez sur Ctrl+C pour arrêter")
    
    # Garder l'écouteur actif
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Arrêt de l'écouteur...")
        if watch:
            watch.unsubscribe()
        print("✅ Écouteur arrêté")

def test_simple_response():
    """Test simple de génération de réponse"""
    print("\n🧪 Test simple de génération de réponse...")
    
    assistant = ENCOAIAssistant()
    
    if not assistant.client:
        print("❌ Assistant AI non disponible")
        return
    
    # Test de réponse
    test_prompt = "Comment gérer une panne de signalisation ?"
    
    async def test():
        response = await assistant.generate_railway_response(test_prompt)
        print(f"📝 Question: {test_prompt}")
        print(f"🤖 Réponse: {response}")
    
    asyncio.run(test())

if __name__ == "__main__":
    print("🚂 ENCO Firestore Chatbot Test")
    print("1. Test complet avec écouteur")
    print("2. Test simple de génération")
    
    choice = input("\nChoisissez un test (1 ou 2): ").strip()
    
    if choice == "1":
        asyncio.run(test_firestore_chatbot())
    elif choice == "2":
        test_simple_response()
    else:
        print("❌ Choix invalide") 