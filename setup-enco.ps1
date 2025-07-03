# 1. Création du .env
Set-Content .env "TELEGRAM_TOKEN=7563163873:AAH2_NRypoHmZxaU-GrP459ErMwiUzMCoW0"
Add-Content .env "FIREBASE_CREDENTIALS=../firebase/serviceAccountKey.json"
Add-Content .env "PORT=3001"
Add-Content .env "REACT_APP_API_URL=https://believable-motivation-production.up.railway.app"
Add-Content .env "WEBHOOK_URL=https://ton-sous-domaine.railway.app"

# 2. Copie du .env dans les sous-dossiers
Copy-Item .env bot\.env -Force
Copy-Item .env api\.env -Force

# 3. Installation des dépendances API
cd api
npm install

# 4. Installation des dépendances dashboard
cd ../admin-dashboard
npm install --legacy-peer-deps

# 5. Build dashboard
npm run build

# 6. Installation des dépendances bot
cd ../bot
pip install -r requirements.txt

Write-Host "✅ Installation terminée. Prêt pour déploiement Railway !" 