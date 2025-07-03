#!/usr/bin/env python3
"""
Script de test pour vérifier le fonctionnement du webhook
Usage: python test_webhook.py
"""

import requests
import json
import time

# Configuration
WEBHOOK_URL = "https://enco-prestarail-bot.railway.app/webhook"

def test_invalid_payloads():
    """Teste le webhook avec des payloads invalides"""
    print("🧪 Test des payloads invalides")
    print("-" * 40)
    
    test_cases = [
        {
            "name": "Payload vide",
            "payload": {},
            "expected_status": 400
        },
        {
            "name": "Payload sans update_id",
            "payload": {"message": {"text": "test"}},
            "expected_status": 400
        },
        {
            "name": "Payload avec type (non attendu)",
            "payload": {"update_id": 123, "type": "message", "message": {"text": "test"}},
            "expected_status": 400
        },
        {
            "name": "Payload avec update_id null",
            "payload": {"update_id": None},
            "expected_status": 400
        },
        {
            "name": "Payload avec update_id string",
            "payload": {"update_id": "invalid"},
            "expected_status": 400
        }
    ]
    
    for test_case in test_cases:
        print(f"Test: {test_case['name']}")
        try:
            response = requests.post(WEBHOOK_URL, json=test_case['payload'], timeout=10)
            status_ok = response.status_code == test_case['expected_status']
            print(f"   Status: {response.status_code} (attendu: {test_case['expected_status']}) {'✅' if status_ok else '❌'}")
            print(f"   Réponse: {response.text[:100]}...")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
        print()

def test_valid_payloads():
    """Teste le webhook avec des payloads valides"""
    print("✅ Test des payloads valides")
    print("-" * 40)
    
    test_cases = [
        {
            "name": "Message texte simple",
            "payload": {
                "update_id": 123456789,
                "message": {
                    "message_id": 1,
                    "from": {"id": 123456, "username": "test_user", "first_name": "Test"},
                    "chat": {"id": 123456, "type": "private", "title": "Test Chat"},
                    "date": int(time.time()),
                    "text": "/start"
                }
            }
        },
        {
            "name": "Callback query",
            "payload": {
                "update_id": 123456790,
                "callback_query": {
                    "id": "123456789",
                    "from": {"id": 123456, "username": "test_user"},
                    "message": {
                        "message_id": 2,
                        "from": {"id": 123456, "username": "test_user"},
                        "chat": {"id": 123456, "type": "private"},
                        "date": int(time.time()),
                        "text": "Menu"
                    },
                    "data": "test_callback"
                }
            }
        },
        {
            "name": "Photo",
            "payload": {
                "update_id": 123456791,
                "message": {
                    "message_id": 3,
                    "from": {"id": 123456, "username": "test_user"},
                    "chat": {"id": 123456, "type": "private"},
                    "date": int(time.time()),
                    "photo": [
                        {
                            "file_id": "test_file_id",
                            "file_unique_id": "test_unique_id",
                            "width": 640,
                            "height": 480,
                            "file_size": 12345
                        }
                    ],
                    "caption": "Test photo"
                }
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"Test: {test_case['name']}")
        try:
            response = requests.post(WEBHOOK_URL, json=test_case['payload'], timeout=10)
            status_ok = response.status_code == 200
            print(f"   Status: {response.status_code} {'✅' if status_ok else '❌'}")
            print(f"   Réponse: {response.text}")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
        print()

def test_webhook_availability():
    """Teste la disponibilité du webhook"""
    print("🌐 Test de disponibilité du webhook")
    print("-" * 40)
    
    try:
        # Test GET (doit retourner 405 Method Not Allowed)
        response = requests.get(WEBHOOK_URL, timeout=10)
        print(f"GET request: {response.status_code} (attendu: 405) {'✅' if response.status_code == 405 else '❌'}")
    except Exception as e:
        print(f"GET request: ❌ Erreur - {e}")
    
    try:
        # Test PUT (doit retourner 405 Method Not Allowed)
        response = requests.put(WEBHOOK_URL, json={}, timeout=10)
        print(f"PUT request: {response.status_code} (attendu: 405) {'✅' if response.status_code == 405 else '❌'}")
    except Exception as e:
        print(f"PUT request: ❌ Erreur - {e}")
    
    try:
        # Test DELETE (doit retourner 405 Method Not Allowed)
        response = requests.delete(WEBHOOK_URL, timeout=10)
        print(f"DELETE request: {response.status_code} (attendu: 405) {'✅' if response.status_code == 405 else '❌'}")
    except Exception as e:
        print(f"DELETE request: ❌ Erreur - {e}")

def main():
    print("🔍 Test complet du webhook Telegram ENCO")
    print("=" * 60)
    print(f"URL testée: {WEBHOOK_URL}")
    print()
    
    # Test de disponibilité
    test_webhook_availability()
    print()
    
    # Test des payloads invalides
    test_invalid_payloads()
    
    # Test des payloads valides
    test_valid_payloads()
    
    print("🎯 Résumé des tests:")
    print("- Les payloads invalides doivent retourner 400")
    print("- Les payloads valides doivent retourner 200")
    print("- Les méthodes HTTP non autorisées doivent retourner 405")
    print("- Seuls les vrais updates Telegram doivent être traités")

if __name__ == "__main__":
    main() 