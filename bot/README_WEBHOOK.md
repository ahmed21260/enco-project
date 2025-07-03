# 🔧 Configuration et Test du Webhook Telegram

Ce dossier contient les scripts pour configurer, tester et diagnostiquer le webhook Telegram du bot ENCO.

## 📋 Fichiers

- `main.py` - Bot principal avec webhook sécurisé
- `setup_webhook.py` - Script de configuration du webhook
- `test_webhook.py` - Script de test du webhook
- `README_WEBHOOK.md` - Ce fichier

## 🚀 Déploiement

### 1. Variables d'environnement requises

```bash
BOT_TOKEN=your_telegram_bot_token
ENCO_USE_FIRESTORE=1
FIREBASE_SERVICE_ACCOUNT={"type": "service_account", ...}
FIREBASE_STORAGE_BUCKET=enco-prestarail.firebasestorage.app
PORT=8080
```

### 2. Déploiement sur Railway

Le `Procfile` doit être configuré pour exposer le bot Python :

```
web: cd bot && python main.py
worker: cd api && npm start
```

## 🔧 Configuration du Webhook

### Utilisation du script setup_webhook.py

```bash
cd bot
python setup_webhook.py
```

**Actions disponibles :**
1. **Configurer le webhook** - Configure le webhook vers `https://enco-prestarail-bot.railway.app/webhook`
2. **Supprimer le webhook** - Supprime la configuration actuelle
3. **Tester le webhook** - Teste la réponse du webhook
4. **Afficher les informations** - Affiche l'état actuel du webhook
5. **Tout faire** - Configure et teste le webhook

### Configuration manuelle

```bash
# Vérifier l'état actuel
curl "https://api.telegram.org/bot<BOT_TOKEN>/getWebhookInfo"

# Configurer le webhook
curl -X POST "https://api.telegram.org/bot<BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://enco-prestarail-bot.railway.app/webhook",
    "allowed_updates": ["message", "callback_query", "photo", "voice"],
    "max_connections": 40
  }'

# Supprimer le webhook
curl -X POST "https://api.telegram.org/bot<BOT_TOKEN>/deleteWebhook"
```

## 🧪 Test du Webhook

### Utilisation du script test_webhook.py

```bash
cd bot
python test_webhook.py
```

Ce script teste :
- ✅ **Payloads valides** (doivent retourner 200)
- ❌ **Payloads invalides** (doivent retourner 400)
- 🌐 **Méthodes HTTP** (seul POST autorisé)

### Tests manuels

```bash
# Test avec payload invalide (doit retourner 400)
curl -X POST "https://enco-prestarail-bot.railway.app/webhook" \
  -H "Content-Type: application/json" \
  -d '{"test": "invalid"}'

# Test avec payload valide (doit retourner 200)
curl -X POST "https://enco-prestarail-bot.railway.app/webhook" \
  -H "Content-Type: application/json" \
  -d '{
    "update_id": 123456789,
    "message": {
      "message_id": 1,
      "from": {"id": 123456, "username": "test_user"},
      "chat": {"id": 123456, "type": "private"},
      "date": 1234567890,
      "text": "/start"
    }
  }'
```

## 🔍 Diagnostic des Problèmes

### Erreurs courantes

1. **TypeError: Update.__init__() got an unexpected keyword argument 'type'**
   - **Cause** : Payload reçu n'est pas un vrai update Telegram
   - **Solution** : Vérifier que seul Telegram appelle le webhook

2. **TypeError: Update.__init__() missing 1 required positional argument: 'update_id'**
   - **Cause** : Payload sans `update_id`
   - **Solution** : Même que ci-dessus

3. **404 Not Found**
   - **Cause** : Mauvais process exposé sur Railway
   - **Solution** : Vérifier le Procfile et redéployer

### Vérifications à faire

1. **Logs Railway** : Vérifier que le bot Python démarre
2. **Webhook info** : Vérifier l'URL configurée
3. **Tests manuels** : Utiliser les scripts de test
4. **Variables d'environnement** : Vérifier BOT_TOKEN

## 📝 Logs

Le bot log maintenant :
- 🔍 **Payload reçu** : Contenu JSON complet
- ✅ **Updates valides** : ID et type d'update
- ❌ **Payloads invalides** : Raison du rejet
- 🚨 **Erreurs** : Détails des exceptions

## 🎯 Bonnes Pratiques

1. **Ne jamais tester `/webhook` manuellement** avec des payloads inventés
2. **Utiliser les scripts de test** pour diagnostiquer
3. **Vérifier les logs** après chaque déploiement
4. **Configurer le webhook** après chaque redéploiement
5. **Protéger le endpoint** contre les appels non-Telegram

## 🔄 Workflow de Déploiement

1. **Déployer** le code sur Railway
2. **Vérifier** que le bot démarre (logs Railway)
3. **Configurer** le webhook (`python setup_webhook.py`)
4. **Tester** le webhook (`python test_webhook.py`)
5. **Envoyer un message** au bot sur Telegram
6. **Vérifier** les logs pour confirmer le fonctionnement

---

**Note** : Le webhook est maintenant sécurisé et ne traite que les vrais updates Telegram. Les payloads invalides sont rejetés avec un code 400 approprié. 