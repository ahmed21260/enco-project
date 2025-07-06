#!/usr/bin/env python3
"""
Audit Firestore Chatbot ENCO
- Vérifie les messages, statuts, réponses IA, erreurs éventuelles
- Donne un résumé clair du flux et des éventuels problèmes
"""

import os
import sys
from datetime import datetime
from collections import Counter

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.firestore import db

USER_LIMIT = 10  # Nombre d'utilisateurs à auditer
MSG_LIMIT = 10   # Nombre de messages par utilisateur

print("\n🚦 Audit Firestore Chatbot ENCO")
print("=" * 50)

if not db:
    print("❌ Firestore non initialisé. Vérifiez la configuration.")
    sys.exit(1)

users_ref = db.collection('users').list_documents(page_size=USER_LIMIT)
user_count = 0
msg_total = 0
msg_with_response = 0
msg_with_error = 0
status_counter = Counter()

for user_doc in users_ref:
    user_id = user_doc.id
    print(f"\n👤 Utilisateur : {user_id}")
    messages_ref = db.collection(f'users/{user_id}/messages')
    messages = list(messages_ref.order_by('timestamp', direction='DESCENDING').limit(MSG_LIMIT).stream())
    if not messages:
        print("  (Aucun message)")
        continue
    user_count += 1
    for msg in messages:
        data = msg.to_dict()
        prompt = data.get('prompt', '[Aucun prompt]')
        response = data.get('response')
        status = data.get('status', {})
        state = status.get('state', 'N/A')
        created = status.get('created_at', data.get('timestamp', 'N/A'))
        updated = status.get('updated_at', 'N/A')
        error = status.get('error')
        print(f"- 📝 Prompt: {prompt[:60]}")
        print(f"  📊 Statut: {state} | Créé: {created} | MAJ: {updated}")
        if response:
            print(f"  🤖 Réponse IA: {response[:80]}{'...' if len(response)>80 else ''}")
            msg_with_response += 1
        else:
            print(f"  ⏳ En attente de réponse IA")
        if error:
            print(f"  ❌ Erreur: {error}")
            msg_with_error += 1
        status_counter[state] += 1
        msg_total += 1

print("\n=== Résumé global ===")
print(f"Utilisateurs audités : {user_count}")
print(f"Messages audités    : {msg_total}")
print(f"Réponses IA         : {msg_with_response}")
print(f"Messages en erreur  : {msg_with_error}")
print(f"Statuts rencontrés  : {dict(status_counter)}")

if msg_with_error > 0:
    print("\n⚠️  Des erreurs ont été détectées dans certains messages. Consultez les logs ci-dessus.")
if msg_total == 0:
    print("ℹ️  Aucun message trouvé. Envoyez un message au bot pour tester le flux.")
else:
    print("\n✅ Audit terminé. Flux Firestore/IA opérationnel si la majorité des statuts sont 'completed'.") 