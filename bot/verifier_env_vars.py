#!/usr/bin/env python3
"""
Vérification et correction des variables d'environnement ENCO
- Vérifie toutes les variables nécessaires
- Propose des corrections
- Génère un fichier .env corrigé
"""

import os
import sys
from datetime import datetime

# Variables attendues
VARIABLES_ATTENDUES = {
    'TELEGRAM_BOT_TOKEN': 'Token du bot Telegram',
    'FIREBASE_STORAGE_BUCKET': 'enco-prestarail.firebasestorage.app',
    'ENCO_USE_FIRESTORE': '1',
    'OPENAI_API_KEY': 'Clé API OpenAI (optionnel)',
    'FIREBASE_SERVICE_ACCOUNT': 'JSON service account Firebase',
    'WEBHOOK_URL': 'URL webhook Railway',
    'PORT': '8080'
}

def verifier_variable(nom, valeur_attendue=None):
    """Vérifie une variable d'environnement"""
    valeur = os.getenv(nom)
    
    if valeur is None:
        return False, f"❌ {nom}: MANQUANTE"
    
    if valeur_attendue and valeur != valeur_attendue:
        return False, f"⚠️  {nom}: {valeur} (attendu: {valeur_attendue})"
    
    return True, f"✅ {nom}: {valeur}"

def generer_fichier_env():
    """Génère un fichier .env avec les variables manquantes"""
    print("\n📝 Génération du fichier .env...")
    
    env_content = []
    env_content.append("# Configuration ENCO Bot")
    env_content.append(f"# Généré le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    env_content.append("")
    
    for nom, description in VARIABLES_ATTENDUES.items():
        valeur_actuelle = os.getenv(nom)
        
        if valeur_actuelle:
            env_content.append(f"{nom}={valeur_actuelle}")
        else:
            if nom == 'FIREBASE_STORAGE_BUCKET':
                env_content.append(f"{nom}=enco-prestarail.firebasestorage.app")
            elif nom == 'ENCO_USE_FIRESTORE':
                env_content.append(f"{nom}=1")
            elif nom == 'PORT':
                env_content.append(f"{nom}=8080")
            else:
                env_content.append(f"{nom}=")
    
    env_content.append("")
    env_content.append("# Variables optionnelles:")
    env_content.append("# OPENAI_API_KEY=sk-...")
    env_content.append("# WEBHOOK_URL=https://...")
    
    return "\n".join(env_content)

def main():
    print("🔧 Vérification des variables d'environnement ENCO")
    print("="*60)
    
    # Vérifier chaque variable
    variables_ok = 0
    variables_total = len(VARIABLES_ATTENDUES)
    
    for nom, description in VARIABLES_ATTENDUES.items():
        if nom in ['FIREBASE_STORAGE_BUCKET', 'ENCO_USE_FIRESTORE', 'PORT']:
            ok, message = verifier_variable(nom, description)
        else:
            ok, message = verifier_variable(nom)
        
        print(f"  {message}")
        if ok:
            variables_ok += 1
    
    # Résumé
    print(f"\n📊 Résumé: {variables_ok}/{variables_total} variables correctes")
    
    if variables_ok < variables_total:
        print("\n⚠️  Variables manquantes ou incorrectes détectées!")
        
        # Générer le fichier .env
        env_content = generer_fichier_env()
        
        try:
            with open('.env', 'w', encoding='utf-8') as f:
                f.write(env_content)
            print("✅ Fichier .env généré avec les corrections")
            print("📁 Vérifiez et complétez le fichier .env généré")
        except Exception as e:
            print(f"❌ Erreur génération .env: {e}")
    else:
        print("✅ Toutes les variables d'environnement sont correctes!")
    
    # Vérifications spéciales:
    print("\n🔍 Vérifications spéciales:")
    
    # Vérifier le bucket Firebase
    bucket = os.getenv('FIREBASE_STORAGE_BUCKET')
    if bucket and bucket != 'enco-prestarail.firebasestorage.app':
        print(f"  ⚠️  Bucket Firebase incorrect: {bucket}")
        print(f"     Attendu: enco-prestarail.firebasestorage.app")
    
    # Vérifier Firestore activé
    firestore_enabled = os.getenv('ENCO_USE_FIRESTORE') == '1'
    if not firestore_enabled:
        print("  ⚠️  Firestore désactivé (ENCO_USE_FIRESTORE != '1')")
    
    # Vérifier OpenAI
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("  ℹ️  OpenAI API key manquante (optionnel)")
    
    print("\n✅ Vérification terminée!")

if __name__ == '__main__':
    main() 