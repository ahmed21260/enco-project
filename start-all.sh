#!/bin/bash

# Lancer l'API Express
cd api && npm install && npm run start &
API_PID=$!
cd ..

# Lancer le dashboard (Vite)
cd admin-dashboard && npm install && npm run dev &
DASH_PID=$!
cd ..

# Lancer le bot Telegram (Python)
cd bot && pip install -r requirements.txt && python main.py &
BOT_PID=$!
cd ..

# Attendre que tous les serveurs se terminent
wait $API_PID $DASH_PID $BOT_PID 