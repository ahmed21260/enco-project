// server.js
const express = require('express');
const bodyParser = require('body-parser');
const TelegramBot = require('node-telegram-bot-api');

const app = express();

// 🔐 Token du bot
const TOKEN = process.env.BOT_TOKEN || 'TON_TOKEN_ICI';

// 🌍 URL du webhook (Railway en prod) — doit être HTTPS
const WEBHOOK_URL = process.env.WEBHOOK_URL || '';

// 🔁 Démarrage du bot : webhook si URL définie, sinon fallback en polling
let bot;

if (WEBHOOK_URL) {
  bot = new TelegramBot(TOKEN);
  bot.setWebHook(`${WEBHOOK_URL}/webhook`);
  console.log('📡 Mode WEBHOOK activé');
} else {
  bot = new TelegramBot(TOKEN, { polling: true });
  console.log('🛰️ Mode POLLING activé (fallback)');
}

// 🧠 Middleware pour parser le JSON
app.use(bodyParser.json());

// 🏥 Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'enco-bot-server' });
});

// 📬 Route webhook (nécessaire si mode webhook)
app.post('/webhook', (req, res) => {
  const body = req.body;
  
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
  
  // Vérifie la présence de update_id (champ obligatoire Telegram)
  if (!body || typeof body.update_id === 'undefined') {
    console.error('❌ Webhook reçu sans update_id ou format incorrect:', body);
    return res.status(400).json({ error: 'Invalid Telegram update: missing update_id' });
  }
  try {
    bot.processUpdate(body);
    res.sendStatus(200);
  } catch (err) {
    console.error('❌ Erreur processUpdate:', err);
    res.status(500).json({ error: 'processUpdate failed' });
  }
});

// 📨 Réaction simple à un message reçu
bot.on('message', (msg) => {
  const chatId = msg.chat.id;
  const text = msg.text || '';
  console.log(`📩 Message reçu de ${msg.from.username || msg.from.first_name}: ${text}`);
  bot.sendMessage(chatId, `👋 Bien reçu ${msg.from.first_name}, tu as dit : "${text}"`);
});

// 🚀 Lancement du serveur Express
const PORT = process.env.PORT || 8080;
app.listen(PORT, () => {
  console.log(`🚀 Serveur BOT en écoute sur port ${PORT}`);
}); 