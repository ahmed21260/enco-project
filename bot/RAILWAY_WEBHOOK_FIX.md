# 🔧 Fix Railway Webhook Notifications

## 🚨 Problème identifié

Les logs Railway montraient des erreurs 400 sur le webhook :
```
❌ Payload sans update_id reçu, ignoré (pas un update Telegram)
```

**Cause** : Railway envoie automatiquement des notifications de déploiement à votre endpoint `/webhook`, mais votre bot attend uniquement des updates Telegram avec un champ `update_id`.

## 🔍 Analyse des logs

Les payloads Railway reçus contiennent :
```json
{
  "type": "DEPLOY",
  "project": {
    "id": "c7aa1c4e-1c1f-4b22-8f85-380135c05deb",
    "name": "ravishing-enchantment"
  },
  "deployment": {
    "id": "5205aac8-7549-4697-a8e8-fa110bf9cc5f"
  }
}
```

Ces payloads n'ont pas d'`update_id`, donc le webhook les rejette avec une erreur 400.

## ✅ Solution appliquée

### 1. Modification du webhook Python (`bot/main.py`)

Ajout de la détection et l'ignorance des notifications Railway :

```python
# Ignorer les notifications de déploiement Railway
if "type" in data and data["type"] == "DEPLOY":
    logging.info("🚂 Notification de déploiement Railway reçue, ignorée")
    return "Railway deployment notification ignored", 200

# Ignorer les autres types de notifications Railway
if "service" in data or "project" in data:
    logging.info("🚂 Notification Railway reçue, ignorée")
    return "Railway notification ignored", 200
```

### 2. Modification du webhook Node.js (`bot/bot-server/server.js`)

Même logique pour le serveur Node.js :

```javascript
// Ignorer les notifications de déploiement Railway
if (body && body.type === 'DEPLOY') {
  console.log('🚂 Notification de déploiement Railway reçue, ignorée');
  return res.status(200).json({ message: 'Railway deployment notification ignored' });
}

// Ignorer les autres types de notifications Railway
if (body && (body.service || body.project)) {
  console.log('🚂 Notification Railway reçue, ignorée');
  return res.status(200).json({ message: 'Railway notification ignored' });
}
```

### 3. Ajout d'endpoints de santé

- `/health` pour les deux serveurs
- Amélioration de la page d'accueil

## 🧪 Tests

Utilisez le script `fix_railway_webhook.py` pour tester :

```bash
cd bot
python fix_railway_webhook.py
```

Ce script teste :
- ✅ Accessibilité du service Railway
- 🚂 Ignorance des notifications Railway (doit retourner 200)
- 📱 Traitement des updates Telegram (doit retourner 200)
- ❌ Rejet des payloads invalides (doit retourner 400)

## 🚀 Déploiement

1. **Commitez les changements** :
   ```bash
   git add .
   git commit -m 'Fix Railway webhook notifications'
   git push origin main
   ```

2. **Railway redéploie automatiquement**

3. **Vérifiez les logs** pour confirmer :
   - Le bot démarre sans erreur
   - Les notifications Railway sont ignorées avec le message "🚂"
   - Les updates Telegram sont traités normalement

## 📊 Résultat attendu

Après le fix, les logs devraient montrer :
```
🚂 Notification de déploiement Railway reçue, ignorée
🚂 Notification Railway reçue, ignorée
✅ Update Telegram valide reçu (ID: 123456789)
```

Plus d'erreurs 400 pour les notifications Railway !

## 🔄 Workflow de maintenance

1. **Après chaque déploiement** : Vérifiez que les notifications Railway sont ignorées
2. **En cas de problème** : Utilisez `fix_railway_webhook.py` pour diagnostiquer
3. **Pour tester** : Envoyez un message au bot sur Telegram

---

**Note** : Cette solution permet à Railway de continuer à envoyer ses notifications sans perturber le fonctionnement du bot Telegram. 