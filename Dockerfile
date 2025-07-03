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

# ---- FINAL IMAGE (multi-stage, à adapter selon ton infra Railway) ---- 