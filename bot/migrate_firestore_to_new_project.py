#!/usr/bin/env python3
"""
Migration Firestore → Firestore (ancien projet → nouveau projet)
- Copie toutes les collections principales d'un ancien projet Firebase vers le nouveau (enco-prestarail)
- Corrige les URLs de bucket dans les documents photos si besoin
"""

import firebase_admin
from firebase_admin import credentials, firestore
import os
import copy

BUCKET = os.environ.get('FIREBASE_STORAGE_BUCKET', 'enco-prestarail.firebasestorage.app')

# Chemins des fichiers service account
OLD_CRED_PATH = 'old_serviceAccountKey_railway.txt'  # À placer dans bot/
NEW_CRED_PATH = 'serviceAccountKey_railway.txt'      # Déjà dans bot/

# Patch : si le fichier old n'existe pas, utiliser le même que le nouveau
if not os.path.exists(OLD_CRED_PATH):
    print(f"⚠️  Fichier {OLD_CRED_PATH} introuvable, utilisation de {NEW_CRED_PATH} pour les deux Firestore.")
    OLD_CRED_PATH = NEW_CRED_PATH

# Liste des collections à migrer
COLLECTIONS = [
    'positions_log',
    'anomalies',
    'urgences',
    'checklists',
    'photos',
    'operateurs',
    'prises_poste',
    'bons_attachement'
]

BUCKET_CORRECT = 'enco-prestarail.firebasestorage.app'

# Initialisation Firestore ancien projet
print('Connexion à l\'ancien Firestore...')
cred_old = credentials.Certificate(OLD_CRED_PATH)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred_old, {'storageBucket': BUCKET}, name='old')
db_old = firestore.client(firebase_admin.get_app('old'))

# Initialisation Firestore nouveau projet
print('Connexion au nouveau Firestore...')
cred_new = credentials.Certificate(NEW_CRED_PATH)
if len(firebase_admin._apps) == 1:
    firebase_admin.initialize_app(cred_new, {'storageBucket': BUCKET}, name='new')
db_new = firestore.client(firebase_admin.get_app('new'))

print('\n--- MIGRATION DES COLLECTIONS ---')
for coll in COLLECTIONS:
    print(f'\nMigration de la collection : {coll}')
    docs = list(db_old.collection(coll).stream())
    print(f'  {len(docs)} documents à migrer...')
    for doc in docs:
        data = doc.to_dict()
        # Correction des URLs de bucket pour les photos
        if coll == 'photos':
            if 'url' in data and BUCKET_CORRECT not in data['url']:
                data['url'] = data['url'].replace('default', BUCKET_CORRECT)
            if 'photoURL' in data and BUCKET_CORRECT not in data['photoURL']:
                data['photoURL'] = data['photoURL'].replace('default', BUCKET_CORRECT)
        # Ajout dans la nouvelle base
        db_new.collection(coll).document(doc.id).set(copy.deepcopy(data))
    print(f'  ✅ {len(docs)} documents migrés pour {coll}')

print('\n--- MIGRATION TERMINÉE ---')
print('Vérifie le nouveau projet Firestore (enco-prestarail) pour toutes les collections !') 