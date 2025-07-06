# 🚀 Déploiement de l'API ENCO sur Railway

## **Étapes de déploiement :**

### 1. **Préparer le repository API**
```bash
cd api/
git init
git add .
git commit -m "Initial commit API ENCO"
```

### 2. **Créer un nouveau projet Railway**
- Va sur [Railway.app](https://railway.app)
- Clique "New Project"
- Choisis "Deploy from GitHub repo"
- Connecte ton repo GitHub
- Sélectionne le dossier `api/`

### 3. **Configurer les variables d'environnement**
Dans Railway, va dans l'onglet "Variables" et ajoute :

```env
FIREBASE_SERVICE_ACCOUNT={"type":"service_account","project_id":"enco-prestarail",...}
FIREBASE_STORAGE_BUCKET=enco-prestarail.appspot.com
PORT=3001
```

### 4. **Déployer**
- Railway va automatiquement détecter le `Procfile`
- Le build se lance automatiquement
- L'API sera accessible sur : `https://enco-api-production.up.railway.app`

### 5. **Tester l'API**
```bash
# Test healthcheck
curl https://enco-api-production.up.railway.app/

# Test positions
curl https://enco-api-production.up.railway.app/api/positions

# Test anomalies
curl https://enco-api-production.up.railway.app/api/anomalies
```

## **URLs de l'API :**

- **Healthcheck** : `https://enco-api-production.up.railway.app/`
- **Positions** : `https://enco-api-production.up.railway.app/api/positions`
- **Anomalies** : `https://enco-api-production.up.railway.app/api/anomalies`
- **Urgences** : `https://enco-api-production.up.railway.app/api/urgences`
- **Opérateurs** : `https://enco-api-production.up.railway.app/api/operateurs`
- **Prises de poste** : `https://enco-api-production.up.railway.app/api/prises-poste`
- **Messages IA** : `https://enco-api-production.up.railway.app/api/messages-ia`

## **Mise à jour du bot :**
Le bot utilise maintenant l'API déployée au lieu de localhost. L'URL est configurée dans `bot/main.py` :

```python
API_URL = os.getenv("API_URL", "https://enco-api-production.up.railway.app")
```

## **Avantages :**
✅ API accessible publiquement  
✅ Bot peut appeler l'API  
✅ Dashboard peut appeler l'API  
✅ Données synchronisées via Firestore  
✅ Scalable et robuste 