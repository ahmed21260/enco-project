# 🚂 Chatbot Firestore ENCO

## Vue d'ensemble

Le chatbot Firestore ENCO permet aux opérateurs d'interagir avec l'IA spécialisée dans le domaine ferroviaire via Firestore. Les messages sont traités automatiquement et enrichis avec le contexte métier.

## Architecture

```
Utilisateur → Firestore (users/{uid}/messages) → Assistant AI → Réponse enrichie
```

### Flux de traitement

1. **Envoi de message** : L'utilisateur écrit un message dans `users/{uid}/messages`
2. **Détection** : L'écouteur Firestore détecte le nouveau message
3. **Traitement** : L'assistant AI analyse le message avec contexte ferroviaire
4. **Réponse** : La réponse est ajoutée au document Firestore avec statut

## Configuration

### Variables d'environnement requises

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Firebase
***REMOVED***
FIREBASE_SERVICE_ACCOUNT={"type": "service_account", ...}
FIREBASE_STORAGE_BUCKET=enco-prestarail.appspot.com
```

### Structure Firestore

```
users/
  {uid}/
    messages/
      {message_id}/
        prompt: "Question de l'utilisateur"
        response: "Réponse de l'IA"
        status: {
          state: "completed|processing|error"
          created_at: "2024-01-01T12:00:00"
          updated_at: "2024-01-01T12:00:05"
        }
        timestamp: "2024-01-01T12:00:00"
        user_id: "{uid}"
```

## Utilisation

### 1. Démarrage automatique

L'écouteur Firestore démarre automatiquement avec le bot Telegram :

```bash
cd bot
python main.py
```

### 2. Test manuel

```bash
# Test complet avec écouteur
python test_firestore_chatbot.py

# Test simple de génération
python test_firestore_chatbot.py
```

### 3. Client interactif

```bash
# Mode interactif
python examples/firestore_chatbot_client.py

# Test simple
python examples/firestore_chatbot_client.py
```

## Fonctionnalités

### Contexte ferroviaire spécialisé

L'assistant AI comprend automatiquement :

- **Anomalies** : Analyse des incidents techniques
- **Maintenance** : Conseils de réparation et entretien
- **Sécurité** : Réglementation et procédures
- **Équipements** : Matériel roulant et infrastructure
- **Optimisation** : Amélioration des opérations

### Analyse intelligente

- **Recherche sémantique** : Trouve des anomalies similaires
- **Catégorisation** : Classe automatiquement les demandes
- **Priorisation** : Évalue l'urgence des situations
- **Suggestions** : Propose des résolutions basées sur l'historique

## Exemples d'utilisation

### Message utilisateur
```json
{
  "prompt": "J'ai une anomalie sur la signalisation à la gare centrale, que faire ?",
  "timestamp": "2024-01-01T12:00:00",
  "user_id": "operator_123"
}
```

### Réponse IA
```json
{
  "response": "Pour une anomalie de signalisation à la gare centrale :\n\n1. Vérifiez immédiatement l'état des signaux\n2. Contactez le poste de commande\n3. Appliquez les procédures de sécurité\n4. Documentez l'incident\n\nAnomalies similaires récentes :\n- Signal défaillant voie 3 (résolu en 15min)\n- Panne d'alimentation signalisation (résolu en 45min)",
  "status": {
    "state": "completed",
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T12:00:05"
  }
}
```

## Intégration avec le dashboard

Le dashboard peut afficher les conversations en temps réel :

```javascript
// Écouter les messages d'un utilisateur
const messagesRef = db.collection(`users/${uid}/messages`);
messagesRef.onSnapshot((snapshot) => {
  snapshot.docChanges().forEach((change) => {
    if (change.type === 'modified') {
      const data = change.doc.data();
      if (data.response) {
        // Afficher la réponse dans l'interface
        displayResponse(data.prompt, data.response);
      }
    }
  });
});
```

## Dépannage

### Problèmes courants

1. **Assistant AI non disponible**
   - Vérifiez `OPENAI_API_KEY`
   - Vérifiez la connexion internet

2. **Firestore non initialisé**
   - Vérifiez `***REMOVED***`
   - Vérifiez `FIREBASE_SERVICE_ACCOUNT`

3. **Écouteur ne démarre pas**
   - Vérifiez les logs du bot
   - Vérifiez les permissions Firestore

### Logs utiles

```bash
# Vérifier l'état de l'assistant
grep "Assistant AI" bot.log

# Vérifier l'écouteur Firestore
grep "Écouteur Firestore" bot.log

# Vérifier les messages traités
grep "Nouveau message détecté" bot.log
```

## Développement

### Ajouter de nouvelles fonctionnalités

1. **Nouveau type de demande** : Modifiez `generate_railway_response()`
2. **Nouvelle logique métier** : Ajoutez des méthodes dans `ENCOAIAssistant`
3. **Nouveaux embeddings** : Utilisez `services/embeddings.py`

### Tests

```bash
# Test unitaire de l'assistant
python -m pytest tests/test_ai_assistant.py

# Test d'intégration
python test_firestore_chatbot.py
```

## Sécurité

- Les messages sont isolés par utilisateur (`users/{uid}/messages`)
- L'accès Firestore est contrôlé par les règles de sécurité
- Les clés API sont stockées dans les variables d'environnement
- Les logs ne contiennent pas d'informations sensibles

## Support

Pour toute question ou problème :
1. Vérifiez les logs du bot
2. Testez avec le client interactif
3. Vérifiez la configuration Firebase/OpenAI
4. Consultez la documentation Firestore 