#!/usr/bin/env python3
"""
Migration Firestore base → base (même projet)
- Copie toutes les collections de la base (default) vers la base enco-prestarail
"""

import firebase_admin
from firebase_admin import credentials, firestore
import copy
import os
BUCKET = os.environ.get('FIREBASE_STORAGE_BUCKET', 'enco-prestarail.firebasestorage.app')
# Service account du projet (doit être dans bot/)
CRED_PATH = 'serviceAccountKey_railway.txt'

# Nom des bases
SOURCE_DB = '(default)'
TARGET_DB = 'enco-prestarail'

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

# Initialisation Firestore (une seule app, accès aux deux bases par chemin)
print(f'Connexion à Firestore...')
cred = credentials.Certificate(CRED_PATH)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {'storageBucket': BUCKET})
db = firestore.client()

print('\n--- MIGRATION DES COLLECTIONS ---')
for coll in COLLECTIONS:
    print(f'\nMigration de la collection : {coll}')
    # Lire depuis la base (default)
    source_path = f'projects/{cred.project_id}/databases/(default)/documents/{coll}'
    target_path = f'projects/{cred.project_id}/databases/(default)/documents/{TARGET_DB}/{coll}'
    docs = list(db.collection(coll).stream())
    print(f'  {len(docs)} documents à migrer...')
    for doc in docs:
        data = doc.to_dict()
        # Écrire dans la base cible (sous-collection enco-prestarail/{coll})
        db.collection(TARGET_DB).document(coll).collection('data').document(doc.id).set(copy.deepcopy(data))
    print(f'  ✅ {len(docs)} documents migrés pour {coll}')

print('\n--- MIGRATION TERMINÉE ---')
print(f'Verifie la base {TARGET_DB} pour toutes les collections !') 