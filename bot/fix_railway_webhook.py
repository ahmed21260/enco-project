#!/usr/bin/env python3
"""
Script pour diagnostiquer et corriger les problèmes de webhook Railway
Usage: python fix_railway_webhook.py
"""

import os
import requests
import json


def check_railway_status():
    """Vérifie le statut du service Railway"""
    print("🔍 Vérification du statut Railway")
    print("=" * 50)
    
    # URL du service (à adapter selon votre configuration)
    service_url = "https://enco-prestarail-bot.railway.app"
    
    try:
        # Test de la page d'accueil
        response = requests.get(service_url, timeout=10)
        print(f"✅ Service accessible: {response.status_code}")
        print(f"   Contenu: {response.text[:100]}...")
        
        # Test du health check
        health_response = requests.get(f"{service_url}/health", timeout=10)
        print(f"✅ Health check: {health_response.status_code}")
        if health_response.status_code == 200:
            print(f"   Status: {health_response.json()}")
        
        return True
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

def test_webhook_railway_notifications():
    """Teste le webhook avec des notifications Railway"""
    print("\n🧪 Test des notifications Railway")
    print("=" * 50)
    
    webhook_url = "https://enco-prestarail-bot.railway.app/webhook"
    
    # Test avec une notification de déploiement Railway
    railway_deploy_payload = {
        "type": "DEPLOY",
        "project": {
            "id": "test-project-id",
            "name": "test-project"
        },
        "deployment": {
            "id": "test-deployment-id"
        }
    }
    
    try:
        response = requests.post(webhook_url, json=railway_deploy_payload, timeout=10)
        print(f"🚂 Test notification Railway: {response.status_code}")
        print(f"   Réponse: {response.text}")
        
        if response.status_code == 200:
            print("✅ Notification Railway correctement ignorée")
        else:
            print("❌ Erreur: la notification Railway n'est pas ignorée")
            
    except Exception as e:
        print(f"❌ Erreur de test: {e}")

def test_webhook_telegram():
    """Teste le webhook avec un update Telegram valide"""
    print("\n📱 Test des updates Telegram")
    print("=" * 50)
    
    webhook_url = "https://enco-prestarail-bot.railway.app/webhook"
    
    # Test avec un update Telegram valide
    telegram_payload = {
        "update_id": 123456789,
        "message": {
            "message_id": 1,
            "from": {"id": 123456, "username": "test_user"},
            "chat": {"id": 123456, "type": "private"},
            "date": 1234567890,
            "text": "/start"
        }
    }
    
    try:
        response = requests.post(webhook_url, json=telegram_payload, timeout=10)
        print(f"📱 Test update Telegram: {response.status_code}")
        print(f"   Réponse: {response.text}")
        
        if response.status_code == 200:
            print("✅ Update Telegram correctement traité")
        else:
            print("❌ Erreur: l'update Telegram n'est pas traité")
            
    except Exception as e:
        print(f"❌ Erreur de test: {e}")

def get_deployment_instructions():
    """Affiche les instructions de déploiement"""
    print("\n🚀 Instructions de déploiement")
    print("=" * 50)
    print("1. Commitez les changements:")
    print("   git add .")
    print("   git commit -m 'Fix Railway webhook notifications'")
    print("   git push origin main")
    print()
    print("2. Railway va automatiquement redéployer")
    print()
    print("3. Vérifiez les logs Railway pour confirmer:")
    print("   - Le bot démarre sans erreur")
    print("   - Les notifications Railway sont ignorées")
    print("   - Les updates Telegram sont traités")
    print()
    print("4. Testez le webhook après déploiement:")
    print("   python fix_railway_webhook.py")

def main():
    print("🔧 Diagnostic et correction du webhook Railway ENCO")
    print("=" * 60)
    
    # Vérifier le statut actuel
    if check_railway_status():
        print("\n✅ Le service Railway est accessible")
        
        # Tester les notifications Railway
        test_webhook_railway_notifications()
        
        # Tester les updates Telegram
        test_webhook_telegram()
        
        print("\n📋 Résumé:")
        print("- Les notifications Railway doivent retourner 200 et être ignorées")
        print("- Les updates Telegram doivent retourner 200 et être traités")
        print("- Les payloads invalides doivent retourner 400")
        
    else:
        print("\n❌ Le service Railway n'est pas accessible")
        print("Vérifiez que le déploiement est terminé et que l'URL est correcte")
    
    # Afficher les instructions de déploiement
    get_deployment_instructions()

if __name__ == "__main__":
    main() 