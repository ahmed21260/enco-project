#!/usr/bin/env python3
"""
Exemple de client pour tester le chatbot Firestore ENCO
Permet d'envoyer des messages et d'écouter les réponses
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# Ajouter le répertoire bot au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.firestore import db

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class FirestoreChatbotClient:
    """Client pour interagir avec le chatbot Firestore"""
    
    def __init__(self, user_id: str = "test_user"):
        self.user_id = user_id
        self.messages_ref = None
        
        if db:
            self.messages_ref = db.collection(f'users/{user_id}/messages')
        else:
            print("❌ Firestore non initialisé")
    
    def send_message(self, prompt: str) -> bool:
        """
        Envoie un message au chatbot
        
        Args:
            prompt: Le message à envoyer
            
        Returns:
            True si succès
        """
        if not self.messages_ref:
            print("❌ Messages ref non initialisé")
            return False
        
        try:
            # Ajouter le message
            message_ref = self.messages_ref.add({
                'prompt': prompt,
                'timestamp': datetime.now().isoformat(),
                'user_id': self.user_id
            })
            
            print(f"✅ Message envoyé: {prompt}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur envoi message: {e}")
            return False
    
    def listen_for_response(self, timeout: int = 30):
        """
        Écoute les réponses pour ce message
        
        Args:
            timeout: Timeout en secondes
        """
        if not self.messages_ref:
            print("❌ Messages ref non initialisé")
            return
        
        try:
            # Écouter les nouveaux messages
            def on_snapshot(doc_snapshot, changes, read_time):
                for change in changes:
                    if change.type.name == 'MODIFIED':
                        doc = change.document
                        data = doc.to_dict()
                        
                        if data.get('response'):
                            print(f"\n🤖 Réponse reçue:")
                            print(f"📝 Question: {data.get('prompt', 'N/A')}")
                            print(f"💬 Réponse: {data.get('response', 'N/A')}")
                            print(f"📊 Statut: {data.get('status', {}).get('state', 'N/A')}")
                            print("-" * 50)
            
            # Démarrer l'écouteur
            watch = self.messages_ref.on_snapshot(on_snapshot)
            print(f"🔄 Écoute des réponses pendant {timeout} secondes...")
            
            # Attendre
            asyncio.sleep(timeout)
            
            # Arrêter l'écouteur
            watch.unsubscribe()
            print("✅ Écoute terminée")
            
        except Exception as e:
            print(f"❌ Erreur écoute: {e}")
    
    def get_recent_messages(self, limit: int = 5):
        """
        Récupère les messages récents
        
        Args:
            limit: Nombre de messages à récupérer
        """
        if not self.messages_ref:
            print("❌ Messages ref non initialisé")
            return
        
        try:
            messages = self.messages_ref.order_by('timestamp', direction='DESCENDING').limit(limit).stream()
            
            print(f"\n📨 Messages récents ({limit} derniers):")
            print("-" * 50)
            
            for message in messages:
                data = message.to_dict()
                print(f"📝 Question: {data.get('prompt', 'N/A')}")
                print(f"🤖 Réponse: {data.get('response', 'En attente...')}")
                print(f"📊 Statut: {data.get('status', {}).get('state', 'N/A')}")
                print(f"⏰ Timestamp: {data.get('timestamp', 'N/A')}")
                print("-" * 30)
                
        except Exception as e:
            print(f"❌ Erreur récupération messages: {e}")

async def interactive_chat():
    """Chat interactif avec le chatbot"""
    print("🚂 Chatbot Firestore ENCO - Mode Interactif")
    print("=" * 50)
    
    user_id = input("Entrez votre ID utilisateur (ou appuyez sur Entrée pour 'test_user'): ").strip()
    if not user_id:
        user_id = "test_user"
    
    client = FirestoreChatbotClient(user_id)
    
    if not client.messages_ref:
        print("❌ Impossible d'initialiser le client")
        return
    
    print(f"✅ Connecté en tant que: {user_id}")
    print("💡 Tapez 'quit' pour quitter, 'history' pour voir l'historique")
    
    while True:
        try:
            prompt = input("\n💬 Votre message: ").strip()
            
            if not prompt:
                continue
            
            if prompt.lower() == 'quit':
                print("👋 Au revoir !")
                break
            
            if prompt.lower() == 'history':
                client.get_recent_messages()
                continue
            
            # Envoyer le message
            success = client.send_message(prompt)
            
            if success:
                print("⏳ Attente de la réponse...")
                # Attendre un peu pour la réponse
                await asyncio.sleep(5)
                
                # Vérifier la réponse
                client.get_recent_messages(1)
            
        except KeyboardInterrupt:
            print("\n👋 Au revoir !")
            break
        except Exception as e:
            print(f"❌ Erreur: {e}")

def test_simple():
    """Test simple d'envoi de message"""
    print("🧪 Test simple du chatbot")
    
    client = FirestoreChatbotClient("test_user_123")
    
    if not client.messages_ref:
        print("❌ Impossible d'initialiser le client")
        return
    
    # Message de test
    test_prompt = "Comment gérer une panne de signalisation ferroviaire ?"
    
    print(f"📝 Envoi du message: {test_prompt}")
    success = client.send_message(test_prompt)
    
    if success:
        print("✅ Message envoyé avec succès")
        print("⏳ Attente de 10 secondes pour la réponse...")
        
        # Attendre la réponse
        import time
        time.sleep(10)
        
        # Vérifier la réponse
        client.get_recent_messages(1)
    else:
        print("❌ Échec de l'envoi")

if __name__ == "__main__":
    print("🚂 ENCO Firestore Chatbot Client")
    print("1. Mode interactif")
    print("2. Test simple")
    
    choice = input("\nChoisissez un mode (1 ou 2): ").strip()
    
    if choice == "1":
        asyncio.run(interactive_chat())
    elif choice == "2":
        test_simple()
    else:
        print("❌ Choix invalide") 