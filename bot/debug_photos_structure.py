#!/usr/bin/env python3
"""
Script de diagnostic pour vérifier la structure des données
dans les collections photos, prises_poste et anomalies
"""

import os
from dotenv import load_dotenv
load_dotenv()

import json
from datetime import datetime
from utils.firestore import db

def debug_photos_structure():
    """Diagnostique la structure des données dans Firestore"""
    
    print("🔍 Début du diagnostic de la structure des données...")
    
    if not db:
        print("❌ Erreur: Connexion Firestore non disponible")
        return
    
    # 1. Vérifier la collection photos
    print("\n📸 === COLLECTION PHOTOS ===")
    photos_ref = db.collection('photos')
    photos_docs = list(photos_ref.stream())
    
    print(f"Nombre de documents dans 'photos': {len(photos_docs)}")
    
    if photos_docs:
        print("\nStructure du premier document 'photos':")
        first_photo = photos_docs[0].to_dict()
        for key, value in first_photo.items():
            if isinstance(value, str) and len(value) > 100:
                print(f"  {key}: {value[:50]}...")
            else:
                print(f"  {key}: {value}")
    
    # 2. Vérifier la collection prises_poste
    print("\n📋 === COLLECTION PRISES_POSTE ===")
    prises_ref = db.collection('prises_poste')
    prises_docs = list(prises_ref.stream())
    
    print(f"Nombre de documents dans 'prises_poste': {len(prises_docs)}")
    
    if prises_docs:
        print("\nStructure du premier document 'prises_poste':")
        first_prise = prises_docs[0].to_dict()
        for key, value in first_prise.items():
            if isinstance(value, list) and len(value) > 0:
                print(f"  {key}: {len(value)} éléments")
                if key == 'photos_file_ids' and value:
                    print(f"    Premier ID: {value[0][:50]}...")
            elif isinstance(value, str) and len(value) > 100:
                print(f"  {key}: {value[:50]}...")
            else:
                print(f"  {key}: {value}")
    
    # 3. Vérifier la collection anomalies
    print("\n🚨 === COLLECTION ANOMALIES ===")
    anomalies_ref = db.collection('anomalies')
    anomalies_docs = list(anomalies_ref.stream())
    
    print(f"Nombre de documents dans 'anomalies': {len(anomalies_docs)}")
    
    if anomalies_docs:
        print("\nStructure du premier document 'anomalies':")
        first_anomalie = anomalies_docs[0].to_dict()
        for key, value in first_anomalie.items():
            if isinstance(value, str) and len(value) > 100:
                print(f"  {key}: {value[:50]}...")
            else:
                print(f"  {key}: {value}")
    
    # 4. Analyser les champs photos_file_ids dans prises_poste
    print("\n🔍 === ANALYSE DES PHOTOS_FILE_IDS ===")
    all_photo_ids = set()
    prises_with_photos = 0
    
    for doc in prises_docs:
        data = doc.to_dict()
        photos_file_ids = data.get('photos_file_ids', [])
        if photos_file_ids:
            prises_with_photos += 1
            for photo_id in photos_file_ids:
                all_photo_ids.add(photo_id)
    
    print(f"Prises de poste avec photos: {prises_with_photos}")
    print(f"Nombre total d'IDs de photos uniques: {len(all_photo_ids)}")
    
    if all_photo_ids:
        print("\nExemples d'IDs de photos dans prises_poste:")
        for i, photo_id in enumerate(list(all_photo_ids)[:5]):
            print(f"  {i+1}. {photo_id[:50]}...")
    
    # 5. Vérifier si les photos existent dans Storage
    print("\n🗂️ === VÉRIFICATION STORAGE ===")
    if photos_docs:
        print("Documents dans 'photos' trouvés:")
        for i, doc in enumerate(photos_docs[:3]):
            data = doc.to_dict()
            photo_file_id = data.get('photo_file_id', 'N/A')
            photo_url = data.get('photoURL', 'N/A')
            print(f"  {i+1}. photo_file_id: {photo_file_id[:50]}...")
            print(f"     photoURL: {photo_url[:50]}...")
    else:
        print("❌ Aucun document trouvé dans la collection 'photos'")
    
    # 6. Générer un rapport
    report = {
        'timestamp': datetime.now().isoformat(),
        'photos_count': len(photos_docs),
        'prises_count': len(prises_docs),
        'anomalies_count': len(anomalies_docs),
        'prises_with_photos': prises_with_photos,
        'unique_photo_ids': len(all_photo_ids),
        'sample_photo_ids': list(all_photo_ids)[:10] if all_photo_ids else []
    }
    
    with open('debug_photos_structure_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Rapport détaillé: debug_photos_structure_report.json")
    
    return report

if __name__ == "__main__":
    try:
        debug_photos_structure()
    except Exception as e:
        print(f"❌ Erreur lors du diagnostic: {e}")
        import traceback
        traceback.print_exc() 