#!/usr/bin/env python3
"""
Script pour corriger automatiquement tous les chemins de credentials Firebase
Remplace serviceAccountKey.json par serviceAccountKey_railway.txt dans tous les fichiers Python
"""

import os
import re
import glob

def fix_credentials_paths():
    """Corrige tous les chemins de credentials Firebase dans les fichiers Python"""
    
    # Fichiers à corriger dans le dossier bot/
    bot_files = [
        'utils/firestore.py',
        'test_connection.py',
        'handlers/prise_de_poste.py',
        'sync_and_check_firestore.py',
        'handlers/photo.py',
        'migrate_positions.py',
        'migrate_firestore_to_new_project.py',
        'handlers/anomalie.py',
        'migrate_firestore_database.py',
        'inject_test_data.py',
        'create_firestore_collections.py',
        'convert_json_railway.py'
    ]
    
    # Fichiers à corriger dans d'autres dossiers
    other_files = [
        '../firebase/init_firestore.py'
    ]
    
    all_files = bot_files + other_files
    
    corrections_made = 0
    
    for file_path in all_files:
        if not os.path.exists(file_path):
            print(f"⚠️  Fichier non trouvé: {file_path}")
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Corrections spécifiques
            replacements = [
                # Remplace serviceAccountKey.json par serviceAccountKey_railway.txt
                (r'serviceAccountKey\.json', 'serviceAccountKey_railway.txt'),
                
                # Corrige les chemins relatifs dans les handlers
                (r'bot/serviceAccountKey\.json', 'serviceAccountKey_railway.txt'),
                (r'bot/serviceAccountKey_railway\.txt', 'serviceAccountKey_railway.txt'),
                
                # Corrige les chemins dans utils/firestore.py
                (r'\.\./firebase/serviceAccountKey\.json', '../firebase/serviceAccountKey_railway.txt'),
            ]
            
            for pattern, replacement in replacements:
                content = re.sub(pattern, replacement, content)
            
            # Si le contenu a changé, sauvegarder
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ Corrigé: {file_path}")
                corrections_made += 1
            else:
                print(f"ℹ️  Aucun changement: {file_path}")
                
        except Exception as e:
            print(f"❌ Erreur lors du traitement de {file_path}: {e}")
    
    print(f"\n🎯 Total: {corrections_made} fichiers corrigés")
    
    # Vérification finale
    print("\n🔍 Vérification finale des chemins...")
    remaining_files = glob.glob('**/*.py', recursive=True)
    for file_path in remaining_files:
        if 'serviceAccountKey.json' in open(file_path, 'r', encoding='utf-8').read():
            print(f"⚠️  Attention: {file_path} contient encore 'serviceAccountKey.json'")

if __name__ == '__main__':
    print("🔧 Correction automatique des chemins de credentials Firebase...")
    fix_credentials_paths()
    print("\n✅ Correction terminée !") 