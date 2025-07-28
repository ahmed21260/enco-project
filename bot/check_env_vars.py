#!/usr/bin/env python3
"""
Script pour vérifier les variables d'environnement nécessaires
Usage: python check_env_vars.py
"""

import os
import json

def check_bot_env_vars():
    """Vérifie les variables d'environnement du bot"""
    print("🤖 Variables d'environnement du BOT")
    print("=" * 50)
    
    required_vars = {
        'BOT_TOKEN': 'Token Telegram du bot',
        'ENCO_USE_FIRESTORE': 'Activer Firebase (doit être 1)',
        'FIREBASE_SERVICE_ACCOUNT': 'JSON du service account Firebase',
        'FIREBASE_STORAGE_BUCKET': 'Bucket Firebase Storage',
        'PORT': 'Port du serveur (optionnel, défaut 8080)'
    }
    
    optional_vars = {
        'ENCO_DEBUG': 'Mode debug (optionnel)',
        'API_URL': 'URL de l\'API (optionnel)'
    }
    
    all_good = True
    
    # Vérifier les variables requises
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            if var == 'FIREBASE_SERVICE_ACCOUNT':
                # Tester si le JSON est valide
                try:
                    json.loads(value)
                    print(f"✅ {var}: JSON valide")
                except json.JSONDecodeError:
                    print(f"❌ {var}: JSON invalide")
                    all_good = False
            elif var == 'ENCO_USE_FIRESTORE':
                if value == '1':
                    print(f"✅ {var}: {value} (Firebase activé)")
                else:
                    print(f"⚠️  {var}: {value} (Firebase désactivé)")
            else:
                # Masquer les valeurs sensibles
                if 'TOKEN' in var or 'KEY' in var:
                    display_value = value[:10] + "..." if len(value) > 10 else "***"
                else:
                    display_value = value
                print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: MANQUANT - {description}")
            all_good = False
    
    # Vérifier les variables optionnelles
    print("\n📋 Variables optionnelles :")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"⚠️  {var}: Non définie - {description}")
    
    return all_good

def check_api_env_vars():
    """Vérifie les variables d'environnement de l'API"""
    print("\n🌐 Variables d'environnement de l'API")
    print("=" * 50)
    
    required_vars = {
        'PORT': 'Port du serveur API',
        'FIREBASE_SERVICE_ACCOUNT': 'JSON du service account Firebase',
        'FIREBASE_STORAGE_BUCKET': 'Bucket Firebase Storage'
    }
    
    optional_vars = {
        'NODE_ENV': 'Environnement Node.js',
        'CORS_ORIGIN': 'Origine CORS'
    }
    
    all_good = True
    
    # Vérifier les variables requises
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            if var == 'FIREBASE_SERVICE_ACCOUNT':
                try:
                    json.loads(value)
                    print(f"✅ {var}: JSON valide")
                except json.JSONDecodeError:
                    print(f"❌ {var}: JSON invalide")
                    all_good = False
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: MANQUANT - {description}")
            all_good = False
    
    # Vérifier les variables optionnelles
    print("\n📋 Variables optionnelles :")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"⚠️  {var}: Non définie - {description}")
    
    return all_good

def generate_env_template():
    """Génère un template de variables d'environnement"""
    print("\n📝 Template de variables d'environnement")
    print("=" * 50)
    
    template = """# Variables d'environnement pour le BOT
BOT_TOKEN=your_telegram_bot_token_here
ENCO_USE_FIRESTORE=1
FIREBASE_SERVICE_ACCOUNT={"type":"service_account","project_id":"your-project","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n","client_email":"...","client_id":"...","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"...","universe_domain":"googleapis.com"}
FIREBASE_STORAGE_BUCKET=enco-prestarail.firebasestorage.app
PORT=8080

# Variables optionnelles
ENCO_DEBUG=0
API_URL=https://your-api-url.railway.app/api

# Variables pour l'API (si séparé)
NODE_ENV=production
CORS_ORIGIN=*
"""
    
    print(template)
    
    # Sauvegarder le template
    with open('env_template.txt', 'w') as f:
        f.write(template)
    
    print("\n📁 Template sauvegardé dans 'env_template.txt'")

def main():
    print("🔍 Vérification des variables d'environnement")
    print("=" * 60)
    
    # Vérifier les variables du bot
    bot_ok = check_bot_env_vars()
    
    # Vérifier les variables de l'API
    api_ok = check_api_env_vars()
    
    # Résumé
    print("\n📊 Résumé :")
    print("=" * 30)
    if bot_ok:
        print("✅ Variables du BOT : OK")
    else:
        print("❌ Variables du BOT : PROBLÈMES")
    
    if api_ok:
        print("✅ Variables de l'API : OK")
    else:
        print("❌ Variables de l'API : PROBLÈMES")
    
    if bot_ok and api_ok:
        print("\n🎉 Toutes les variables sont correctement configurées !")
    else:
        print("\n⚠️  Certaines variables nécessitent une attention.")
        print("Utilise le template ci-dessous pour configurer les variables manquantes.")
        generate_env_template()

if __name__ == "__main__":
    main() 