#!/usr/bin/env python3
"""
Script de correction automatique du mapping des photos
Extrait les IDs Telegram depuis les photo_file_id de la collection photos
et les mappe avec les photos_file_ids des prises de poste et anomalies
"""

import os
from dotenv import load_dotenv
load_dotenv()

import json
import re
from datetime import datetime
from utils.firestore import db

def extract_telegram_id_from_firebase_id(firebase_id):
    """
    Extrait l'ID Telegram depuis un photo_file_id Firebase Storage
    Format: PREFIX_TYPE_TELEGRAM_ID.jpg
    """
    # Pattern pour extraire l'ID Telegram
    pattern = r'[^_]+_([^_]+)_(.+)\.jpg$'
    match = re.match(pattern, firebase_id)
    
    if match:
        photo_type = match.group(1)  # 'prise' ou 'anomalie'
        telegram_id = match.group(2)  # L'ID Telegram original
        return telegram_id, photo_type
    else:
        return None, None

def fix_photo_mapping():
    """Corrige le mapping des photos entre les collections"""
    
    print("🔧 Début de la correction du mapping des photos...")
    
    # Utiliser la connexion Firestore existante
    if not db:
        print("❌ Erreur: Connexion Firestore non disponible")
        return
    
    # 1. Récupérer toutes les photos avec leurs URLs
    print("📸 Récupération des photos depuis Firestore...")
    photos_ref = db.collection('photos')
    photos_docs = photos_ref.stream()
    
    # Créer un mapping ID Telegram -> URL
    telegram_to_url_mapping = {}
    telegram_to_type_mapping = {}
    
    for doc in photos_docs:
        data = doc.to_dict()
        photo_file_id = data.get('photo_file_id')
        photo_url = data.get('photoURL') or data.get('url')  # Support both field names
        
        if photo_file_id and photo_url:
            telegram_id, photo_type = extract_telegram_id_from_firebase_id(photo_file_id)
            if telegram_id:
                telegram_to_url_mapping[telegram_id] = photo_url
                telegram_to_type_mapping[telegram_id] = photo_type
                print(f"  ✅ Mappé: {telegram_id[:20]}... -> {photo_url[:50]}...")
    
    print(f"📊 {len(telegram_to_url_mapping)} photos mappées avec succès")
    
    # 2. Corriger les prises de poste
    print("\n🔄 Correction des prises de poste...")
    prises_ref = db.collection('prises_poste')
    prises_docs = prises_ref.stream()
    
    prises_updated = 0
    prises_errors = []
    
    for doc in prises_docs:
        data = doc.to_dict()
        photos_file_ids = data.get('photos_file_ids', [])
        
        if photos_file_ids:
            corrected_urls = []
            errors_in_doc = []
            
            for telegram_id in photos_file_ids:
                if telegram_id in telegram_to_url_mapping:
                    corrected_urls.append(telegram_to_url_mapping[telegram_id])
                else:
                    errors_in_doc.append(telegram_id)
                    print(f"  ❌ ID non trouvé dans photos: {telegram_id[:30]}...")
            
            if errors_in_doc:
                prises_errors.append({
                    'doc_id': doc.id,
                    'missing_ids': errors_in_doc
                })
            
            # Mettre à jour le document si des URLs ont été trouvées
            if corrected_urls:
                try:
                    doc.reference.update({
                        'photos_urls': corrected_urls,
                        'last_updated': datetime.now()
                    })
                    prises_updated += 1
                    print(f"  ✅ Prise de poste {doc.id}: {len(corrected_urls)} URLs mises à jour")
                except Exception as e:
                    print(f"  ❌ Erreur mise à jour {doc.id}: {e}")
    
    # 3. Corriger les anomalies
    print("\n🚨 Correction des anomalies...")
    anomalies_ref = db.collection('anomalies')
    anomalies_docs = anomalies_ref.stream()
    
    anomalies_updated = 0
    anomalies_errors = []
    
    for doc in anomalies_docs:
        data = doc.to_dict()
        photo_file_id = data.get('photo_file_id')
        
        if photo_file_id:
            if photo_file_id in telegram_to_url_mapping:
                try:
                    doc.reference.update({
                        'photoURL': telegram_to_url_mapping[photo_file_id],
                        'last_updated': datetime.now()
                    })
                    anomalies_updated += 1
                    print(f"  ✅ Anomalie {doc.id}: URL mise à jour")
                except Exception as e:
                    print(f"  ❌ Erreur mise à jour {doc.id}: {e}")
            else:
                anomalies_errors.append({
                    'doc_id': doc.id,
                    'missing_id': photo_file_id
                })
                print(f"  ❌ ID non trouvé dans photos: {photo_file_id[:30]}...")
    
    # 4. Générer le rapport
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_photos_mapped': len(telegram_to_url_mapping),
            'prises_updated': prises_updated,
            'anomalies_updated': anomalies_updated,
            'prises_errors': len(prises_errors),
            'anomalies_errors': len(anomalies_errors)
        },
        'telegram_to_url_mapping': telegram_to_url_mapping,
        'prises_errors': prises_errors,
        'anomalies_errors': anomalies_errors
    }
    
    # Sauvegarder le rapport
    with open('photo_mapping_fix_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # Afficher le résumé
    print(f"\n📋 === RAPPORT DE CORRECTION ===")
    print(f"✅ Photos mappées: {len(telegram_to_url_mapping)}")
    print(f"✅ Prises de poste mises à jour: {prises_updated}")
    print(f"✅ Anomalies mises à jour: {anomalies_updated}")
    print(f"❌ Erreurs prises de poste: {len(prises_errors)}")
    print(f"❌ Erreurs anomalies: {len(anomalies_errors)}")
    print(f"📄 Rapport détaillé: photo_mapping_fix_report.json")
    
    if prises_errors or anomalies_errors:
        print(f"\n⚠️  IDs manquants détectés - vérifiez le rapport pour les détails")
    
    return report

if __name__ == "__main__":
    try:
        fix_photo_mapping()
    except Exception as e:
        print(f"❌ Erreur lors de la correction: {e}")
        import traceback
        traceback.print_exc() 