#!/usr/bin/env python3
"""
Script FULL AUTO de correction et de synchronisation fuzzy des photos historiques ENCO
- Parcourt toutes les collections Firestore concernées
- Corrige tous les liens photos (URL) dans chaque document
- Fait du fuzzy matching sur les fichiers locaux pour maximiser la récupération
- Upload les photos locales manquantes dans Storage et crée les documents Firestore manquants
- Génère un rapport détaillé
"""
import os
import json
import argparse
from datetime import datetime
from utils.firestore import db, upload_photo_to_storage
from dotenv import load_dotenv
load_dotenv()

# Répertoire local des photos
LOCAL_PHOTOS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'bot', 'photos'))

# Collections à traiter et leurs champs photo
PHOTO_COLLECTIONS = [
    {'name': 'prises_poste', 'fields': ['photos_file_ids', 'photos_urls', 'photoURL', 'photoUrl', 'urlPhoto']},
    {'name': 'anomalies', 'fields': ['photo_file_id', 'photoURL', 'photoUrl', 'urlPhoto']},
    {'name': 'urgences', 'fields': ['photo_file_id', 'photoURL', 'photoUrl', 'urlPhoto']},
    {'name': 'bons_attachement', 'fields': ['photo_file_id', 'photoURL', 'photoUrl', 'urlPhoto']},
    {'name': 'maintenance', 'fields': ['photo_file_id', 'photoURL', 'photoUrl', 'urlPhoto']},
]

# Utilitaires

def get_telegram_id_from_photo_file_id(photo_file_id):
    if not photo_file_id:
        return None
    if photo_file_id.endswith('.jpg'):
        parts = photo_file_id.split('_')
        if len(parts) >= 3:
            return '_'.join(parts[2:]).replace('.jpg', '')
        else:
            return photo_file_id.replace('.jpg', '')
    return photo_file_id

def fuzzy_find_local_photo(telegram_id):
    if not telegram_id:
        return None
    best_match = None
    best_score = 0
    for fname in os.listdir(LOCAL_PHOTOS_DIR):
        if telegram_id in fname:
            return os.path.join(LOCAL_PHOTOS_DIR, fname)
        score = len(os.path.commonprefix([telegram_id, fname]))
        if score > best_score:
            best_score = score
            best_match = fname
    if best_score > 10 and best_match:
        return os.path.join(LOCAL_PHOTOS_DIR, best_match)
    return None

def upload_and_create_photo_doc(local_path, telegram_id, db):
    storage_path = os.path.basename(local_path)
    url = upload_photo_to_storage(local_path, storage_path)
    if url:
        doc = {
            'photo_file_id': storage_path.replace('.jpg', ''),
            'photoURL': url,
            'createdAt': datetime.now().isoformat(),
            'type': 'sync_import',
        }
        db.collection('photos').add(doc)
        return url
    return None

def main(dry_run=True):
    print(f"=== Correction fuzzy des photos ENCO (dry_run={dry_run}) ===")
    if not db:
        print("❌ Firestore non disponible")
        return
    photos_ref = db.collection('photos')
    photos_docs = list(photos_ref.stream())
    rapport = {'corrections': [], 'fuzzy': [], 'manquantes': [], 'creations': [], 'timestamp': datetime.now().isoformat()}
    for col in PHOTO_COLLECTIONS:
        col_name = col['name']
        print(f"\n--- Traitement collection {col_name} ---")
        col_ref = db.collection(col_name)
        docs = list(col_ref.stream())
        for doc in docs:
            data = doc.to_dict()
            doc_id = doc.id
            corrections = []
            for field in col['fields']:
                value = data.get(field)
                if isinstance(value, list):
                    new_urls = []
                    for pfid in value:
                        telegram_id = get_telegram_id_from_photo_file_id(pfid)
                        url = None
                        # 1. Chercher dans photos
                        for pdoc in photos_docs:
                            pdata = pdoc.to_dict()
                            pfid2 = pdata.get('photo_file_id')
                            if pfid2 and get_telegram_id_from_photo_file_id(pfid2) == telegram_id:
                                url = pdata.get('photoURL') or pdata.get('url')
                                break
                        # 2. Fuzzy match local si pas trouvé
                        if not url:
                            local_path = fuzzy_find_local_photo(telegram_id)
                            if local_path:
                                if not dry_run:
                                    url = upload_and_create_photo_doc(local_path, telegram_id, db)
                                    photos_docs = list(photos_ref.stream())
                                rapport['fuzzy'].append({'telegram_id': telegram_id, 'local_path': local_path, 'doc': doc_id, 'collection': col_name})
                        if url:
                            new_urls.append(url)
                        else:
                            rapport['manquantes'].append({'telegram_id': telegram_id, 'doc': doc_id, 'collection': col_name})
                    if new_urls and not dry_run:
                        doc.reference.update({field.replace('file_ids', 'urls'): new_urls, 'last_updated': datetime.now()})
                        corrections.append({'field': field.replace('file_ids', 'urls'), 'urls': new_urls})
                elif isinstance(value, str):
                    telegram_id = get_telegram_id_from_photo_file_id(value)
                    url = None
                    for pdoc in photos_docs:
                        pdata = pdoc.to_dict()
                        pfid2 = pdata.get('photo_file_id')
                        if pfid2 and get_telegram_id_from_photo_file_id(pfid2) == telegram_id:
                            url = pdata.get('photoURL') or pdata.get('url')
                            break
                    if not url:
                        local_path = fuzzy_find_local_photo(telegram_id)
                        if local_path:
                            if not dry_run:
                                url = upload_and_create_photo_doc(local_path, telegram_id, db)
                                photos_docs = list(photos_ref.stream())
                            rapport['fuzzy'].append({'telegram_id': telegram_id, 'local_path': local_path, 'doc': doc_id, 'collection': col_name})
                    if url and not dry_run:
                        doc.reference.update({field.replace('file_id', 'URL'): url, 'last_updated': datetime.now()})
                        corrections.append({'field': field.replace('file_id', 'URL'), 'url': url})
                    elif not url:
                        rapport['manquantes'].append({'telegram_id': telegram_id, 'doc': doc_id, 'collection': col_name})
            if corrections:
                rapport['corrections'].append({'doc': doc_id, 'collection': col_name, 'corrections': corrections})
    with open('fix_photos_fuzzy_full_auto_report.json', 'w', encoding='utf-8') as f:
        json.dump(rapport, f, indent=2, ensure_ascii=False)
    print(f"\n=== Rapport généré : fix_photos_fuzzy_full_auto_report.json ===")
    print(f"Corrections : {len(rapport['corrections'])}")
    print(f"Photos fuzzy : {len(rapport['fuzzy'])}")
    print(f"Photos manquantes : {len(rapport['manquantes'])}")
    print("(dry_run: aucune modification Firestore)" if dry_run else "(modifications appliquées)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Correction fuzzy des photos ENCO")
    parser.add_argument('--apply', action='store_true', help='Appliquer les corrections (sinon dry-run)')
    args = parser.parse_args()
    main(dry_run=not args.apply) 