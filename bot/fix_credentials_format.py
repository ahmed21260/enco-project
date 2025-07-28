#!/usr/bin/env python3
"""
Script pour corriger le format du fichier de credentials Firebase
Remplace les \\n par de vrais retours à la ligne
"""

import json
import os

def fix_credentials_format():
    """Corrige le format du fichier de credentials Firebase"""
    
    cred_file = "serviceAccountKey_railway.txt"
    
    if not os.path.exists(cred_file):
        print(f"❌ Fichier {cred_file} non trouvé")
        return
    
    try:
        # Lire le contenu actuel
        with open(cred_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parser le JSON
        cred_data = json.loads(content)
        
        # Corriger la clé privée en remplaçant \\n par \n
        if 'private_key' in cred_data:
            cred_data['private_key'] = cred_data['private_key'].replace('\\n', '\n')
        
        # Sauvegarder le fichier corrigé
        with open(cred_file, 'w', encoding='utf-8') as f:
            json.dump(cred_data, f, indent=2)
        
        print(f"✅ Fichier {cred_file} corrigé avec succès")
        
        # Vérification
        print("🔍 Vérification du format...")
        with open(cred_file, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
        
        if 'private_key' in test_data and '\n' in test_data['private_key']:
            print("✅ Format de la clé privée correct")
        else:
            print("⚠️  Format de la clé privée suspect")
            
    except Exception as e:
        print(f"❌ Erreur lors de la correction: {e}")

if __name__ == '__main__':
    print("🔧 Correction du format du fichier de credentials Firebase...")
    fix_credentials_format()
    print("✅ Correction terminée !") 