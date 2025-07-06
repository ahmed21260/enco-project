#!/usr/bin/env python3
"""
Script pour convertir un fichier serviceAccountKey.json en format Railway
Usage: python convert_json_railway.py
"""

import json
import os

def convert_json_for_railway():
    """Convertit le fichier serviceAccountKey.json en format Railway"""
    
    # Vérifier si le fichier existe
    if not os.path.exists('serviceAccountKey.json'):
        print("❌ Fichier serviceAccountKey.json non trouvé")
        print("📥 Télécharge le fichier depuis Firebase Console > Paramètres > Comptes de service")
        return
    
    try:
        # Lire le fichier JSON original
        with open('serviceAccountKey.json', 'r') as f:
            data = json.load(f)
        
        # Convertir la clé privée pour Railway
        # Remplacer les vrais retours à la ligne par \\n
        private_key = data['private_key']
        # Supprimer les retours à la ligne existants et les remplacer par \\n
        private_key_railway = private_key.replace('\n', '\\n')
        data['private_key'] = private_key_railway
        
        # Convertir en JSON sur une seule ligne
        json_railway = json.dumps(data, separators=(',', ':'))
        
        print("✅ JSON converti pour Railway :")
        print("=" * 80)
        print(json_railway)
        print("=" * 80)
        
        # Sauvegarder dans un fichier
        with open('serviceAccountKey_railway.txt', 'w') as f:
            f.write(json_railway)
        
        print("\n📁 JSON sauvegardé dans 'serviceAccountKey_railway.txt'")
        print("\n🔧 Instructions pour Railway :")
        print("1. Copie le JSON ci-dessus")
        print("2. Va dans Railway > Variables d'environnement")
        print("3. Ajoute/modifie FIREBASE_SERVICE_ACCOUNT")
        print("4. Colle le JSON (tout sur une ligne)")
        print("5. Sauvegarde et redéploie")
        
        return json_railway
        
    except Exception as e:
        print(f"❌ Erreur lors de la conversion : {e}")
        return None

def test_json_validity(json_str):
    """Teste si le JSON est valide"""
    try:
        data = json.loads(json_str)
        print("✅ JSON valide")
        
        # Vérifier les champs requis
        required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
        for field in required_fields:
            if field not in data:
                print(f"❌ Champ manquant : {field}")
                return False
            else:
                print(f"✅ Champ présent : {field}")
        
        # Vérifier que la clé privée commence et finit correctement
        private_key = data['private_key']
        if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
            print("❌ Clé privée mal formatée (début)")
            return False
        if not private_key.endswith('-----END PRIVATE KEY-----'):
            print("❌ Clé privée mal formatée (fin)")
            return False
        
        print("✅ Clé privée formatée correctement")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON invalide : {e}")
        return False

def main():
    print("🔄 Conversion du JSON Firebase pour Railway")
    print("=" * 50)
    
    # Convertir le JSON
    json_railway = convert_json_for_railway()
    
    if json_railway:
        print("\n🧪 Test de validité du JSON...")
        test_json_validity(json_railway)

if __name__ == "__main__":
    main() 