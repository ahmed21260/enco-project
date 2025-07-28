#!/usr/bin/env python3
"""
Patch complet ENCO - Vérification et correction des collections Firestore
- Vérifie toutes les collections et leurs données
- Corrige les références de bucket
- Vérifie les routes et configurations
- Restaure les données manquantes si nécessaire
"""

import os
import sys
import json
from datetime import datetime, timedelta
from collections import defaultdict
from dotenv import load_dotenv
load_dotenv()

# Ajouter le répertoire bot au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from utils.firestore import db, USE_FIRESTORE
    print("✅ Import Firestore OK")
except Exception as e:
    print(f"❌ Erreur import Firestore: {e}")
    sys.exit(1)

# Configuration
BUCKET_CORRECT = "enco-prestarail.firebasestorage.app"
COLLECTIONS_ATTENDUES = [
    'positions_operateurs',
    'positions_log', 
    'anomalies',
    'urgences',
    'checklists',
    'prises_poste',
    'photos',
    'operateurs',
    'bons_attachement'
]

def verifier_configuration():
    """Vérifie la configuration Firebase"""
    print("\n🔧 Vérification de la configuration...")
    
    # Vérifier les variables d'environnement
    bucket_env = os.getenv("FIREBASE_STORAGE_BUCKET")
    print(f"📦 Bucket configuré: {bucket_env}")
    
    if bucket_env != BUCKET_CORRECT:
        print(f"⚠️  Bucket incorrect! Attendu: {BUCKET_CORRECT}, Actuel: {bucket_env}")
        return False
    
    print(f"✅ Bucket correct: {BUCKET_CORRECT}")
    return True

def lister_collections():
    """Liste toutes les collections disponibles"""
    print("\n📋 Collections disponibles dans Firestore:")
    
    if not USE_FIRESTORE or not db:
        print("❌ Firestore non initialisé")
        return []
    
    collections = []
    try:
        for collection in db.collections():
            collections.append(collection.id)
            print(f"  - {collection.id}")
    except Exception as e:
        print(f"❌ Erreur lecture collections: {e}")
        return []
    
    return collections

def verifier_collection(collection_name):
    """Vérifie une collection spécifique"""
    print(f"\n🔍 Vérification collection: {collection_name}")
    
    if not db:
        print("❌ Firestore non initialisé")
        return 0
    
    try:
        docs = list(db.collection(collection_name).stream())
        count = len(docs)
        print(f"  📊 Documents: {count}")
        
        if count > 0:
            # Afficher quelques exemples
            for i, doc in enumerate(docs[:3]):
                data = doc.to_dict()
                print(f"    Exemple {i+1}: {doc.id} - {data.get('timestamp', 'N/A')}")
        
        return count
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        return 0

def corriger_references_bucket():
    """Corrige les références de bucket dans les données"""
    print("\n🔧 Correction des références de bucket...")
    
    if not db:
        print("❌ Firestore non initialisé")
        return
    
    corrections = 0
    
    # Vérifier les photos avec mauvaises URLs
    try:
        photos = db.collection('photos').stream()
        for doc in photos:
            data = doc.to_dict()
            update_needed = False
            
            # Corriger les URLs de bucket
            if 'url' in data and BUCKET_CORRECT not in data['url']:
                old_url = data['url']
                data['url'] = data['url'].replace('default', BUCKET_CORRECT)
                update_needed = True
                print(f"  🔄 Photo {doc.id}: {old_url} → {data['url']}")
            
            if update_needed:
                db.collection('photos').document(doc.id).update(data)
                corrections += 1
    except Exception as e:
        print(f"  ❌ Erreur correction photos: {e}")
    
    print(f"✅ {corrections} références de bucket corrigées")

def restaurer_donnees_test():
    """Restaure des données de test si les collections sont vides"""
    print("\n🔄 Restauration de données de test...")
    
    if not db:
        print("❌ Firestore non initialisé")
        return
    
    # Vérifier si positions_operateurs est vide
    try:
        positions_count = len(list(db.collection('positions_operateurs').stream()))
        if positions_count == 0:
            print("  📍 Collection positions_operateurs vide, restauration...")
            
            # Créer une position de test
            test_position = {
                "operateur_id": "1308750107",
                "operatorId": "1308750107", 
                "nom": "Tanjaoui212",
                "timestamp": datetime.now().isoformat(),
                "latitude": 49.436923,
                "longitude": 2.08554,
                "type": "prise_de_poste",
                "actif": True
            }
            
            db.collection('positions_operateurs').document("1308750107").set(test_position)
            print("  ✅ Position de test restaurée")
    except Exception as e:
        print(f"  ❌ Erreur restauration positions: {e}")
    
    # Vérifier si anomalies est vide
    try:
        anomalies_count = len(list(db.collection('anomalies').stream()))
        if anomalies_count == 0:
            print("  🚨 Collection anomalies vide, restauration...")
            
            # Créer une anomalie de test
            test_anomalie = {
                "operateur_id": "1308750107",
                "operatorId": "1308750107",
                "nom": "Tanjaoui212", 
                "timestamp": datetime.now().isoformat(),
                "description": "Test anomalie - Fuite hydraulique",
                "latitude": 49.436923,
                "longitude": 2.08554,
                "handled": False,
                "urgence_level": "NORMAL"
            }
            
            db.collection('anomalies').add(test_anomalie)
            print("  ✅ Anomalie de test restaurée")
    except Exception as e:
        print(f"  ❌ Erreur restauration anomalies: {e}")

def verifier_dashboard_routes():
    """Vérifie les routes du dashboard"""
    print("\n🌐 Vérification des routes dashboard...")
    
    # Vérifier la configuration Firebase du dashboard
    dashboard_config_path = "../admin-dashboard/src/firebaseConfig.js"
    if os.path.exists(dashboard_config_path):
        print(f"  📁 Config dashboard trouvée: {dashboard_config_path}")
        try:
            with open(dashboard_config_path, 'r') as f:
                content = f.read()
                if BUCKET_CORRECT in content:
                    print("  ✅ Bucket correct dans config dashboard")
                else:
                    print("  ⚠️  Bucket incorrect dans config dashboard")
        except Exception as e:
            print(f"  ❌ Erreur lecture config dashboard: {e}")
    else:
        print("  ❌ Config dashboard non trouvée")

def generer_rapport(collections_disponibles, stats_collections):
    """Génère un rapport complet"""
    print("\n" + "="*60)
    print("📊 RAPPORT COMPLET - PATCH COLLECTIONS")
    print("="*60)
    
    print(f"\n🔧 Configuration:")
    print(f"  - Bucket configuré: {os.getenv('FIREBASE_STORAGE_BUCKET', 'NON DÉFINI')}")
    print(f"  - Bucket attendu: {BUCKET_CORRECT}")
    print(f"  - Firestore activé: {USE_FIRESTORE}")
    
    print(f"\n📋 Collections ({len(collections_disponibles)} trouvées):")
    for coll in COLLECTIONS_ATTENDUES:
        if coll in collections_disponibles:
            count = stats_collections.get(coll, 0)
            status = "✅" if count > 0 else "⚠️"
            print(f"  {status} {coll}: {count} documents")
        else:
            print(f"  ❌ {coll}: MANQUANTE")
    
    print(f"\n🎯 Actions recommandées:")
    if not USE_FIRESTORE:
        print("  - Activer Firestore (ENCO_USE_FIRESTORE=1)")
    if os.getenv('FIREBASE_STORAGE_BUCKET') != BUCKET_CORRECT:
        print("  - Corriger FIREBASE_STORAGE_BUCKET")
    
    collections_vides = [coll for coll in COLLECTIONS_ATTENDUES if coll in collections_disponibles and stats_collections.get(coll, 0) == 0]
    if collections_vides:
        print(f"  - Collections vides à vérifier: {', '.join(collections_vides)}")

def main():
    print("🚀 Démarrage du patch complet ENCO")
    print("="*50)
    
    # 1. Vérifier la configuration
    config_ok = verifier_configuration()
    
    # 2. Lister les collections
    collections_disponibles = lister_collections()
    
    # 3. Vérifier chaque collection attendue
    stats_collections = {}
    for collection in COLLECTIONS_ATTENDUES:
        if collection in collections_disponibles:
            count = verifier_collection(collection)
            stats_collections[collection] = count
    
    # 4. Corriger les références de bucket
    if config_ok:
        corriger_references_bucket()
    
    # 5. Restaurer des données de test si nécessaire
    if config_ok:
        restaurer_donnees_test()
    
    # 6. Vérifier les routes dashboard
    verifier_dashboard_routes()
    
    # 7. Générer le rapport
    generer_rapport(collections_disponibles, stats_collections)
    
    print("\n✅ Patch terminé!")

if __name__ == '__main__':
    main() 