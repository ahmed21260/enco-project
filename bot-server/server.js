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

// 📬 Route webhook (nécessaire si mode webhook)
app.post('/webhook', (req, res) => {
  console.log('✅ Webhook reçu :', req.body);
  bot.processUpdate(req.body);
  res.sendStatus(200);
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