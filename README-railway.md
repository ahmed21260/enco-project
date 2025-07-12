# Déploiement ENCO sur Railway

## 1. Prérequis
- Compte Railway (https://railway.app/)
- Repo GitHub à jour

## 2. Variables d'environnement
- Copie le contenu de `.env.example` dans l'interface Railway (onglet Variables)
- Mets à jour `WEBHOOK_URL` après le premier déploiement (ex: https://believable-motivation-production.up.railway.app)

## 3. Déploiement
- Clique sur "New Project" > "Deploy from GitHub repo"
- Laisse Railway builder automatiquement (ou utilise le Dockerfile si besoin)

## 4. Webhook Telegram
- Après le premier déploiement, mets à jour la variable `WEBHOOK_URL` avec l'URL Railway
- Relance le bot pour qu'il set le webhook automatiquement

## 5. Dashboard
- Le build React (`npm run build`) est prêt à être servi sur Railway, Vercel ou Netlify

## 6. API
- Accessible sur `/api` (ex: https://believable-motivation-production.up.railway.app/api)

---

**Ton projet ENCO est prêt pour le cloud !** 