#!/usr/bin/env python3
"""
Script pour configurer et vérifier le webhook Telegram
Usage: python setup_webhook.py
"""

import os
import requests
import json

# Configuration
BOT_TOKEN = os.environ.get("BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN")
WEBHOOK_URL = "https://enco-prestarail-bot.railway.app/webhook"

def get_webhook_info():
    """Récupère les informations actuelles du webhook"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        if data.get("ok"):
            info = data.get("result", {})
            print("🔍 Informations actuelles du webhook:")
            print(f"   URL: {info.get('url', 'Non configuré')}")
            print(f"   Has custom certificate: {info.get('has_custom_certificate', False)}")
            print(f"   Pending update count: {info.get('pending_update_count', 0)}")
            print(f"   Last error date: {info.get('last_error_date', 'Aucune')}")
            print(f"   Last error message: {info.get('last_error_message', 'Aucune')}")
            print(f"   Max connections: {info.get('max_connections', 'Non défini')}")
            print(f"   Allowed updates: {info.get('allowed_updates', 'Tous')}")
            return info
        else:
            print(f"❌ Erreur API Telegram: {data.get('description', 'Erreur inconnue')}")
            return None
    else:
        print(f"❌ Erreur HTTP: {response.status_code}")
        return None

def set_webhook():
    """Configure le webhook Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    data = {
        "url": WEBHOOK_URL,
        "allowed_updates": ["message", "callback_query", "photo", "voice"],
        "max_connections": 40
    }
    
    print(f"🔗 Configuration du webhook vers: {WEBHOOK_URL}")
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("ok"):
            print("✅ Webhook configuré avec succès!")
            print(f"   Résultat: {result.get('result', True)}")
            print(f"   Description: {result.get('description', 'OK')}")
            return True
        else:
            print(f"❌ Erreur lors de la configuration: {result.get('description', 'Erreur inconnue')}")
            return False
    else:
        print(f"❌ Erreur HTTP: {response.status_code}")
        print(f"   Réponse: {response.text}")
        return False

def delete_webhook():
    """Supprime le webhook Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
    response = requests.post(url)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("ok"):
            print("🗑️ Webhook supprimé avec succès!")
            return True
        else:
            print(f"❌ Erreur lors de la suppression: {result.get('description', 'Erreur inconnue')}")
            return False
    else:
        print(f"❌ Erreur HTTP: {response.status_code}")
        return False

def test_webhook():
    """Teste si le webhook répond correctement"""
    print(f"🧪 Test de la réponse du webhook: {WEBHOOK_URL}")
    
    # Test avec un payload invalide (doit retourner 400)
    invalid_payload = {"test": "invalid"}
    response = requests.post(WEBHOOK_URL, json=invalid_payload)
    print(f"   Test payload invalide: {response.status_code} - {response.text}")
    
    # Test avec un payload valide (doit retourner 200)
    valid_payload = {
        "update_id": 123456789,
        "message": {
            "message_id": 1,
            "from": {"id": 123456, "username": "test_user"},
            "chat": {"id": 123456, "type": "private"},
            "date": 1234567890,
            "text": "test"
        }
    }
    response = requests.post(WEBHOOK_URL, json=valid_payload)
    print(f"   Test payload valide: {response.status_code} - {response.text}")

def main():
    print("🤖 Configuration du webhook Telegram ENCO")
    print("=" * 50)
    
    if not BOT_TOKEN:
        print("❌ ERREUR: BOT_TOKEN non défini dans les variables d'environnement")
        return
    
    print(f"🔑 Token bot: {BOT_TOKEN[:10]}...")
    print(f"🌐 URL webhook: {WEBHOOK_URL}")
    print()
    
    # Afficher l'état actuel
    current_info = get_webhook_info()
    print()
    
    # Demander l'action
    print("Actions disponibles:")
    print("1. Configurer le webhook")
    print("2. Supprimer le webhook")
    print("3. Tester le webhook")
    print("4. Afficher les informations")
    print("5. Tout faire (configurer + tester)")
    
    choice = input("\nChoisissez une action (1-5): ").strip()
    
    if choice == "1":
        set_webhook()
    elif choice == "2":
        delete_webhook()
    elif choice == "3":
        test_webhook()
    elif choice == "4":
        get_webhook_info()
    elif choice == "5":
        if set_webhook():
            print()
            test_webhook()
    else:
        print("❌ Choix invalide")

if __name__ == "__main__":
    main() 