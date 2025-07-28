# 📱 Configuration Telegram pour ENCO Planning

## 🎯 Objectif
Configurer l'envoi automatique des plannings aux opérateurs via Telegram.

## 📋 Étapes de configuration

### 1. Créer un bot Telegram
1. Ouvrez Telegram et cherchez `@BotFather`
2. Envoyez `/newbot`
3. Choisissez un nom pour votre bot (ex: "ENCO Planning Bot")
4. Choisissez un username (ex: "enco_planning_bot")
5. **Sauvegardez le token** fourni par BotFather

### 2. Configurer le token dans l'application
1. Créez un fichier `.env` dans le dossier `admin-dashboard/`
2. Ajoutez cette ligne :
```
VITE_TELEGRAM_BOT_TOKEN=votre_token_ici
```
3. Remplacez `votre_token_ici` par le token obtenu de BotFather

### 3. Démarrer une conversation avec le bot
1. Cherchez votre bot par son username
2. Cliquez sur "Start" ou envoyez `/start`
3. Le bot doit répondre avec un message de bienvenue

### 4. Obtenir votre Chat ID
1. Envoyez un message à votre bot
2. Visitez : `https://api.telegram.org/botVOTRE_TOKEN/getUpdates`
3. Cherchez votre `chat_id` dans la réponse JSON

### 5. Tester la connexion
1. Allez dans l'application ENCO
2. Cliquez sur "🧪 Test Nouvelles Fonctionnalités"
3. Lancez les tests pour vérifier la connexion

## 🔧 Configuration des opérateurs

### Ajouter un Telegram ID à un opérateur
1. Allez dans "🐛 Debug Planning"
2. Trouvez l'opérateur dans la liste
3. Si le Telegram ID est manquant, cliquez sur "🔧 Corriger"
4. Ou ajoutez manuellement le `telegram_id` dans Firestore

### Structure des données opérateur
```json
{
  "nom": "Ltanjaoui Tanger danger",
  "operateur_id": "1308750107",
  "telegram_id": "1308750107",
  "actif": true
}
```

## 🚀 Test d'envoi

### Test manuel
1. Créez un planning pour un opérateur avec Telegram ID
2. Cliquez sur "📱 Envoyer Telegram"
3. Vérifiez la réception sur Telegram

### Test automatique
1. Utilisez le composant "🧪 Test Nouvelles Fonctionnalités"
2. Vérifiez que "Connexion Telegram" est ✅
3. Vérifiez que "Envoi Telegram" est ✅

## ⚠️ Dépannage

### Erreur "Unauthorized"
- Vérifiez que le token est correct
- Vérifiez que le bot existe

### Erreur "Chat not found"
- Vérifiez que l'utilisateur a démarré une conversation avec le bot
- Vérifiez que le Chat ID est correct

### Erreur "Forbidden"
- Vérifiez que le bot n'est pas bloqué par l'utilisateur
- Vérifiez les permissions du bot

## 📱 Format des messages

Les messages envoyés incluent :
- 📅 Période d'affectation
- ⏰ Équipe et horaires
- 🏗️ Chantier et adresse
- 📞 Contact et machine
- ⚠️ Consignes de sécurité

## 🔄 Mode fallback

Si la configuration Telegram échoue, le système :
1. Prépare le message
2. Simule l'envoi
3. Affiche un avertissement
4. Continue le fonctionnement normal

## 📞 Support

Pour toute question :
- Vérifiez les logs dans la console du navigateur
- Utilisez le composant "🐛 Debug Planning"
- Testez avec "🧪 Test Nouvelles Fonctionnalités"