# ---- API (Node.js) ----
FROM node:18 AS api
WORKDIR /app/api
COPY api/package*.json ./
RUN npm install
COPY api/ .

# ---- BOT (Python) ----
FROM python:3.11 AS bot
WORKDIR /app/bot
COPY bot/requirements.txt ./
RUN pip install -r requirements.txt
COPY bot/ .

# ---- DASHBOARD (React) ----
FROM node:18 AS dashboard
WORKDIR /app/admin-dashboard
COPY admin-dashboard/package*.json ./
RUN npm install --legacy-peer-deps
COPY admin-dashboard/ .
RUN npm run build

# ---- FINAL IMAGE ----
FROM python:3.11-slim
WORKDIR /app

# Installer Node.js pour l'API
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copier les dépendances Python
COPY --from=bot /app/bot/requirements.txt ./bot/
RUN pip install -r bot/requirements.txt

# Copier le code du bot
COPY --from=bot /app/bot ./bot

# Copier l'API
COPY --from=api /app/api ./api
WORKDIR /app/api
RUN npm install --only=production

# Copier le dashboard buildé
COPY --from=dashboard /app/admin-dashboard/dist ./admin-dashboard/dist

# Copier les fichiers de configuration
COPY Procfile ./
COPY package*.json ./

# Retourner au répertoire racine
WORKDIR /app

# Exposer le port
EXPOSE 3000

# Commande par défaut (sera surchargée par le Procfile)
CMD ["python", "bot/main.py"] 